import requests
import json
from django.conf import settings
from django.core.cache import cache


def retrieve_department_users():
    res = requests.get('{}/api/users?minimal'.format(settings.CMS_URL), auth=(settings.LEDGER_USER,settings.LEDGER_PASS))
    try:
        res.raise_for_status()
        cache.set('department_users',json.loads(res.content).get('objects'),3600)
    except:
        raise

def get_department_user(email):
    res = requests.get('{}/api/users?email={}'.format(settings.CMS_URL,email), auth=(settings.LEDGER_USER,settings.LEDGER_PASS))
    try:
        res.raise_for_status()
        data = json.loads(res.content).get('objects')
        if len(data) > 0:
            return data[0]
        else:
            return None
    except:
        raise

