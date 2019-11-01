import json
import operator
import traceback
from datetime import datetime

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.db.models import Q
from rest_framework import viewsets, filters, serializers, status
from rest_framework.decorators import detail_route, list_route, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.pagination import DatatablesPageNumberPagination

from ledger.accounts.models import EmailUser
from wildlifecompliance.components.main.email import prepare_mail
from wildlifecompliance.components.offence.email import send_mail
from wildlifecompliance.components.organisations.models import Organisation
from wildlifecompliance.components.call_email.models import CallEmailUserAction, CallEmail
from wildlifecompliance.components.inspection.models import InspectionUserAction, Inspection
from wildlifecompliance.components.legal_case.models import LegalCase
from wildlifecompliance.components.main.api import save_location

from wildlifecompliance.components.offence.models import Offence, Offender, AllegedOffence, \
    OffenceUserAction, OffenceCommsLogEntry
from wildlifecompliance.components.section_regulation.models import SectionRegulation
from wildlifecompliance.components.offence.serializers import (
    OffenceSerializer,
    SaveOffenceSerializer,
    SaveOffenderSerializer,
    OrganisationSerializer,
    OffenceDatatableSerializer,
    UpdateAssignedToIdSerializer, UpdateOffenderAttributeSerializer, OffenceOptimisedSerializer,
    # UpdateAllegedOffenceAttributeSerializer, OffenceUserActionSerializer)
    UpdateAllegedOffenceAttributeSerializer, OffenceUserActionSerializer, OffenceCommsLogEntrySerializer,
    UpdateAllegedCommittedOffenceSerializer)
from wildlifecompliance.components.section_regulation.serializers import SectionRegulationSerializer
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, AllegedCommittedOffence
from wildlifecompliance.components.users.models import CompliancePermissionGroup
from wildlifecompliance.helpers import is_internal


class OffenceFilterBackend(DatatablesFilterBackend):

    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        # Storage for the filters
        # Required filters are accumulated here
        # Then issue a query once at last
        q_objects = Q()

        # Filter by the search_text
        search_text = request.GET.get('search[value]')
        if search_text:
            q_objects &= Q(lodgement_number__icontains=search_text) | \
                         Q(identifier__icontains=search_text) | \
                         Q(offender__person__first_name__icontains=search_text) | \
                         Q(offender__person__last_name__icontains=search_text) | \
                         Q(offender__person__email__icontains=search_text) | \
                         Q(offender__organisation__organisation__name__icontains=search_text) | \
                         Q(offender__organisation__organisation__abn__icontains=search_text) | \
                         Q(offender__organisation__organisation__trading_name__icontains=search_text)

        type = request.GET.get('type',).lower()
        if type and type != 'all':
            q_objects &= Q(type=type)

        status = request.GET.get('status',).lower()
        if status and status != 'all':
            q_objects &= Q(status=status)

        # payment_status = request.GET.get('payment_status',).lower()
        # if payment_status and payment_status != 'all':
        #     q_objects &= Q(payment_status=payment_status)

        date_from = request.GET.get('date_from',).lower()
        if date_from:
            date_from = datetime.strptime(date_from, '%d/%m/%Y')
            q_objects &= Q(date_of_issue__gte=date_from)

        date_to = request.GET.get('date_to',).lower()
        if date_to:
            date_to = datetime.strptime(date_to, '%d/%m/%Y')
            q_objects &= Q(date_of_issue__lte=date_to)

        # perform filters
        queryset = queryset.filter(q_objects)

        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        if len(ordering):
            for num, item in enumerate(ordering):
                # offender is the foreign key of the sanction outcome
                if item == 'offender':
                    # offender can be a person or an organisation
                    ordering[num] = 'offender__person'
                    ordering.insert(num + 1, 'offender__organisation')
                elif item == '-offender':
                    ordering[num] = '-offender__person'
                    ordering.insert(num + 1, '-offender__organisation')
                elif item == 'status__name':
                    ordering[num] = 'status'
                elif item == '-status__name':
                    ordering[num] = '-status'
                elif item == 'user_action':
                    pass

            queryset = queryset.order_by(*ordering).distinct()

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class OffencePaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (OffenceFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    queryset = Offence.objects.none()
    serializer_class = OffenceDatatableSerializer
    page_size = 10

    def get_queryset(self):
        # user = self.request.user
        if is_internal(self.request):
            return Offence.objects.all()
        return Offence.objects.none()

    @list_route(methods=['GET', ])
    def get_paginated_datatable(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = OffenceDatatableSerializer(result_page, many=True, context={'request': request})
        ret = self.paginator.get_paginated_response(serializer.data)
        return ret


class OffenceViewSet(viewsets.ModelViewSet):
    queryset = Offence.objects.all()
    serializer_class = OffenceSerializer

    def retrieve(self, request, *args, **kwargs):
        return super(OffenceViewSet, self).retrieve(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return Offence.objects.all()
        return Offence.objects.none()

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def workflow_action(self, request, instance=None, *args, **kwargs):
        try:
            with transaction.atomic():
                if not instance:
                    instance = self.get_object()

                comms_log_id = request.data.get('comms_log_id')
                if comms_log_id and comms_log_id is not 'null':
                    workflow_entry = instance.comms_logs.get(id=comms_log_id)
                else:
                    workflow_entry = self.add_comms_log(request, instance, workflow=True)

                # Set status
                workflow_type = request.data.get('workflow_type')
                email_data = None

                if workflow_type == Offence.WORKFLOW_CLOSE:
                    instance.close(request)
                    # Email to manager
                    email_data = prepare_mail(request, instance, workflow_entry, send_mail)
                else:
                    # Should not reach here
                    # instance.save()
                    pass

                # Log the above email as a communication log entry
                if email_data:
                    serializer = OffenceCommsLogEntrySerializer(instance=workflow_entry, data=email_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                return self.retrieve(request)
                # return_serializer = OffenceSerializer(instance=instance, context={'request': request})
                # headers = self.get_success_headers(return_serializer.data)
                # return Response(
                #     return_serializer.data,
                #     status=status.HTTP_201_CREATED,
                #     headers=headers
                # )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


    @list_route(methods=['GET', ])
    def can_user_create(self, request, *args, **kwargs):
        # Determine permissions which allow the holder to create new offence
        codename_who_can_create = 'officer'
        compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
        permissions = Permission.objects.filter(codename=codename_who_can_create, content_type_id=compliance_content_type.id)

        # Find groups which has permissions determined above
        allowed_groups = CompliancePermissionGroup.objects.filter(permissions__in=permissions)
        for allowed_group in allowed_groups.all():
            if request.user in allowed_group.members:
                return Response(True)
        return Response(False)


    @list_route(methods=['GET', ])
    def optimised(self, request, *args, **kwargs):
        queryset = self.get_queryset().exclude(location__isnull=True)

        filter_status = request.query_params.get('status', '')
        filter_status = '' if filter_status.lower() == 'all' else filter_status
        filter_date_from = request.query_params.get('date_from', '')
        filter_date_to = request.query_params.get('date_to', '')
        filter_sanction_outcome_type = request.query_params.get('sanction_outcome_type', '')
        filter_sanction_outcome_type = '' if filter_sanction_outcome_type.lower() == 'all' else filter_sanction_outcome_type

        q_list = []
        if filter_status:
            q_list.append(Q(status=filter_status))
        if filter_date_from:
            date_from = datetime.strptime(filter_date_from, '%d/%m/%Y')
            q_list.append(Q(occurrence_date_from__gte=date_from) | Q(occurrence_date_to__gte=date_from))
        if filter_date_to:
            date_to = datetime.strptime(filter_date_to, '%d/%m/%Y')
            q_list.append(Q(occurrence_date_to__lte=date_to) | Q(occurrence_date_from__lte=date_to))
        if filter_sanction_outcome_type:
            offence_ids = SanctionOutcome.objects.filter(type=filter_sanction_outcome_type).values_list('offence__id', flat=True).distinct()
            q_list.append(Q(id__in=offence_ids))

        queryset = queryset.filter(reduce(operator.and_, q_list)) if len(q_list) else queryset


        serializer = OffenceOptimisedSerializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['GET', ])
    def status_choices(self, request, *args, **kwargs):
        res_obj = []
        for choice in Offence.STATUS_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')

    @list_route(methods=['GET', ])
    def types(self, request, *args, **kwargs):
        res_obj = []
        section_regulations = SectionRegulation.objects.all()
        for item in section_regulations:
            res_obj.append({'id': item.id, 'display': item.act + ' ' + item.name});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')

    @list_route(methods=['GET', ])
    def statuses(self, request, *args, **kwargs):
        res_obj = []
        for choice in Offence.STATUS_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')

    @list_route(methods=['GET', ])
    def filter_by_call_email(self, request, *args, **kwargs):
        call_email_id = self.request.query_params.get('call_email_id', None)

        try:
            call_email = CallEmail.objects.get(id=call_email_id)
            queryset = self.get_queryset().filter(call_email__exact=call_email)
        except:
            queryset = self.get_queryset()

        serializer = OffenceSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @list_route(methods=['GET', ])
    def filter_by_inspection(self, request, *args, **kwargs):
        inspection_id = self.request.query_params.get('inspection_id', None)

        try:
            inspection = Inspection.objects.get(id=inspection_id)
            queryset = self.get_queryset().filter(inspection__exact=inspection)
        except:
            queryset = self.get_queryset()

        serializer = OffenceSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @list_route(methods=['GET', ])
    def filter_by_legal_case(self, request, *args, **kwargs):
        legal_case_id = self.request.query_params.get('legal_case_id', None)

        try:
            legal_case = LegalCase.objects.get(id=legal_case_id)
            queryset = self.get_queryset().filter(legal_case__exact=legal_case)
        except:
            queryset = self.get_queryset()

        serializer = OffenceSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def update_parent(self, request, instance, *args, **kwargs):
        # Log parent actions and update status, if required
        # If CallEmail
        if instance.call_email:
            instance.call_email.log_user_action(
                    CallEmailUserAction.ACTION_OFFENCE.format(
                    instance.lodgement_number), request)
            #instance.call_email.status = 'open_inspection'
            #instance.call_email.save()
        # If Inspection
        elif instance.inspection:
            instance.inspection.log_user_action(
                    InspectionUserAction.ACTION_OFFENCE.format(
                    instance.lodgement_number), request)
            #instance.inspection.status = 'open_inspection'
            #instance.inspection.save()

    # @detail_route(methods=['POST', ])
    # @renderer_classes((JSONRenderer,))
    def update(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                request_data = request.data

                # 1. Save Location
                if (
                        request_data.get('location', {}).get('geometry', {}).get('coordinates', {}) or
                        request_data.get('location', {}).get('properties', {}).get('postcode', {}) or
                        request_data.get('location', {}).get('properties', {}).get('details', {})
                ):
                    location_request_data = request.data.get('location')
                    returned_location = save_location(location_request_data)
                    if returned_location:
                        request_data.update({'location_id': returned_location.get('id')})

                # 2. Save Offence
                serializer = SaveOffenceSerializer(instance, data=request_data, partial=True)
                serializer.is_valid(raise_exception=True)
                saved_offence_instance = serializer.save()  # Here, relations between this offence and location, and this offence and call_email/inspection are created

                # 3. Handle alleged offences
                for item in request_data['alleged_offences']:
                    alleged_offence, created = AllegedOffence.objects.get_or_create(section_regulation_id=item['section_regulation']['id'], offence_id=request_data['id'])

                    if created:
                        # new alleged offence is added to the offence
                        # Which should be added to all the sanction outcomes under the offence if the status is 'draft'
                        sanction_outcomes = SanctionOutcome.objects.filter(status=SanctionOutcome.STATUS_DRAFT, offence=instance)
                        for so in sanction_outcomes:
                            aco = AllegedCommittedOffence.objects.create(included=False, alleged_offence=alleged_offence, sanction_outcome=so)
                    else:
                        serializer = None
                        alleged_offence_removed = False
                        alleged_offence_restored = False

                        # Update attributes of existing alleged offence
                        if not alleged_offence.removed and item['removed']:
                            # This alleged offence is going to be removed
                            alleged_offence_removed = True
                            serializer = UpdateAllegedOffenceAttributeSerializer(alleged_offence, data={
                                'removed': item['removed'],
                                'removed_by_id': request.user.id,
                                'reason_for_removal': item['reason_for_removal']
                            })
                        elif alleged_offence.removed and not item['removed']:
                            # This alleged offence is going to be restored
                            alleged_offence_restored = True
                            serializer = UpdateAllegedOffenceAttributeSerializer(alleged_offence, data={
                                'removed': item['removed'],
                                'removed_by_id': None,
                                'reason_for_removal': ''
                            })

                        if serializer:
                            serializer.is_valid(raise_exception=True)
                            serializer.save()

                            # Action log
                            if alleged_offence_removed:
                                instance.log_user_action(OffenceUserAction.ACTION_REMOVE_ALLEGED_OFFENCE.format(alleged_offence, item['reason_for_removal']), request)

                                # Update alleged committed offence's included status to False
                                alleged_committed_offences = AllegedCommittedOffence.objects.filter(Q(alleged_offence=alleged_offence))
                                for aco in alleged_committed_offences.all():
                                    serializer_aco = UpdateAllegedCommittedOffenceSerializer(aco, data={'included': False}, context={'sanction_outcome': aco.sanction_outcome})
                                    serializer_aco.is_valid(raise_exception=True)
                                    serializer_aco.save()

                            elif alleged_offence_restored:
                                instance.log_user_action(OffenceUserAction.ACTION_RESTORE_ALLEGED_OFFENCE.format(alleged_offence), request)

                # 4. Create relations between this offence and offender(s)
                for item in request_data['offenders']:
                    if item['person']:
                        # offender = Offender.objects.filter(person__id=item['person']['id'], offence__id=request_data['id'])
                        offender, created = Offender.objects.get_or_create(person_id=item['person']['id'], offence_id=request_data['id'])
                        # # if offender.count():
                        # #     created = False
                        # # else:
                        # #     created = True
                        # #     serializer_offender = SaveOffenderSerializer(data={'offence_id': instance.id, 'person_id': item['person']['id']})
                        # #     serializer_offender.is_valid(raise_exception=True)
                        #     serializer_offender.save()


                    elif item['organisation']:
                        offender, created = Offender.objects.get_or_create(organisation_id=item['organisation']['id'], offence_id=request_data['id'])

                    if not created:
                        serializer = None

                        # Update attributes of existing offender
                        if not offender.removed and item['removed']:
                            # This offender is going to be removed
                            serializer = UpdateOffenderAttributeSerializer(offender, data={
                                'removed': item['removed'],
                                'removed_by_id': request.user.id,
                                'reason_for_removal': item['reason_for_removal']
                            })

                        elif offender.removed and not item['removed']:
                            # This offender is going to be restored
                            serializer = UpdateOffenderAttributeSerializer(offender, data={
                                'removed': item['removed'],
                                'removed_by_id': None,
                                'reason_for_removal': ''
                            })

                        else:
                            # other case where nothing changed on this offender
                            pass

                        if serializer:
                            serializer.is_valid(raise_exception=True)

                            # Action log
                            if not offender.removed and item['removed']:
                                instance.log_user_action(OffenceUserAction.ACTION_REMOVE_OFFENDER.format(offender, item['reason_for_removal']), request)
                            elif offender.removed and not item['removed']:
                                instance.log_user_action(OffenceUserAction.ACTION_RESTORE_OFFENDER.format(offender), request)

                            serializer.save()

                # 4. Return Json
                return self.retrieve(request)

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    # @list_route(methods=['POST', ])
    # def offence_save(self, request, *args, **kwargs):
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                request_data = request.data

                # 1. Save Location
                if (
                    request_data.get('location', {}).get('geometry', {}).get('coordinates', {}) or
                    request_data.get('location', {}).get('properties', {}).get('postcode', {}) or
                    request_data.get('location', {}).get('properties', {}).get('details', {})
                ):
                    location_request_data = request.data.get('location')
                    returned_location = save_location(location_request_data)
                    if returned_location:
                        request_data.update({'location_id': returned_location.get('id')})

                # 2. Create Offence
                request_data['status'] = 'open'
                serializer = SaveOffenceSerializer(data=request_data)
                serializer.is_valid(raise_exception=True)
                saved_offence_instance = serializer.save()  # Here, relations between this offence and location, and this offence and call_email/inspection are created

                # 2.1. Determine allocated group and save it
                new_group = Offence.get_compliance_permission_group(saved_offence_instance.regionDistrictId)
                saved_offence_instance.allocated_group = new_group
                saved_offence_instance.assigned_to = None
                saved_offence_instance.responsible_officer = request.user
                saved_offence_instance.log_user_action(OffenceUserAction.ACTION_CREATE.format(saved_offence_instance.lodgement_number), request)
                saved_offence_instance.save()

                # 2.2. Update parents
                self.update_parent(request, saved_offence_instance)
                
                ## 2a. Log it to the call email, if applicable
                #if saved_offence_instance.call_email:
                #    saved_offence_instance.call_email.log_user_action(
                #            CallEmailUserAction.ACTION_OFFENCE.format(
                #                saved_offence_instance.call_email.number),
                #                request)

                ## 2b. Log it to the inspection, if applicable
                #if saved_offence_instance.inspection:
                #    saved_offence_instance.inspection.log_user_action(
                #            InspectionUserAction.ACTION_OFFENCE.format(
                #                saved_offence_instance.inspection.number),
                #                request)

                # 3. Create relations between this offence and the alleged 0ffence(s)
                for alleged_offence in request_data['alleged_offences']:
                    section_regulation = SectionRegulation.objects.get(id=alleged_offence['section_regulation']['id'])
                    # Insert a record into the through table
                    alleged_offence = AllegedOffence.objects.create(section_regulation=section_regulation, offence=saved_offence_instance,)

                # 4. Create relations between this offence and offender(s)
                for dict in request_data['offenders']:
                    if dict['data_type'] == 'individual':
                        offender = EmailUser.objects.get(id=dict['id'])
                        serializer_offender = SaveOffenderSerializer(data={'offence_id': saved_offence_instance.id, 'person_id': offender.id})
                        serializer_offender.is_valid(raise_exception=True)
                        serializer_offender.save()
                    elif dict['data_type'] == 'organisation':
                        offender = Organisation.objects.get(id=dict['id'])
                        serializer_offender = SaveOffenderSerializer(data={'offence_id': saved_offence_instance.id, 'organisation_id': offender.id})
                        serializer_offender.is_valid(raise_exception=True)
                        serializer_offender.save()

                # 4. Return Json
                headers = self.get_success_headers(serializer.data)
                return_serializer = OffenceSerializer(instance=saved_offence_instance, context={'request': request})
                # return_serializer = InspectionSerializer(saved_instance, context={'request': request})
                ret = Response(
                    return_serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
                return ret

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def update_assigned_to_id(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            validation_serializer = OffenceSerializer(instance, context={'request': request})
            user_in_group = validation_serializer.data.get('user_in_group')

            if user_in_group:
                # current user is in the group
                if request.data.get('current_user'):
                    # current user is going to assign him or herself to the object
                    serializer_partial = UpdateAssignedToIdSerializer(instance=instance, data={'assigned_to_id': request.user.id,})
                else:
                    # current user is going to assign someone else to the object
                    serializer_partial = UpdateAssignedToIdSerializer(instance=instance, data=request.data)

                if serializer_partial.is_valid(raise_exception=True):
                    # Update only assigned_to_id data
                    serializer_partial.save()

                # Construct return value
                return_serializer = OffenceSerializer(instance=instance, context={'request': request})
                headers = self.get_success_headers(return_serializer.data)
                return Response(return_serializer.data, status=status.HTTP_200_OK, headers=headers)
            else:
                return Response(validation_serializer.data, status=status.HTTP_200_OK)

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = OffenceUserActionSerializer(qs, many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, instance=None, workflow=False, *args, **kwargs):
        try:
            with transaction.atomic():
                # create offence outcome instance if not passed to this method
                if not instance:
                    instance = self.get_object()
                # add offence outcome attribute to request_data
                request_data = request.data.copy()
                request_data['offence'] = u'{}'.format(instance.id)
                if request_data.get('comms_log_id'):
                    comms = OffenceCommsLogEntry.objects.get(
                        id=request_data.get('comms_log_id')
                    )
                    serializer = OffenceCommsLogEntrySerializer(
                        instance=comms,
                        data=request.data)
                else:
                    serializer = OffenceCommsLogEntrySerializer(
                        data=request_data
                    )
                serializer.is_valid(raise_exception=True)
                # overwrite comms with updated instance
                comms = serializer.save()

                if workflow:
                    return comms
                else:
                    return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

class SearchSectionRegulation(viewsets.ModelViewSet):
    queryset = SectionRegulation.objects.all()
    serializer_class = SectionRegulationSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('act', 'name', 'offence_text',)


class SearchOrganisation(viewsets.ModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('organisation__abn', 'organisation__name',)

