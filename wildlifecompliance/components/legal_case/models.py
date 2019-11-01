from __future__ import unicode_literals
import logging
from django.db import models
from django.contrib.gis.db import models
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models import Max
from django.utils.encoding import python_2_unicode_compatible
from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.licence.models import LicenceType
from wildlifecompliance.components.organisations.models import Organisation
from wildlifecompliance.components.call_email.models import CallEmail, Location
from wildlifecompliance.components.main.models import (
        CommunicationsLogEntry,
        UserAction, 
        Document,
        )
from wildlifecompliance.components.main.related_item import can_close_record
from wildlifecompliance.components.users.models import RegionDistrict, CompliancePermissionGroup
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class LegalCasePriority(models.Model):
    case_priority = models.CharField(max_length=50)
    schema = JSONField(null=True)
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    replaced_by = models.ForeignKey(
        'self', on_delete=models.PROTECT, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    #approval_document = models.ForeignKey(
    #    'InspectionTypeApprovalDocument',
    #    related_name='inspection_type',
    #    null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CasePriority'
        verbose_name_plural = 'CM_CasePriorities'
        unique_together = ('case_priority', 'version')

    def __str__(self):
        return '{0}, v.{1}'.format(self.case_priority, self.version)


class LegalCase(RevisionedMixin):
    STATUS_OPEN = 'open'
    #STATUS_WITH_MANAGER = 'with_manager'
    #STATUS_REQUEST_AMENDMENT = 'request_amendment'
    STATUS_AWAIT_ENDORSEMENT = 'await_endorsement'
    #STATUS_SANCTION_OUTCOME = 'sanction_outcome'
    STATUS_DISCARDED = 'discarded'
    STATUS_CLOSED = 'closed'
    STATUS_PENDING_CLOSURE = 'pending_closure'
    STATUS_CHOICES = (
            (STATUS_OPEN, 'Open'),
            #(STATUS_WITH_MANAGER, 'With Manager'),
            #(STATUS_REQUEST_AMENDMENT, 'Request Amendment'),
            (STATUS_AWAIT_ENDORSEMENT, 'Awaiting Endorsement'),
            #(STATUS_SANCTION_OUTCOME, 'Awaiting Sanction Outcomes'),
            (STATUS_DISCARDED, 'Discarded'),
            (STATUS_CLOSED, 'Closed'),
            (STATUS_PENDING_CLOSURE, 'Pending Closure')
            )

    title = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(
            max_length=100,
            choices=STATUS_CHOICES,
            default='open'
            )
    details = models.TextField(blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    case_created_date = models.DateField(null=True)
    case_created_time = models.TimeField(blank=True, null=True)
    call_email = models.ForeignKey(
        CallEmail, 
        related_name='legal_case_call_email',
        null=True
        )
    assigned_to = models.ForeignKey(
        EmailUser, 
        related_name='legal_case_assigned_to',
        null=True
        )
    allocated_group = models.ForeignKey(
        CompliancePermissionGroup,
        related_name='legal_case_allocated_group', 
        null=True
        )
    region = models.ForeignKey(
        RegionDistrict, 
        related_name='legal_case_region', 
        null=True
    )
    district = models.ForeignKey(
        RegionDistrict, 
        related_name='legal_case_district', 
        null=True
    )
    legal_case_priority = models.ForeignKey(
            LegalCasePriority,
            null=True
            )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_LegalCase'
        verbose_name_plural = 'CM_LegalCases'

    def __str__(self):
        return 'ID: {}, Title: {}'.format(self.number, self.title)

    # Prefix "CS" char to LegalCase number.
    def save(self, *args, **kwargs):
        
        super(LegalCase, self).save(*args,**kwargs)
        if self.number is None:
            new_number_id = 'CS{0:06d}'.format(self.pk)
            self.number = new_number_id
            self.save()

    def log_user_action(self, action, request):
        return LegalCaseUserAction.log_action(self, action, request.user)
    
    @property
    def get_related_items_identifier(self):
        return self.number

    @property
    def get_related_items_descriptor(self):
        #return '{0}, {1}'.format(self.title, self.details)
        return self.title

    #def send_to_manager(self, request):
    #    self.status = self.STATUS_AWAIT_ENDORSEMENT
    #    self.log_user_action(
    #        InspectionUserAction.ACTION_SEND_TO_MANAGER.format(self.number), 
    #        request)
    #    self.save()

    def close(self, request):
        close_record, parents = can_close_record(self, request)
        if close_record:
            self.status = self.STATUS_CLOSED
            self.log_user_action(
                    LegalCaseUserAction.ACTION_CLOSE.format(self.number),
                    request)
        else:
            self.status = self.STATUS_PENDING_CLOSURE
            self.log_user_action(
                    LegalCaseUserAction.ACTION_PENDING_CLOSURE.format(self.number), 
                    request)
        self.save()
        # Call close() on any parent with pending_closure status
        if parents and self.status == 'closed':
            for parent in parents:
                if parent.status == 'pending_closure':
                    parent.close(request)


class LegalCaseCommsLogEntry(CommunicationsLogEntry):
    legal_case = models.ForeignKey(LegalCase, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'


class LegalCaseCommsLogDocument(Document):
    log_entry = models.ForeignKey(
        LegalCaseCommsLogEntry,
        related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class LegalCaseUserAction(UserAction):
    ACTION_CREATE_LEGAL_CASE = "Create Case {}"
    ACTION_SAVE_LEGAL_CASE = "Save Case {}"
    #ACTION_OFFENCE = "Create Offence {}"
    #ACTION_SANCTION_OUTCOME = "Create Sanction Outcome {}"
    #ACTION_SEND_TO_MANAGER = "Send Inspection {} to Manager"
    #ACTION_CLOSE = "Close Inspection {}"
    #ACTION_PENDING_CLOSURE = "Mark Inspection {} as pending closure"
    #ACTION_REQUEST_AMENDMENT = "Request amendment for {}"
    #ACTION_ENDORSEMENT = "Inspection {} has been endorsed by {}"
    ACTION_ADD_WEAK_LINK = "Create manual link between {}: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between {}: {} and {}: {}"
    #ACTION_MAKE_TEAM_LEAD = "Make {} team lead"
    #ACTION_ADD_TEAM_MEMBER = "Add {} to team"
    #ACTION_REMOVE_TEAM_MEMBER = "Remove {} from team"
    #ACTION_UPLOAD_INSPECTION_REPORT = "Upload Inspection Report '{}'"
    #ACTION_CHANGE_INDIVIDUAL_INSPECTED = "Change individual inspected from {} to {}"
    #ACTION_CHANGE_ORGANISATION_INSPECTED = "Change organisation inspected from {} to {}"

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, legal_case, action, user):
        return cls.objects.create(
            legal_case=legal_case,
            who=user,
            what=str(action)
        )

    legal_case = models.ForeignKey(LegalCase, related_name='action_logs')


class LegalCaseDocument(Document):
    legal_case = models.ForeignKey(LegalCase, related_name='documents')
    _file = models.FileField(max_length=255)
    input_name = models.CharField(max_length=255, blank=True, null=True)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)
    version_comment = models.CharField(max_length=255, blank=True, null=True)

    def delete(self):
        if self.can_delete:
            return super(LegalCaseDocument, self).delete()
        #logger.info(
         #   'Cannot delete existing document object after application has been submitted (including document submitted before\
          #  application pushback to status Draft): {}'.format(
           #     self.name)
        #)

    class Meta:
        app_label = 'wildlifecompliance'

