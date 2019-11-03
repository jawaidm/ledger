from django.db import models
from django.db.models import Q

from ledger.accounts.models import RevisionedMixin


class SectionRegulation(RevisionedMixin):
    act = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=50, blank=True, verbose_name='Regulation')
    offence_text = models.CharField(max_length=200, blank=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Section/Regulation'
        verbose_name_plural = 'CM_Sections/Regulations'
        ordering = ('act', 'name')

    def retrieve_penalty_amount_by_date(self, date_of_issue):
        return PenaltyAmount.objects.filter(
            Q(section_regulation=self) &
            Q(date_of_enforcement__lte=date_of_issue)).order_by('date_of_enforcement', ).last().amount

    def __str__(self):
        return '{}:{}:{}'.format(self.act, self.name, self.offence_text)


class PenaltyAmount(RevisionedMixin):
    amount =  models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    amount_after_due =  models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    date_of_enforcement = models.DateField(blank=True, null=True)
    section_regulation = models.ForeignKey(SectionRegulation, related_name='penalty_amounts')

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_PenaltyAmount'
        verbose_name_plural = 'CM_PenaltyAmounts'
        ordering = ('date_of_enforcement', )  # oldest record first, latest record last

    def __str__(self):
        return '${} ({}:{})'.format(self.amount, self.date_of_enforcement, self.section_regulation)