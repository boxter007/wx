from django.db import transaction
from . import models
from django.db.models import F
from django.db.models import Q
import uuid
import json
import datetime
import requests
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

log = logging.getLogger("collect")

appid = 'wxf29113dcf17a3978'
secret = 'f7add42fb8cdfc50549f3ced26f89264'


def transfer(user, counterparty, amount,ttype,remark,formid):
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
    if (formid != ''):
        firetransmessage(user, A.name, counterparty,B.name, formid, amount,
                         remark,
                         datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         transid)

    return True


def gettransferlist(user, page):
    try:
        usrobjs = models.User.objects.filter(wxid=user)
        if (usrobjs.exists()):
            usrobj = usrobjs[0]
            trans = usrobj.transaction_to_user.values(
                'userid__name', 'debit', 'credit', 'balance',
                'balance_redpack', 'counterparty__name', 'transaction_time',
                'transactionid', 'userid__img', 'counterparty__img',
                'remark').order_by('-transaction_time')
            r1 = Paginator(trans, 10)
            try:
                r2 = r1.page(page)
            except PageNotAnInteger:
                r2 = r1.page(1)
            except EmptyPage:
                r2 = r1.page(r1.num_pages)

            return r2, r1.num_pages,r2.number
    except Exception as e:
        log.error(e)
        return None

def getalltransferlist(page):
    try:
        accountobjs = models.Account.objects.exclude(
            Q(userid_id=1) | Q(counterparty_id=1)).filter(credit = 0)
        if (accountobjs.exists()):
            trans = accountobjs.values(
                'userid__name', 'debit', 'credit', 'balance',
                'balance_redpack', 'counterparty__name', 'transaction_time',
                'transactionid', 'counterparty__img', 'userid__img',
                'remark').order_by('-transaction_time')
            r1 = Paginator(trans, 10)
            try:
                r2 = r1.page(page)
            except PageNotAnInteger:
                r2 = r1.page(1)
            except EmptyPage:
                r2 = r1.page(r1.num_pages)

            return r2, r1.num_pages,r2.number
    except Exception as e:
        log.error(e)
        return None


def makeqrcode(openid):
    try:
        url = 'https://api.weixin.qq.com/wxa/getwxacode?access_token=%s' % getaccesstoken(
        )

        data = json.dumps({
            'width': 480,
            'path': 'pages/trade/trade?scene=%s' % openid,
            'auto_color': True
        })
        log.info('"method":"makeqrcode","RequestUrl":"%s","PostData":"%s"' % (url, data))
        response = requests.post(url, data)
        log.info('"method":"makeqrcode","Response.Status":"%s"' % response.status_code)
        if (response.status_code == 200):
            return response.content
        else:
            return ''
    except Exception as e:
        log.error(e)
        return ''


def firetransmessage(sender, sendername, receiver, receivername, formid, amount,
                     remark, time, transid):
    try:
        url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token=%s' % getaccesstoken()
        jsontemplate = '{"touser": "%s","template_id": "%s","form_id": "%s","data": {"keyword1": {"value": "%s"},"keyword2": {"value": "%s"},"keyword3": {"value": "%s"} ,"keyword4": {"value": "%s"},"keyword5": {"value": "%s"}}}'
        headers = {'content-type': 'charset=utf8'}

        data = jsontemplate % (
            sender, 'XzN8Itq8kM7m5xSL9fG4GokRWfEzl7JbZeq3q0sPDbY', formid,
            transid, receivername, time, amount, remark)
        data = data.encode('UTF8')
        response = requests.post(url, data,headers = headers)
        data = jsontemplate % (
            receiver, 'fAHigjdz_1wFs3zGjeOJeLn6Ob5z-fJaRUi94TuUC0M', formid,
            transid, sendername, time, amount, remark)
        response = requests.post(url,data)
    except Exception as e:
        log.error(e)

def getopenid(js_code):
    try:
        grant_type = 'authorization_code'
        url = 'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % (
            appid, secret, js_code)
        log.info('"method":"getopenid","RequestUrl":"%s"' % url)
        response = requests.get(url)
        log.info('"method":"getopenid","Response.Status":"%s","Response.text":"%s"' %
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
        log.info('"method":"getaccesstoken","RequestUrl":"%s"' % url)
        response = requests.get(url)
        log.info('"method":"getaccesstoken","Response.Status":"%s","Response.text":"%s"' %
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