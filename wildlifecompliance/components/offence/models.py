from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save

from ledger.accounts.models import RevisionedMixin, EmailUser
from wildlifecompliance.components.call_email.models import Location, CallEmail
from wildlifecompliance.components.legal_case.models import LegalCase
from wildlifecompliance.components.inspection.models import Inspection
from wildlifecompliance.components.main.models import Document, CommunicationsLogEntry
from wildlifecompliance.components.main.related_item import can_close_record
from wildlifecompliance.components.section_regulation.models import SectionRegulation
from wildlifecompliance.components.users.models import RegionDistrict, CompliancePermissionGroup
from wildlifecompliance.components.organisations.models import Organisation


class Offence(RevisionedMixin):
    WORKFLOW_CREATE = 'create'
    WORKFLOW_CLOSE = 'close'

    STATUS_DRAFT = 'draft'
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_PENDING_CLOSURE = 'pending_closure'
    STATUS_DISCARDED = 'discarded'

    EDITABLE_STATUSES = (STATUS_DRAFT, STATUS_OPEN,)
    FINAL_STATUSES = (STATUS_CLOSED, STATUS_DISCARDED,)

    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_OPEN, 'Open'),
        (STATUS_PENDING_CLOSURE, 'Pending Closure'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_DISCARDED, 'Discarded'),
    )

    identifier = models.CharField(
        max_length=50,
        blank=True,
    )
    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default='open',
    )
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        related_name="offence_location",
    )
    call_email = models.ForeignKey(
        CallEmail,
        null=True,
        blank=True,
        related_name='offence_call_eamil',
    )
    legal_case = models.ForeignKey(
        LegalCase,
        null=True,
        blank=True,
        related_name='offence_legal_case',
    )
    inspection = models.ForeignKey(
        Inspection,
        null=True,
        blank=True,
        related_name='offence_inspection',
    )
    lodgement_number = models.CharField(max_length=50, blank=True,)
    occurrence_from_to = models.BooleanField(default=False)
    occurrence_date_from = models.DateField(null=True, blank=True)
    occurrence_time_from = models.TimeField(null=True, blank=True)
    occurrence_date_to = models.DateField(null=True, blank=True)
    occurrence_time_to = models.TimeField(null=True, blank=True)
    alleged_offences = models.ManyToManyField(
        SectionRegulation,
        blank=True,
        through='AllegedOffence',
    )
    details = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        EmailUser,
        related_name='offence_assigned_to',
        null=True
    )
    allocated_group = models.ForeignKey(
        CompliancePermissionGroup,
        related_name='offence_allocated_group',
        null=True
    )
    region = models.ForeignKey(RegionDistrict, related_name='offence_region', null=True,)
    district = models.ForeignKey(RegionDistrict, related_name='offence_district', null=True,)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Offence'
        verbose_name_plural = 'CM_Offences'

    def __str__(self):
        return 'ID: {}, Status: {}, Identifier: {}'.format(self.id, self.status, self.identifier)

    def save(self, *args, **kwargs):
        super(Offence, self).save(*args, **kwargs)
        if not self.lodgement_number:
            self.lodgement_number = 'OF{0:06d}'.format(self.pk)
            self.save()

    def log_user_action(self, action, request=None):
        if request:
            return OffenceUserAction.log_action(self, action, request.user)
        else:
            return OffenceUserAction.log_action(self, action)

    @property
    def get_related_items_identifier(self):
        #return '{}'.format(self.identifier)
        return self.lodgement_number

    @staticmethod
    def get_compliance_permission_group(regionDistrictId):
        region_district = RegionDistrict.objects.filter(id=regionDistrictId)

        # 2. Determine which permission(s) is going to be applied
        compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
        codename = 'officer'
        per_district = True

        permissions = Permission.objects.filter(codename=codename, content_type_id=compliance_content_type.id)

        # 3. Find groups which has the permission(s) determined above in the regionDistrict.
        if per_district:
            groups = CompliancePermissionGroup.objects.filter(region_district__in=region_district, permissions__in=permissions)
        else:
            groups = CompliancePermissionGroup.objects.filter(permissions__in=permissions)

        return groups.first()

    @property
    def regionDistrictId(self):
        return self.district.id if self.district else self.region.id

    @property
    def get_related_items_descriptor(self):
        #return '{}, {}'.format(self.identifier, self.details)
        return self.identifier

    def close(self, request=None):
        close_record, parents = can_close_record(self)
        if close_record:
            self.status =  self.STATUS_CLOSED
            self.log_user_action(OffenceUserAction.ACTION_CLOSE.format(self.lodgement_number), request)
        else:
            self.status =  self.STATUS_PENDING_CLOSURE
            self.log_user_action(OffenceUserAction.ACTION_PENDING_CLOSURE.format(self.lodgement_number), request)
        self.save()


def perform_can_close_record(sender, instance, **kwargs):
    # Trigger the close() function of each parent entity of this offence
    if instance.status in (Offence.FINAL_STATUSES):
        close_record, parents = can_close_record(instance)
        for parent in parents:
            if parent.status == 'pending_closure':
                parent.close()

post_save.connect(perform_can_close_record, sender=Offence)


class AllegedOffence(RevisionedMixin):
    offence = models.ForeignKey(Offence, null=False,)
    section_regulation = models.ForeignKey(SectionRegulation, null=False, )
    reason_for_removal = models.TextField(blank=True)
    removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(
        EmailUser,
        null=True,
        related_name='alleged_offence_removed_by'
    )

    def __str__(self):
        return self.section_regulation.__str__()

    def retrieve_penalty_amount_by_date(self, date_of_issue):
        return self.section_regulation.retrieve_penalty_amount_by_date(date_of_issue)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_AllegedOffence'
        verbose_name_plural = 'CM_AllegedOffences'


class ActiveOffenderManager(models.Manager):
    def get_queryset(self):
        return super(ActiveOffenderManager, self).get_queryset().filter(removed=False)


class Offender(models.Model):
    reason_for_removal = models.TextField(blank=True)
    removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(
        EmailUser,
        null=True,
        related_name='offender_removed_by'
    )
    person = models.ForeignKey(
        EmailUser,
        null=True,
        related_name='offender_person',
    )
    organisation = models.ForeignKey(
        Organisation,
        null=True,
        related_name='offender_organisation',
    )
    offence = models.ForeignKey(
        Offence,
        null=True,
        on_delete=models.SET_NULL,
    )
    active_offenders = ActiveOffenderManager()
    objects = models.Manager()

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Offender'
        verbose_name_plural = 'CM_Offenders'

    def __str__(self):
        if self.person:
            return 'First name: {}, Last name: {}'.format(self.person.first_name, self.person.last_name)
        else:
            return '---'


class OffenceUserAction(models.Model):
    ACTION_CLOSE = "Close offence: {}"
    ACTION_PENDING_CLOSURE = "Mark offence {} as pending closure"
    ACTION_CREATE = "Create offence: {}"
    ACTION_REMOVE_ALLEGED_OFFENCE = "Remove alleged offence: {}, Reason: {}"
    ACTION_REMOVE_OFFENDER = "Remove offender: {}, Reason: {}"
    ACTION_RESTORE_ALLEGED_OFFENCE = "Restore alleged offence: {}"
    ACTION_RESTORE_OFFENDER = "Restore offender: {}"
    ACTION_ADD_WEAK_LINK = "Create manual link between {}: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between {}: {} and {}: {}"

    who = models.ForeignKey(EmailUser, null=True, blank=True)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)
    offence = models.ForeignKey(Offence, related_name='action_logs')

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, obj, action, user=None):
        return cls.objects.create(
            offence=obj,
            who=user,
            what=str(action)
        )


class OffenceCommsLogDocument(Document):
    log_entry = models.ForeignKey('OffenceCommsLogEntry', related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class OffenceCommsLogEntry(CommunicationsLogEntry):
    offence = models.ForeignKey(Offence, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'

