# from django.http import HttpResponseRedirect
# from django.core.urlresolvers import reverse
# from django.conf import settings
# from django.core.exceptions import ValidationError
# from django.db import transaction

from datetime import datetime, timedelta, date
# from django.utils import timezone
# from dateutil.relativedelta import relativedelta
# from commercialoperator.components.main.models import Park
# from commercialoperator.components.proposals.models import Proposal
# from commercialoperator.components.organisations.models import Organisation
# from commercialoperator.components.bookings.models import Booking, ParkBooking, BookingInvoice, ApplicationFee
# from commercialoperator.components.bookings.email import send_monthly_invoice_tclass_email_notification
# from ledger.checkout.utils import create_basket_session, create_checkout_session, calculate_excl_gst
from django.http.response import HttpResponseRedirect
from django.urls import reverse

from ledger.checkout.utils import create_basket_session, create_checkout_session
from ledger.payments.models import Invoice
# from ledger.payments.utils import oracle_parser
# import json
# import ast
from decimal import Decimal

import logging

from wildlifecompliance import settings
from wildlifecompliance.components.wc_payments.models import InfringementPenalty

logger = logging.getLogger('payment_checkout')

def get_session_infringement_invoice(session):
    """ Infringement Penalty session ID """
    if 'wc_infringement_invoice' in session:
        wc_infringement_id = session['wc_infringement_invoice']
    else:
        raise Exception('Infringement Penalty not in Session')

    try:
        return InfringementPenalty.objects.get(id=wc_infringement_id)
    except Invoice.DoesNotExist:
        raise Exception('Infringement Penalty not found for Sanction Outcome {}'.format(wc_infringement_id))

def set_session_infringement_invoice(session, infringement_penalty):
    """ Infringement Penalty session ID """
    session['wc_infringement_invoice'] = infringement_penalty.id
    session.modified = True

def delete_session_infringement_invoice(session):
    """ Infringement Penalty session ID """
    if 'wc_infringement_invoice' in session:
        del session['wc_infringement_invoice']
        session.modified = True

def create_infringement_lines(sanction_outcome, invoice_text=None, vouchers=[], internal=False):
    """ Create the ledger lines - line item for infringement penalty sent to payment system """

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    line_items = [
        {   'ledger_description': 'Infringement Notice: {}, Issued: {} {}'.format(
                sanction_outcome.lodgement_number,
                sanction_outcome.date_of_issue.strftime("%d-%m-%Y"),
                sanction_outcome.time_of_issue.strftime("%I:%M")),
            'oracle_code': 'ABC123 GST',
            'price_incl_tax':  sanction_outcome.penalty_amount,
            'price_excl_tax':  sanction_outcome.penalty_amount,
            'quantity': 1,
        },
    ]
    logger.info('{}'.format(line_items))
    return line_items

#def _create_fee_lines(proposal, invoice_text=None, vouchers=[], internal=False):
#    """ Create the ledger lines - line item for application fee sent to payment system """
#
#    now = datetime.now().strftime('%Y-%m-%d %H:%M')
#    application_price = proposal.application_type.application_fee
#    licence_price = proposal.licence_fee_amount
#    line_items = [
#        {   'ledger_description': 'Application Fee - {} - {}'.format(now, proposal.lodgement_number),
#            'oracle_code': proposal.application_type.oracle_code_application,
#            'price_incl_tax':  application_price,
#            'price_excl_tax':  application_price if proposal.application_type.is_gst_exempt else calculate_excl_gst(application_price),
#            'quantity': 1,
#        },
#    ]
#    logger.info('{}'.format(line_items))
#    return line_items


def checkout(request, proposal, lines, return_url_ns='public_booking_success', return_preload_url_ns='public_booking_success', invoice_text=None, vouchers=[], internal=False):
    #import ipdb; ipdb.set_trace()
    basket_params = {
        'products': lines,
        'vouchers': vouchers,
        'system': settings.WC_PAYMENT_SYSTEM_ID,
        'custom_basket': True,
    }

    basket, basket_hash = create_basket_session(request, basket_params)
    #fallback_url = request.build_absolute_uri('/')
    checkout_params = {
        'system': settings.WC_PAYMENT_SYSTEM_ID,
        'fallback_url': request.build_absolute_uri('/'),                                      # 'http://mooring-ria-jm.dbca.wa.gov.au/'
        'return_url': request.build_absolute_uri(reverse(return_url_ns)),          # 'http://mooring-ria-jm.dbca.wa.gov.au/success/'
        'return_preload_url': request.build_absolute_uri(reverse(return_url_ns)),  # 'http://mooring-ria-jm.dbca.wa.gov.au/success/'
        'force_redirect': True,
        'proxy': True if internal else False,
        'invoice_text': invoice_text,                                                         # 'Reservation for Jawaid Mushtaq from 2019-05-17 to 2019-05-19 at RIA 005'
    }
    #    if not internal:
    #        checkout_params['check_url'] = request.build_absolute_uri('/api/booking/{}/booking_checkout_status.json'.format(booking.id))
    if internal or request.user.is_anonymous():
        #checkout_params['basket_owner'] = booking.customer.id
        checkout_params['basket_owner'] = proposal.submitter_id


    create_checkout_session(request, checkout_params)

    #    if internal:
    #        response = place_order_submission(request)
    #    else:
    response = HttpResponseRedirect(reverse('checkout:index'))
    # inject the current basket into the redirect response cookies
    # or else, anonymous users will be directionless
    response.set_cookie(
        settings.OSCAR_BASKET_COOKIE_OPEN, basket_hash,
        max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME,
        secure=settings.OSCAR_BASKET_COOKIE_SECURE, httponly=True
    )

    return response
