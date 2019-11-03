import traceback

from rest_framework.fields import CharField
#from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField

from ledger.accounts.models import EmailUser, Address
#from wildlifecompliance.components.call_email.serializers import LocationSerializer, LocationSerializerOptimized
from wildlifecompliance.components.legal_case.models import (
    LegalCase,
    LegalCaseUserAction,
    LegalCaseCommsLogEntry,
    LegalCasePriority,
    )
from wildlifecompliance.components.main.related_item import get_related_items
from wildlifecompliance.components.main.serializers import CommunicationLogEntrySerializer
from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    CompliancePermissionGroupMembersSerializer
)
from rest_framework import serializers
from django.core.exceptions import ValidationError
from wildlifecompliance.components.main.fields import CustomChoiceField

from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    CompliancePermissionGroupMembersSerializer,
    UserAddressSerializer,
)
#from wildlifecompliance.components.offence.serializers import OrganisationSerializer
#from django.contrib.auth.models import Permission, ContentType


class LegalCasePrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalCasePriority
        fields = ('__all__')
        read_only_fields = (
                'id',
                )

class LegalCaseSerializer(serializers.ModelSerializer):
    allocated_group = serializers.SerializerMethodField()
    #all_officers = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    related_items = serializers.SerializerMethodField()
    legal_case_priority = LegalCasePrioritySerializer()
    #inspection_report = serializers.SerializerMethodField()
    #data = InspectionFormDataRecordSerializer(many=True)
    #location = LocationSerializer(read_only=True)

    class Meta:
        model = LegalCase
        fields = (
                'id',
                'number',
                'status',
                'title',
                'details',
                'case_created_date',
                'case_created_time',
                'assigned_to_id',
                'allocated_group',
                'allocated_group_id',
                'user_in_group',
                'can_user_action',
                'user_is_assignee',
                'related_items',
                'call_email_id',
                'region_id',
                'district_id',
                'legal_case_priority',
                'legal_case_priority_id',
                )
        read_only_fields = (
                'id',
                )

    def get_related_items(self, obj):
        return get_related_items(obj)

    def get_user_in_group(self, obj):
        return_val = False
        user_id = self.context.get('request', {}).user.id
        if obj.allocated_group:
           for member in obj.allocated_group.members:
               if user_id == member.id:
                  return_val = True
        return return_val

    def get_can_user_action(self, obj):
        return_val = False
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return_val = True
        elif obj.allocated_group and not obj.assigned_to_id:
           for member in obj.allocated_group.members:
               if user_id == member.id:
                  return_val = True
        return return_val

    def get_user_is_assignee(self, obj):
        return_val = False
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return_val = True

        return return_val

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


class SaveLegalCaseSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    allocated_group_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    call_email_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    legal_case_priority_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = LegalCase
        fields = (
                'id',
                'title',
                'details',
                'case_created_date',
                'case_created_time',
                'assigned_to_id',
                'allocated_group_id',
                'call_email_id',
                'legal_case_priority_id',
                )
        read_only_fields = (
                'id',
                )

        
class LegalCaseUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = LegalCaseUserAction
        fields = '__all__'


class LegalCaseCommsLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = LegalCaseCommsLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class LegalCaseDatatableSerializer(serializers.ModelSerializer):
    user_action = serializers.SerializerMethodField()
    created_date = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    assigned_to = ComplianceUserDetailsOptimisedSerializer(read_only=True)
    #inspection_team_lead = EmailUserSerializer()
    
    class Meta:
        model = LegalCase
        fields = (
                'number',
                'title',
                'status',
                #'case_created_date',
                'created_date',
                'user_action',
                'assigned_to',
                'assigned_to_id',
                )

    def get_user_action(self, obj):
        user_id = self.context.get('request', {}).user.id
        view_url = '<a href=/internal/legal_case/' + str(obj.id) + '>View</a>'
        process_url = '<a href=/internal/legal_case/' + str(obj.id) + '>Process</a>'
        returned_url = ''

        if obj.status == 'closed':
            returned_url = view_url
        elif user_id == obj.assigned_to_id:
            returned_url = process_url
        elif (obj.allocated_group
                and not obj.assigned_to_id):
            for member in obj.allocated_group.members:
                if user_id == member.id:
                    returned_url = process_url

        if not returned_url:
            returned_url = view_url

        return returned_url

    def get_created_date(self, obj):
        if obj.case_created_date:
            if obj.case_created_time:
                return obj.case_created_date.strftime("%d/%m/%Y") + '  ' + obj.case_created_time.strftime('%H:%M')
            else:
                return obj.case_created_date.strftime("%d/%m/%Y")
        else:
            return None

class UpdateAssignedToIdSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    
    class Meta:
        model = LegalCase
        fields = (
            'assigned_to_id',
        )

