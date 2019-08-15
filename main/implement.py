from django.db import transaction
from . import models
from django.db.models import F
import uuid
import json
import datetime
import requests
import logging
log = logging.getLogger("collect")

appid = 'wxad901a90a74d3b9e'
secret = 'dcc381d508b71bdcd093a7ea43c1e092'

def transfer(user, counterparty, amount,ttype,remark):
    try:
        with transaction.atomic():
            A = models.User.objects.filter(wxid=user)
            B = models.User.objects.filter(wxid=counterparty)
            if (not A.exists()) or (not B.exists):
                return False
            A = A[0]
            B = B[0]
            #判断交易后余额，如果出现负值，则取消交易
            if (A.balance - amount < 0 ):
                return False

            #可用红包-->可用红包转账
            if (ttype == 0):
                #判断交易后余额，如果出现负值，则取消交易
                if (A.balance_redpack - amount < 0):
                    return False
                transid = uuid.uuid1().hex
                #发起方记账
                transA = models.Account.objects.create(
                    debit=amount,
                    credit=0,
                    balance=A.balance - amount,
                    balance_redpack=A.balance_redpack - amount,
                    remark=remark,
                    userid=A,
                    counterparty=B,
                    transactionid=transid)
                #交易对手记账
                transB = models.Account.objects.create(
                    debit=0,
                    credit=amount,
                    balance=B.balance + amount,
                    balance_redpack=B.balance_redpack + amount,
                    remark=remark,
                    userid=B,
                    counterparty=A,
                    transactionid=transid)
                #发起方减余额
                A.balance = transA.balance
                #发起方减红包余额
                A.balance_redpack = transA.balance_redpack
                A.save()
                #交易对手增余额
                B.balance = transB.balance
                #交易对手增红包余额
                B.balance_redpack = transB.balance_redpack
                B.save()

            #非红包-->非红包转账
            elif (ttype == 1):
                transid = uuid.uuid1().hex
                #发起方记账
                transA = models.Account.objects.create(
                    debit=amount,
                    credit=0,
                    balance=A.balance - amount,
                    balance_redpack=A.balance_redpack,
                    remark=remark,
                    userid=A,
                    counterparty=B,
                    transactionid=transid)
                #交易对手记账
                transB = models.Account.objects.create(
                    debit=0,
                    credit=amount,
                    balance=B.balance + amount,
                    balance_redpack=B.balance_redpack,
                    remark=remark,
                    userid=B,
                    counterparty=A,
                    transactionid=transid)
                #发起方减余额
                A.balance = transA.balance
                A.save()
                #交易对手增余额
                B.balance = transB.balance
                B.save()
            #可用红包-->非红包转账
            elif (ttype == 2):
                #判断交易后余额，如果出现负值，则取消交易
                if (A.balance_redpack - amount < 0):
                    return False
                transid = uuid.uuid1().hex
                #发起方记账
                transA = models.Account.objects.create(
                    debit=amount,
                    credit=0,
                    balance=A.balance - amount,
                    balance_redpack=A.balance_redpack - amount,
                    remark=remark,
                    userid=A,
                    counterparty=B,
                    transactionid=transid)
                #交易对手记账
                transB = models.Account.objects.create(
                    debit=0,
                    credit=amount,
                    balance=B.balance + amount,
                    balance_redpack=B.balance_redpack,
                    remark=remark,
                    userid=B,
                    counterparty=A,
                    transactionid=transid)
                #发起方减余额
                A.balance = transA.balance
                #发起方减红包余额
                A.balance_redpack = transA.balance_redpack
                A.save()
                #交易对手增余额
                B.balance = transB.balance
                B.save()
    except Exception as e:
        log.error(e)
        return False
    return True

def gettransferlist(user):
    try:
        usrobjs = models.User.objects.filter(wxid=user)
        if (usrobjs.exists()):
            usrobj = usrobjs[0]
            trans = usrobj.transaction_to_user.values(
                'userid__name', 'debit', 'credit', 'balance',
                'balance_redpack', 'counterparty__name',
                'transaction_time').order_by(
                    '-transaction_time')
            return list(trans)
    except Exception as e:
        log.error(e)
        return None

def makeqrcode(openid):
    try:
        url = 'https://api.weixin.qq.com/wxa/getwxacode?access_token=%s' % getaccesstoken(
        )

        data = json.dumps({
            'width': 480,
            'path': 'page/index/index?id=%s' % openid,
            'auto_color':True
        })
        log.info('makeqrcode    RequestUrl=%s   PostData=%s' % (url, data))
        response = requests.post(url, data)
        log.info('makeqrcode    Response.Status=%s' % response.status_code)
        if (response.status_code == 200):
            return response.content
        else:
            return ''
    except Exception as e:
        log.error(e)
        return ''


def getopenid(js_code):
    try:
        grant_type = 'authorization_code'
        url = 'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % (
            appid, secret, js_code)
        log.info('getopenid RequestUrl=%s' % url)
        response = requests.get(url)
        log.info('getopenid Response.Status=%s  Response.text=%s' %
                 (response.status_code,response.text))
        if (response.status_code == 200):
            result = json.loads(response.text)
            return result['openid']
        else:
            return ''
    except Exception as e:
        log.error(e)
        return ''

def getaccesstoken():
    try:
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (
            appid, secret)
        log.info('getaccesstoken RequestUrl=%s' % url)
        response = requests.get(url)
        log.info('getaccesstoken Response.Status=%s  Response.text=%s' %
                (response.status_code, response.text))
        if (response.status_code == 200):
            result = json.loads(response.text)
            return result['access_token']
        else:
            return ''
    except Exception as e:
        log.error(e)
        return ''

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,  datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)