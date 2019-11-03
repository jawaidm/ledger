from django.db.models import Q
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from wildlifecompliance.components.main.fields import CustomChoiceField
from wildlifecompliance.components.main.related_item import get_related_items
from wildlifecompliance.components.main.serializers import CommunicationLogEntrySerializer
from wildlifecompliance.components.offence.models import AllegedOffence
from wildlifecompliance.components.offence.serializers import OffenderSerializer, \
    OffenceSerializer
from wildlifecompliance.components.section_regulation.serializers import SectionRegulationSerializer
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, RemediationAction, \
    SanctionOutcomeCommsLogEntry, SanctionOutcomeUserAction, AllegedCommittedOffence
from wildlifecompliance.components.users.serializers import CompliancePermissionGroupMembersSerializer


class AllegedOffenceSerializer(serializers.ModelSerializer):
    offence = OffenceSerializer(read_only=True)
    section_regulation = SectionRegulationSerializer(read_only=True)

    class Meta:
        model = AllegedOffence
        fields = (
            'id',
            'offence',
            'section_regulation',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=AllegedOffence.objects.filter(removed=False),
                fields=['offence', 'section_regulation'],
                message='Offence cannot associated with the sambe section regulation more than once'
            )
        ]

    def validate(self, data):
        # TODO: Add object level validation here if needed
        return data


class AllegedCommittedOffenceCreateSerializer(serializers.ModelSerializer):
    alleged_offence_id = serializers.IntegerField(write_only=True,)
    sanction_outcome_id = serializers.IntegerField(write_only=True,)

    class Meta:
        model = AllegedCommittedOffence
        fields = (
            'alleged_offence_id',
            'sanction_outcome_id',
        )

    def validate(self, data):
        existing = AllegedCommittedOffence.objects.filter(alleged_offence__id=data['alleged_offence_id'],
                                                          sanction_outcome__id=data['sanction_outcome_id'],
                                                          removed=False)
        if existing:
            ao = existing.first().alleged_offence
            raise serializers.ValidationError('Alleged offence: %s is duplicated' % ao)
        return data


class AllegedCommittedOffenceSerializer(serializers.ModelSerializer):
    alleged_offence = AllegedOffenceSerializer(read_only=True,)
    # removed_by_id = serializers.IntegerField(write_only=True, required=False)
    in_editable_status = serializers.SerializerMethodField()
    can_user_restore = serializers.SerializerMethodField()

    class Meta:
        model = AllegedCommittedOffence
        fields = (
            'id',
            'included',
            # 'removed',
            # 'reason_for_removal',
            # 'removed_by',
            # 'removed_by_id',
            'alleged_offence',
            'in_editable_status',
            'can_user_restore',
        )

    def get_in_editable_status(self, obj):
        # Check if the sanction outcome is in the status of STATUS_AWAITING_AMENDMENT or SanctionOutcome,
        # Which means the sanction outcome is under some officer at the moment, therefore it should be editable
        return obj.sanction_outcome.status in (SanctionOutcome.STATUS_DRAFT,)

    def get_can_user_restore(self, obj):
        can_user_restore = False

        if self.get_in_editable_status(obj) and obj.removed:
            existing = AllegedCommittedOffence.objects.filter(sanction_outcome=obj.sanction_outcome, alleged_offence=obj.alleged_offence, included=True, removed=False)
            if not existing:
                # If there is not same alleged committed offence in the database, there should be restore button
                can_user_restore = True

        return can_user_restore


class SanctionOutcomeSerializer(serializers.ModelSerializer):
    status = CustomChoiceField(read_only=True)
    type = CustomChoiceField(read_only=True)
    payment_status = CustomChoiceField(read_only=True)
    alleged_committed_offences = serializers.SerializerMethodField()
    offender = OffenderSerializer(read_only=True,)
    offence = OffenceSerializer(read_only=True,)
    allocated_group = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    related_items = serializers.SerializerMethodField()
    paper_notices = serializers.SerializerMethodField()

    class Meta:
        model = SanctionOutcome
        fields = (
            'id',
            'type',
            'status',
            'payment_status',
            'lodgement_number',
            'region_id',
            'district_id',
            'identifier',
            'offence',
            'offender',
            'alleged_committed_offences',
            'issued_on_paper',
            'paper_id',
            'paper_notices',
            'description',
            'date_of_issue',
            'time_of_issue',
            'assigned_to_id',
            'allocated_group',
            'allocated_group_id',
            'user_in_group',
            'can_user_action',
            'user_is_assignee',
            'related_items',
        )
        read_only_fields = ()

    def get_paper_notices(self, obj):
        return [[r.name, r._file.url] for r in obj.documents.all()]

    def get_allocated_group(self, obj):
        allocated_group = [{
            'email': '',
            'first_name': '',
            'full_name': '',
            'id': None,
            'last_name': '',
            'title': '',
        }]
        returned_allocated_group = CompliancePermissionGroupMembersSerializer(instance=obj.allocated_group)
        for member in returned_allocated_group.data['members']:
            allocated_group.append(member)

        return allocated_group

    def get_user_in_group(self, obj):
        user_id = self.context.get('request', {}).user.id

        if obj.allocated_group:
            for member in obj.allocated_group.members:
                if user_id == member.id:
                    return True
        return False

    def get_can_user_action(self, obj):
        # User can have action buttons
        # when user is assigned to the target object or
        # when user is a member of the allocated group and no one is assigned to the target object
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return True
        elif obj.allocated_group and not obj.assigned_to_id:
            if user_id in [member.id for member in obj.allocated_group.members]:
                return True

        return False

    def get_user_is_assignee(self, obj):
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return True

        return False

    def get_related_items(self, obj):
        return get_related_items(obj)

    def get_alleged_committed_offences(self, so_obj):
        ao_ids_already_included = AllegedCommittedOffence.objects.filter(sanction_outcome=so_obj).values_list('alleged_offence__id', flat=True)

        # Check if there is newly aded alleged offence to be added to this sanction outcome
        if so_obj.status == SanctionOutcome.STATUS_DRAFT:
            # Only when sanction outcome is in draft status, newly added alleged offence should be added
            # Query newly added alleged offence which is not included yet
            # However whenever new alleged offence is added to the offence, it should be added to the sanction outcomes under the offence at the moment.
            qs_allegedOffences = AllegedOffence.objects.filter(Q(offence=so_obj.offence) & Q(removed=False)).exclude(Q(id__in=ao_ids_already_included))
            for ao in qs_allegedOffences:
                aco = AllegedCommittedOffence.objects.create(included=False, alleged_offence=ao, sanction_outcome=so_obj)

        qs_allegedCommittedOffences = AllegedCommittedOffence.objects.filter(sanction_outcome=so_obj)
        return [AllegedCommittedOffenceSerializer(item, context={'request': self.context.get('request', {})}).data for item in qs_allegedCommittedOffences]


class UpdateAssignedToIdSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = SanctionOutcome
        fields = (
            'assigned_to_id',
        )


class SanctionOutcomeDatatableSerializer(serializers.ModelSerializer):
    status = CustomChoiceField(read_only=True)
    payment_status = CustomChoiceField(read_only=True)
    type = CustomChoiceField(read_only=True)
    user_action = serializers.SerializerMethodField()
    offender = OffenderSerializer(read_only=True,)
    paper_notices = serializers.SerializerMethodField()

    class Meta:
        model = SanctionOutcome
        fields = (
            'id',
            'type',
            'status',
            'payment_status',
            'lodgement_number',
            'region',
            'district',
            'identifier',
            'offence',
            'offender',
            'alleged_offences',
            'issued_on_paper',
            'paper_id',
            'description',
            'date_of_issue',
            'time_of_issue',
            'user_action',
            'paper_notices',
        )
        read_only_fields = ()

    def get_paper_notices(self, obj):
        return [[r.name, r._file.url] for r in obj.documents.all()]

    def get_user_action(self, obj):
        user_id = self.context.get('request', {}).user.id
        view_url = '<a href=/internal/sanction_outcome/' + str(obj.id) + '>View</a>'
        process_url = '<a href=/internal/sanction_outcome/' + str(obj.id) + '>Process</a>'
        returned_url = ''

        if obj.status == SanctionOutcome.STATUS_CLOSED:
            # if object is closed, now one can process but view
            returned_url = view_url
        elif user_id == obj.assigned_to_id:
            # if user is assigned to the object, the user can process it
            returned_url = process_url
        elif (obj.allocated_group and not obj.assigned_to_id):
            if user_id in [member.id for member in obj.allocated_group.members]:
                # if user belongs to the same group of the object
                # and no one is assigned to the object,
                # the user can process it
                returned_url = process_url

        if not returned_url:
            # In other case user can view
            returned_url = view_url

        return returned_url


class SaveSanctionOutcomeSerializer(serializers.ModelSerializer):
    offence_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    offender_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    region_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    district_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    allocated_group_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = SanctionOutcome
        fields = (
            'id',
            'type',
            'identifier',
            'offence_id',
            'offender_id',
            'region_id',
            'district_id',
            'allocated_group_id',
            'issued_on_paper',
            'paper_id',
            'description',
            'date_of_issue',
            'time_of_issue',
        )

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not data['region_id']:
            non_field_errors.append('Sanction Outcome must have a region')

        if data['issued_on_paper']:
            if not data['paper_id']:
                non_field_errors.append('Paper ID is required')
            if not data['date_of_issue']:
                non_field_errors.append('Date of Issue is required')
            if not data['time_of_issue']:
                non_field_errors.append('Time of Issue is required')
            if not self.context['num_of_documents_attached']:
                non_field_errors.append('Paper notice is required')

        if field_errors:
            raise serializers.ValidationError(field_errors)

        if non_field_errors:
            raise serializers.ValidationError(non_field_errors)

        return data

    def create(self, validated_data):
        """
        this method is called when creating new record after the validate() method.
        here is the best place to edit data here if needed
        """

        return super(SaveSanctionOutcomeSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        """
        this method is called when updating existing record after the validate() method.
        here is the best place to edit data here if needed
        """
        return super(SaveSanctionOutcomeSerializer, self).update(instance, validated_data)


class SaveRemediationActionSerializer(serializers.ModelSerializer):
    sanction_outcome_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = RemediationAction
        fields = (
            'id',
            'action',
            'due_date',
            'sanction_outcome_id',
        )


class SanctionOutcomeUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = SanctionOutcomeUserAction
        fields = '__all__'


class SanctionOutcomeCommsLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = SanctionOutcomeCommsLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]

