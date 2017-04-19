import requests
import datetime
from django.core.mail import EmailMessage 
import traceback
import json
import csv 
from six.moves import StringIO
from wsgiref.util import FileWrapper
from decimal import Decimal as D
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve
from django.contrib.auth.models import AnonymousUser
from six.moves.urllib.parse import urlparse
#
from ledger.basket.models import Basket
from ledger.catalogue.models import Product
from ledger.payments.models import OracleParser, OracleParserInvoice, Invoice, OracleInterface, OracleInterface 
from oscar.core.loading import get_class
from oscar.apps.voucher.models import Voucher
import logging
logger = logging.getLogger(__name__)


OrderPlacementMixin = get_class('checkout.mixins','OrderPlacementMixin')
Selector = get_class('partner.strategy', 'Selector')
selector = Selector()

def isLedgerURL(url):
    ''' Check if the url is a ledger url
    :return: Boolean
    '''
    match = None
    try:
        match = resolve(urlparse(url)[2])
    except:
        pass
    if match:
        return True
    return False

def checkURL(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except:
        raise

def systemid_check(system):
    system = system[1:]
    if len(system) == 3:
        system = '0{}'.format(system)
    elif len(system) > 4:
        system = system[:4]
    return system

def validSystem(system_id):
    ''' Check if the system is in the itsystems register.
    :return: Boolean
    '''
    if settings.CMS_URL:
        # TODO: prefetch whole systems register list, store in django cache, use that instead of doing a GET request every time
        res = requests.get('{}?system_id={}'.format(settings.CMS_URL,system_id), auth=(settings.LEDGER_USER,settings.LEDGER_PASS))
        try:
            res.raise_for_status()
            res = json.loads(res.content).get('objects')
            if not res:
                return False
            return True
        except:
            raise
    else:
        logger.warn('CMS_URL not set, ledger.payments.utils.validSystem will always return true')
        return True

def calculate_excl_gst(amount):
    percentage = D(100 - settings.LEDGER_GST)/ D(100.0)
    return percentage * D(amount)

def createBasket(product_list,owner,system,vouchers=None,force_flush=True):
    ''' Create a basket so that a user can check it out.
        @param product_list - [
            {
                "id": "<id of the product in oscar>",
                "quantity": "<quantity of the products to be added>"
            }
        ]
        @param - owner (user id or user object)
    '''
    try:
        if not validSystem(system):
            raise ValidationError('A system with the given id does not exist.')
        old_basket = basket = None
        valid_products = []
        User = get_user_model()
        # Check if owner is of class AUTH_USER_MODEL or id
        if not isinstance(owner, AnonymousUser):
            if not isinstance(owner, User):
                owner = User.objects.get(id=owner)
            # Check if owner has previous baskets
            if owner.baskets.filter(status='Open'):
                old_basket = owner.baskets.get(status='Open')

        # Use the previously open basket if its present or create a new one 
        if old_basket:
            if system.lower() == old_basket.system.lower() or not old_basket.system:
                basket = old_basket
                if force_flush:
                    basket.flush()
            else:
                raise ValidationError('You have a basket that is not completed in system {}'.format(old_basket.system))
        else:
            basket = Basket()
        # Set the owner and strategy being used to create the basket    
        if isinstance(owner, User):
            basket.owner = owner
        basket.system = system
        basket.strategy = selector.strategy(user=owner)
        # Check if there are products to be added to the cart and if they are valid products
        if not product_list:
            raise ValueError('There are no products to add to the order.')
        for product in product_list:
            p = Product.objects.get(id=product["id"])
            if not product.get("quantity"):
                product["quantity"] = 1
            valid_products.append({'product': p, 'quantity': product["quantity"]})
        # Add the valid products to the basket
        for p in valid_products:
            basket.add_product(p['product'],p['quantity'])
        # Add vouchers to the basket
        if vouchers is not None:
            for v in vouchers:
                basket.vouchers.add(Voucher.objects.get(code=v["code"]))
        # Save the basket
        basket.save()
        return basket
    except Product.DoesNotExist:
        raise
    except Exception as e:
        raise

def createCustomBasket(product_list,owner,system,vouchers=None,force_flush=True):
    ''' Create a basket so that a user can check it out.
        @param product_list - [
            {
                "id": "<id of the product in oscar>",
                "quantity": "<quantity of the products to be added>"
            }
        ]
        @param - owner (user id or user object)
    '''
    #import pdb; pdb.set_trace()
    try:
        if not validSystem(system):
            raise ValidationError('A system with the given id does not exist.')
        old_basket = basket = None
        valid_products = []
        User = get_user_model()
        # Check if owner is of class AUTH_USER_MODEL or id
        if not isinstance(owner, AnonymousUser):
            if not isinstance(owner, User):
                owner = User.objects.get(id=owner)
            # Check if owner has previous baskets
            if owner.baskets.filter(status='Open'):
                old_basket = owner.baskets.get(status='Open')
        
        # Use the previously open basket if its present or create a new one    
        if old_basket:
            if system.lower() == old_basket.system.lower() or not old_basket.system:
                basket = old_basket
                if force_flush:
                    basket.flush()
            else:
                raise ValidationError('You have a basket that is not completed in system {}'.format(old_basket.system))
        else:
            basket = Basket()
        # Set the owner and strategy being used to create the basket    
        if isinstance(owner, User):
            basket.owner = owner
        basket.system = system
        basket.strategy = selector.strategy(user=owner)
        basket.custom_ledger = True
        # Check if there are products to be added to the cart and if they are valid products
        defaults = ('ledger_description','quantity','price_incl_tax','oracle_code')
        for p in product_list:
            if not all(d in p for d in defaults):
                raise ValidationError('Please make sure that the product format is valid')
            p['price_excl_tax'] = calculate_excl_gst(p['price_incl_tax'])
        # Save the basket
        basket.save()
        # Add the valid products to the basket
        for p in product_list:
            basket.addNonOscarProduct(p)
        # Save the basket (again)
        basket.save()
        # Add vouchers to the basket
        if vouchers is not None:
            for v in vouchers:
                basket.vouchers.add(Voucher.objects.get(code=v["code"]))
            basket.save()
        return basket
    except Product.DoesNotExist:
        raise
    except Exception as e:
        raise

#Oracle Parser
def generateOracleParserFile(oracle_codes):
    strIO = StringIO()
    fieldnames = ['Activity Code','Amount']
    writer = csv.writer(strIO)
    writer.writerow(fieldnames)
    for k,v in oracle_codes.items():
        if v != 0:
            writer.writerow([k,v])
    strIO.flush()
    strIO.seek(0)
    return strIO

def sendInterfaceParserEmail(oracle_codes,system_name,system_id,error_email=False,error_string=None):
    try:
        dt = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        if not error_email:
            _file = generateOracleParserFile(oracle_codes)
            try:
                sys = OracleInterfaceSystem.objects.get(system_id=system_id)
                recipients = sys.recipients.all()
            except OracleInterfaceSystem.DoesNotExist:
                recipients = []
                
            email = EmailMessage(
                'Oracle Interface Summary for {} as at {}'.format(system_name,dt),
                'Oracle Interface Summary File for {} as at {}'.format(system_name,dt),
                settings.DEFAULT_FROM_EMAIL,
                to=[r.email for r in recipients]if recipients else [settings.NOTIFICATION_EMAIL]
            )
            email.attach('OracleInterface_{}.csv'.format(dt), _file.getvalue(), 'text/csv')
        else:
            email = EmailMessage(
                'Oracle Interface Summary Error for {} as at{}'.format(system_name,dt),
                'There was an error in generating a summary report for the oracle interface parser.Please refer to the following log output:\n{}'.format(error_string),
                settings.DEFAULT_FROM_EMAIL,
                to=[r.email for r in recipients]if recipients else [settings.NOTIFICATION_EMAIL]
            )
        
        email.send()
    except Exception as e:
        print(traceback.print_exc())
        raise e

def addToInterface(oracle_codes,system_name):
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    for k,v in oracle_codes.items():
        if v != 0:
            OracleInterface.objects.create(
                receipt_number = 0,
                receipt_date = date,
                activity_name = k,
                amount = v,
                customer_name = system_name,
                description = k,
                comments = '{} GST/{}'.format(k,date),
                status = 'NEW',
                status_date = date
            )
def oracle_parser(date,system,system_name):
    with transaction.atomic():
        try:
            op,created = OracleParser.objects.get_or_create(date_parsed=date)
            bpoint_txns = []
            bpoint_qs = [i.bpoint_transactions.filter(settlement_date=date,response_code=0) for i in Invoice.objects.filter(system=system)]
            for x in bpoint_qs:
                if x:
                    for t in x:
                        bpoint_txns.append(t)
            oracle_codes = {}
            parser_codes = {}
            # Bpoint Processing
            parser_codes,oracle_codes = bpoint_oracle_parser(op,parser_codes,oracle_codes,bpoint_txns)
            # Convert Deimals to strings as they cannot be serialized
            for k,v in parser_codes.items():
                for a,b in v.items():
                    for r,f in b.items():
                        parser_codes[k][a][r] = str(parser_codes[k][a][r])
            for k,v in parser_codes.items():
                OracleParserInvoice.objects.create(reference=k,details=json.dumps(v),parser=op)
            # Add items to oracle interface table 
            addToInterface(oracle_codes,system_name)
            # Send an email with all the activity codes entered into the interface table
            sendInterfaceParserEmail(oracle_codes,system_name,system)  
            return oracle_codes
        except Exception as e:
            error = traceback.print_exc()
            sendInterfaceParserEmail(oracle_codes,system_name,system,error_email=True,error_string=error)
            raise e

def bpoint_oracle_parser(parser,oracle_codes,parser_codes,bpoint_txns):
    try:
        for txn in bpoint_txns:
            invoice = Invoice.objects.get(reference=txn.crn1)
            if invoice.reference not in parser_codes.keys():
                parser_codes[invoice.reference] = {} 
            items = invoice.order.lines.all()
            items_codes = [i.oracle_code for i in items]
            for i in items_codes:
                if i not in oracle_codes.keys():
                    oracle_codes[i] = D('0.0')
                if i not in parser_codes[invoice.reference].keys():
                    parser_codes[invoice.reference] = {i:{'payment': D('0.0'),'refund': D('0.0')}}
            # Start Parsing items in invoices
            payable_amount = txn.amount
            for i in items:
                code = i.oracle_code
                # Check previous parser results for this invoice
                previous_invoices = OracleParserInvoice.objects.filter(reference=invoice.reference)
                code_paid_amount = D('0.0')
                code_refunded_amount = D('0.0')
                for p in previous_invoices:
                    details = dict(json.loads(p.details))
                    for k,v in details.items():
                        p_item = details[k]
                        if k == code:
                            code_paid_amount +=  D(p_item['payment'])
                            code_refunded_amount += D(p_item['refund'])
                # Deal with the current txn
                if txn.action == 'payment':
                    code_payable_amount = i.line_price_incl_tax - code_paid_amount
                    amt = code_payable_amount if code_payable_amount <= payable_amount else payable_amount
                    oracle_codes[code] += amt
                    payable_amount -= amt 
                    code_paid_amount += amt
                    for k,v in parser_codes[invoice.reference][code].items():
                        item = parser_codes[invoice.reference][code]
                        if k == 'payment':
                            item[k] += amt

                elif txn.action == 'refund':
                    code_refundable_amount = i.line_price_incl_tax - code_refunded_amount
                    amt = code_refundable_amount if code_refundable_amount <= payable_amount else payable_amount
                    oracle_codes[code] -= amt
                    payable_amount -= amt 
                    code_refunded_amount += amt
                    for k,v in parser_codes[invoice.reference][code].items():
                        item = parser_codes[invoice.reference][code]
                        if k == 'refund':
                            item[k] += amt
        return parser_codes,oracle_codes
    except Exception as e:
        print(traceback.print_exc())
        raise e

def update_payments(invoice):
    try:
        i = invoice
        # Bpoint Transactions
        for line in i.order.lines.all():
            paid_amount = line.paid 
            refunded_amount = line.refunded
            amount = line.line_price_incl_tax
            # Bpoint Amounts
            for bpoint in i.bpoint_transactions:
                if bpoint.approved: 
                    if paid_amount < amount:
                        if bpoint.action == 'payment':
                            remaining_amount = amount - paid_amount
                            if bpoint.id in line.payment_details['card'].keys():
                                new_amount  = D(line.payment_details['card'][bpoint.id]) + remaining_amount if remaining_amount <= bpoint.amount else bpoint.amount
                                line.payment_details['card'][bpoint.id] = str(new_amount)
                                paid_amount += remaining_amount if remaining_amount <= bpoint.amount else bpoint.amount
                            else:
                                new_amount  = D(0.0) + remaining_amount if remaining_amount <= bpoint.amount else bpoint.amount
                                line.payment_details['card'][bpoint.id] = str(new_amount)
                                paid_amount += remaining_amount if remaining_amount <= bpoint.amount else bpoint.amount
                    if refunded_amount < amount:
                        if bpoint.action == 'refund':
                            remaining_amount = amount - refunded_amount
                            if bpoint.id in line.refund_details['card'].keys():
                                new_amount = D(line.refund_details['card'][bpoint.id]) + remaining_amount if remaining_amount <= bpoint.amount else bpoint.amount
                                line.refund_details['card'][bpoint.id] = str(new_amount)
                                refunded_amount += remaining_amount if remaining_amount <= bpoint.amount else bpoint.amount
                            else:
                                new_amount = D(0.0) + remaining_amount if remaining_amount <= bpoint.amount else bpoint.amount
                                line.refund_details['card'][bpoint.id] = str(new_amount)
                                refunded_amount += remaining_amount if remaining_amount <= bpoint.amount else bpoint.amount
            # Bpay Transactions
            for bpay in i.bpay_transactions:
                if bpay.approved:
                    if paid_amount < amount:
                        if bpay.p_instruction_code == '05'and bpay.type == 399:
                            remaining_amount = amount - paid_amount
                            if bpay.id in line.payment_details['bpay'].keys():
                                new_amount  = D(line.payment_details['bpay'][bpay.id]) + remaining_amount if remaining_amount <= bpay.amount else bpay.amount
                                line.payment_details['bpay'][bpay.id] = str(new_amount)
                                paid_amount += remaining_amount if remaining_amount <= bpay.amount else bpay.amount
                            else:
                                new_amount  = D(0.0) + remaining_amount if remaining_amount <= bpay.amount else bpay.amount
                                line.payment_details['bpay'][bpay.id] = str(new_amount)
                                paid_amount += remaining_amount if remaining_amount <= bpay.amount else bpay.amount
                    if refunded_amount < amount:
                        if bpay.p_instruction_code == '25'and bpay.type == 699:
                            remaining_amount = amount - refunded_amount
                            if bpay.id in line.refund_details['bpay'].keys():
                                new_amount = D(line.refund_details['bpay'][bpay.id]) + remaining_amount if remaining_amount <= bpay.amount else bpay.amount
                                line.refund_details['bpay'][bpay.id] = str(new_amount)
                                refunded_amount += remaining_amount if remaining_amount <= bpay.amount else bpay.amount
                            else:
                                new_amount = D(0.0) + remaining_amount if remaining_amount <= bpay.amount else bpay.amount
                                line.refund_details['bpay'][bpay.id] = str(new_amount)
                                refunded_amount += remaining_amount if remaining_amount <= bpay.amount else bpay.amount
            # Cash Transactions
            for c in i.cash_transactions.all():
                if paid_amount < amount:
                    if c.type == 'payment':
                        remaining_amount = amount - paid_amount
                        if c.id in line.payment_details['cash'].keys():
                            new_amount  = D(line.payment_details['cash'][c.id]) + remaining_amount if remaining_amount <= c.amount else c.amount
                            line.payment_details['cash'][c.id] = str(new_amount)
                            paid_amount += remaining_amount if remaining_amount <= c.amount else c.amount
                        else:
                            new_amount  = D(0.0) + remaining_amount if remaining_amount <= c.amount else c.amount
                            line.payment_details['cash'][c.id] = str(new_amount)
                            paid_amount += remaining_amount if remaining_amount <= c.amount else c.amount
                if refunded_amount < amount:
                    if c.type == 'refund':
                        remaining_amount = amount - refunded_amount
                        if c.id in line.refund_details['cash'].keys():
                            new_amount = D(line.refund_details['cash'][c.id]) + remaining_amount if remaining_amount <= c.amount else c.amount
                            line.refund_details['cash'][c.id] = str(new_amount)
                            refunded_amount += remaining_amount if remaining_amount <= c.amount else c.amount
                        else:
                            new_amount = D(0.0) + remaining_amount if remaining_amount <= c.amount else c.amount
                            line.refund_details['cash'][c.id] = str(new_amount)
                            refunded_amount += remaining_amount if remaining_amount <= c.amount else c.amount
            line.save()
    except:
        print(traceback.print_exc())
        raise
