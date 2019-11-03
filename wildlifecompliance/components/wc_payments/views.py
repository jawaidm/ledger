# # from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
# # from django.core.urlresolvers import reverse
# # from django.contrib.auth.decorators import login_required
# from django.shortcuts import render, get_object_or_404, redirect
# from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.base import View, TemplateView
# from django.conf import settings
# from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
# from django.views.decorators.csrf import csrf_protect
# from django.core.exceptions import ValidationError
from django.db import transaction

# from datetime import datetime, timedelta, date
# from django.utils import timezone
# from dateutil.relativedelta import relativedelta
#
# from commercialoperator.components.proposals.models import Proposal
# from commercialoperator.components.compliances.models import Compliance
# from commercialoperator.components.main.models import Park
# from commercialoperator.components.organisations.models import Organisation
# from commercialoperator.components.bookings.context_processors import commercialoperator_url, template_context
# from commercialoperator.components.bookings.invoice_pdf import create_invoice_pdf_bytes
# from commercialoperator.components.bookings.confirmation_pdf import create_confirmation_pdf_bytes
# from commercialoperator.components.bookings.monthly_confirmation_pdf import create_monthly_confirmation_pdf_bytes
# from commercialoperator.components.bookings.email import (
#     send_invoice_tclass_email_notification,
#     send_confirmation_tclass_email_notification,
#     send_application_fee_invoice_tclass_email_notification,
#     send_application_fee_confirmation_tclass_email_notification,
# )
# from commercialoperator.components.bookings.utils import (
#     create_booking,
#     get_session_booking,
#     set_session_booking,
#     delete_session_booking,
#     create_lines,
#     checkout,
#     create_fee_lines,
#     get_session_application_invoice,
#     set_session_application_invoice,
#     delete_session_application_invoice,
#     calc_payment_due_date,
#     create_bpay_invoice,
# )

# from commercialoperator.components.proposals.serializers import ProposalSerializer

from ledger.checkout.utils import create_basket_session, create_checkout_session, place_order_submission, get_cookie_basket
from ledger.payments.utils import oracle_parser_on_invoice,update_payments
import json
from decimal import Decimal

# from commercialoperator.components.bookings.models import Booking, ParkBooking, BookingInvoice, ApplicationFee, ApplicationFeeInvoice
from ledger.payments.models import Invoice
from ledger.basket.models import Basket
from ledger.payments.mixins import InvoiceOwnerMixin
from oscar.apps.order.models import Order

import logging

from wildlifecompliance.components.wc_payments.context_processors import template_context
from wildlifecompliance.components.wc_payments.models import InfringementPenalty, InfringementPenaltyInvoice
from wildlifecompliance.components.wc_payments.utils import set_session_infringement_invoice, create_infringement_lines, \
    get_session_infringement_invoice, delete_session_infringement_invoice, checkout
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome

logger = logging.getLogger('payment_checkout')


class InfringementPenaltyView(TemplateView):
    template_name = 'wildlifecompliance/payments/success.html'

    def get_object(self):
        return get_object_or_404(SanctionOutcome, id=self.kwargs['sanction_outcome_id'])

    def post(self, request, *args, **kwargs):

        sanction_outcome = self.get_object()
        infringement_penalty = InfringementPenalty.objects.create(sanction_outcome=sanction_outcome, created_by=request.user, payment_type=InfringementPenalty.PAYMENT_TYPE_TEMPORARY)

        try:
            with transaction.atomic():
                set_session_infringement_invoice(request.session, infringement_penalty)
                lines = create_infringement_lines(sanction_outcome)
                checkout_response = checkout(
                    request,
                    sanction_outcome,
                    lines,
                    return_url_ns='penalty_success',
                    return_preload_url_ns='penalty_success',
                    invoice_text='Infringement Notice'
                )

                logger.info('{} built payment line item {} for Infringement and handing over to payment gateway'.format('User {} with id {}'.format(sanction_outcome.offender.person.get_full_name(), sanction_outcome.offender.person.id), sanction_outcome.id))
                return checkout_response

        except Exception, e:
            logger.error('Error Creating Infringement Penalty: {}'.format(e))
            if infringement_penalty:
                infringement_penalty.delete()
            raise


# from commercialoperator.components.proposals.utils import proposal_submit
class InfringementPenaltySuccessView(TemplateView):
    template_name = 'wildlifecompliance/payments/success.html'

    def get(self, request, *args, **kwargs):
        print (" Infringement Peanlty SUCCESS ")

        sanction_outcome = None
        offender = None
        invoice = None

        try:
            context = template_context(self.request)
            basket = None
            infringement_penalty = get_session_infringement_invoice(request.session)
            sanction_outcome = infringement_penalty.sanction_outcome

            recipient = sanction_outcome.offender.person.email
            submitter = sanction_outcome.assigned_to.email if sanction_outcome.assigned_to else None

            if self.request.user.is_authenticated():
                basket = Basket.objects.filter(status='Submitted', owner=request.user).order_by('-id')[:1]
            else:
                # basket = Basket.objects.filter(status='Submitted', owner=booking.proposal.submitter).order_by('-id')[:1]
                basket = Basket.objects.filter(status='Submitted', owner=None).order_by('-id')[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)
            if invoice.payment_status == 'paid':
                sanction_outcome.status = SanctionOutcome.STATUS_CLOSED
                sanction_outcome.payment_status = SanctionOutcome.PAYMENT_STATUS_PAID
                sanction_outcome.save()
            invoice_ref = invoice.reference
            fee_inv, created = InfringementPenaltyInvoice.objects.get_or_create(infringement_penalty=infringement_penalty, invoice_reference=invoice_ref)

            if infringement_penalty.payment_type == InfringementPenalty.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    order.user = submitter
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an infringement penalty with an incorrect invoice'.format('User {} with id {}'.format(sanction_outcome.offender.person.get_full_name(), sanction_outcome.offender.person.id) if sanction_outcome.offender else 'An anonymous user'))
                    #return redirect('external', args=(proposal.id,))
                    return redirect('external')

                if inv.system not in ['0999']: # TODO Change to correct VALUE
                    logger.error('{} tried paying an infringement penalty with an invoice from another system with reference number {}'.format('User {} with id {}'.format(sanction_outcome.offender.person.get_full_name(), sanction_outcome.offender.person.id) if sanction_outcome.offender.person else 'An anonymous user',inv.reference))
                    #return redirect('external-proposal-detail', args=(proposal.id,))
                    return redirect('external')

                if fee_inv:
                    infringement_penalty.payment_type = InfringementPenalty.PAYMENT_TYPE_INTERNET
                    infringement_penalty.expiry_time = None
                    update_payments(invoice_ref)

#                    proposal = proposal_submit(proposal, request)
#                    if proposal and (invoice.payment_status == 'paid' or invoice.payment_status == 'over_paid'):
#                        sanction_outcome.fee_invoice_reference = invoice_ref
#                        proposal.save()
#                    else:
#                        logger.error('Invoice payment status is {}'.format(invoice.payment_status))
#                        raise
#                    application_fee.save()
                    infringement_penalty.save()
                    request.session['wc_last_infringement_invoice'] = infringement_penalty.id
                    delete_session_infringement_invoice(request.session)

					# TODO 1. offender, 2. internal officer
                    #send_application_fee_invoice_tclass_email_notification(request, proposal, invoice, recipients=[recipient])
                    #send_application_fee_confirmation_tclass_email_notification(request, application_fee, invoice, recipients=[recipient])

                    context = {
                        'sanction_outcome': sanction_outcome,
                        'offender': recipient,
                        'fee_invoice': invoice
                    }
                    print(context)
                    return render(request, self.template_name, context)

        except Exception as e:
            if ('wc_last_infringement_invoice' in request.session) and InfringementPenalty.objects.filter(id=request.session['wc_last_infringement_invoice']).exists():
                infringement_penalty = InfringementPenalty.objects.get(id=request.session['wc_last_infringement_invoice'])
                sanction_outcome = infringement_penalty.sanction_outcome

                recipient = sanction_outcome.offender.person.email
                submitter = sanction_outcome.assigned_to.email if sanction_outcome.assigned_to else None

                if InfringementPenaltyInvoice.objects.filter(infringement_penalty=infringement_penalty).count() > 0:
                    ip_inv = InfringementPenaltyInvoice.objects.filter(infringement_penalty=infringement_penalty)
                    invoice = ip_inv[0]
            else:
                return redirect('external')

        context = {
            'sanction_outcome': sanction_outcome,
            'offender': recipient,
            'fee_invoice': invoice
        }
        return render(request, self.template_name, context)


