from django.conf import settings
from ledger.accounts.models import EmailUser,Address
from disturbance.components.approvals.models import (
    Approval
)
from disturbance.components.organisations.models import (
                                Organisation
                            )
from rest_framework import serializers

class ApprovalSerializer(serializers.ModelSerializer):
    applicant = serializers.CharField(source='applicant.name')
    licence_document = serializers.CharField(source='licence_document._file.url')
    status = serializers.CharField(source='get_status_display')
    class Meta:
        model = Approval
        fields = (
            'id',
            'licence_document',
            'replaced_by',
            'current_proposal',
            'activity',
            'region',
            'tenure',
            'title',
            'renewal_sent',
            'issue_date',
            'original_issue_date',
            'start_date',
            'expiry_date',
            'surrender_details',
            'suspension_details',
            'applicant',
            'extracted_fields',
            'status',
            'reference'
        )
