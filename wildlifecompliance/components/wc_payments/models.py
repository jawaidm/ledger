from __future__ import unicode_literals

from datetime import datetime, timedelta
from django.db import models, transaction
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
# from django.utils import timezone
from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.payments.models import Invoice
#from commercialoperator.components.proposals.models import Proposal
#from commercialoperator.components.main.models import Park
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome
from decimal import Decimal as D
from ledger.checkout.utils import calculate_excl_gst

import logging
logger = logging.getLogger(__name__)

def expiry_default():
    return timezone.now() + timedelta(minutes=30)


class Payment(RevisionedMixin):

    send_invoice = models.BooleanField(default=False)
    confirmation_sent = models.BooleanField(default=False)
    created = models.DateTimeField(default=timezone.now)  # default should be callable otherwise it is called only once when the server starts
    expiry_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        abstract = True

    @property
    def paid(self):
        payment_status = self.__check_payment_status()
        if payment_status == 'paid' or payment_status == 'over_paid':
            return True
        return False

    @property
    def unpaid(self):
        payment_status = self.__check_payment_status()
        if payment_status == 'unpaid':
            return True
        return False

    @property
    def amount_paid(self):
        return self.__check_payment_amount()

    def __check_payment_amount(self):
        amount = D('0.0')
        if self.active_invoice:
            return self.active_invoice.payment_amount
        return amount


    def __check_invoice_payment_status(self):
        invoices = []
        payment_amount = D('0.0')
        invoice_amount = D('0.0')
        references = self.invoices.all().values('invoice_reference')
        for r in references:
            try:
                invoices.append(Invoice.objects.get(reference=r.get("invoice_reference")))
            except Invoice.DoesNotExist:
                pass
        for i in invoices:
            if not i.voided:
                payment_amount += i.payment_amount
                invoice_amount += i.amount

        if invoice_amount == payment_amount:
            return 'paid'
        if payment_amount > invoice_amount:
            return 'over_paid'
        return "unpaid"

    def __check_payment_status(self):
        invoices = []
        amount = D('0.0')
        references = self.invoices.all().values('invoice_reference')
        for r in references:
            try:
                invoices.append(Invoice.objects.get(reference=r.get("invoice_reference")))
            except Invoice.DoesNotExist:
                pass
        for i in invoices:
            if not i.voided:
                amount += i.payment_amount

        if amount == 0:
            return 'unpaid'
        elif self.cost_total < amount:
            return 'over_paid'
        elif self.cost_total > amount:
            return 'partially_paid'
        return "paid"


class InfringementPenalty(Payment):
    PAYMENT_TYPE_INTERNET = 0
    PAYMENT_TYPE_RECEPTION = 1
    PAYMENT_TYPE_BLACK = 2
    PAYMENT_TYPE_TEMPORARY = 3
    PAYMENT_TYPE_CHOICES = (
        (PAYMENT_TYPE_INTERNET, 'Internet booking'),
        (PAYMENT_TYPE_RECEPTION, 'Reception booking'),
        (PAYMENT_TYPE_BLACK, 'Black booking'),
        (PAYMENT_TYPE_TEMPORARY, 'Temporary reservation'),
    )

    sanction_outcome = models.ForeignKey(SanctionOutcome, on_delete=models.PROTECT, blank=True, null=True, related_name='infringement_penalties')
    payment_type = models.SmallIntegerField(choices=PAYMENT_TYPE_CHOICES, default=0)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    created_by = models.ForeignKey(EmailUser,on_delete=models.PROTECT, blank=True, null=True,related_name='created_by_infringement_penalty')

    def __str__(self):
        return 'Sanction Outcome {} : Invoice {}'.format(self.sanction_outcome, self.infringement_penalty_invoices.last())

    class Meta:
        app_label = 'wildlifecompliance'


class InfringementPenaltyInvoice(RevisionedMixin):
    #application_fee = models.ForeignKey(ApplicationFee, related_name='application_fee_invoices')
    infringement_penalty = models.ForeignKey(InfringementPenalty, related_name='infringement_penalty_invoices')
    invoice_reference = models.CharField(max_length=50, null=True, blank=True, default='')

    def __str__(self):
        return 'Sanction Outcomes {} : Invoice #{}'.format(self.id, self.invoice_reference)

    class Meta:
        app_label = 'wildlifecompliance'

    @property
    def active(self):
        try:
            invoice = Invoice.objects.get(reference=self.invoice_reference)
            return False if invoice.voided else True
        except Invoice.DoesNotExist:
            pass
        return False


#import reversion
#reversion.register(ApplicationFee, follow=['application_fee_invoices'])
#reversion.register(ApplicationFeeInvoice)


