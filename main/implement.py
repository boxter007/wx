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
import threading
import vthread
import random
from django.core.cache import cache

log = logging.getLogger("collect")

appid = 'wxf29113dcf17a3978'
secret = 'f7add42fb8cdfc50549f3ced26f89264'


def transfer(user, counterparty, amount, ttype, remark, formid, tag):
    result = False
    mutex = threading.Lock()
    mutex.acquire()
    try:
        with transaction.atomic():
            A = models.User.objects.filter(wxid=user)
            B = models.User.objects.filter(wxid=counterparty)
            T = models.Remarktag.objects.filter(id = tag)
            if (not A.exists()) or (not B.exists) or (not T.exists()):
                return False
            A = A[0]
            B = B[0]
            T = T[0]
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
                    tagid=T,
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
                    tagid=T,
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
                    tagid=T,
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
                    tagid=T,
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
                    tagid=T,
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
                    tagid=T,
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
        result = True
    except Exception as e:
        log.exception(e)
        result = False
    finally:
        mutex.release()

    if (formid != ''):

        firetransmessage(user, A.name, counterparty,B.name, formid, amount,
                         '#%s#%s' % (T.tag, remark),
                         datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         transid)

    return result

def gettransferlist(user, page):
    try:
        usrobjs = models.User.objects.filter(wxid=user)
        if (usrobjs.exists()):
            usrobj = usrobjs[0]
            trans = usrobj.transaction_to_user.values(
                'userid__name', 'debit', 'credit', 'balance',
                'balance_redpack', 'counterparty__name', 'transaction_time',
                'transactionid', 'userid__img', 'counterparty__img', 'remark',
                'tagid__tag').order_by('-transaction_time')

            r1 = Paginator(trans, 10)
            try:
                r2 = r1.page(page)
            except PageNotAnInteger:
                r2 = r1.page(1)
            except EmptyPage:
                r2 = r1.page(r1.num_pages)

            return r2, r1.num_pages,r2.number
    except Exception as e:
        log.exception(e)
        return None

def getalltransferlist(page):
    try:
        accountobjs = models.Account.objects.exclude(
            Q(userid_id=1) | Q(counterparty_id=1)
            | Q(userid_id=2) | Q(userid_id=2)).filter(credit=0)
        if (accountobjs.exists()):
            trans = accountobjs.values(
                'userid__name', 'debit', 'credit', 'balance',
                'balance_redpack', 'counterparty__name', 'transaction_time',
                'transactionid', 'counterparty__img', 'userid__img', 'remark',
                'tagid__tag').order_by('-transaction_time')
            r1 = Paginator(trans, 10)
            try:
                r2 = r1.page(page)
            except PageNotAnInteger:
                r2 = r1.page(1)
            except EmptyPage:
                r2 = r1.page(r1.num_pages)

            return r2, r1.num_pages, r2.number
        else:
            return '','0','0'
    except Exception as e:
        log.exception(e)
        return '', '0', '0'


def makeqrcode(openid):
    try:
        url = 'https://api.weixin.qq.com/wxa/getwxacode?access_token=%s' % getaccesstoken(
        )

        data = json.dumps({
            'width': 480,
            'path': 'pages/trade/trade?scene=%s' % openid,
            'auto_color': True
        })
        log.info('[%s][Process]["RequestUrl":"%s","PostData":"%s"]' % (openid, url, data))

        response = requests.post(url, data)
        log.info('[%s][Process]["Response.Status":"%s"]' %
                 (openid, response.status_code))

        if (response.status_code == 200):
            return response.content
        else:
            return ''
    except Exception as e:
        log.exception(e)
        return ''


@vthread.thread
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
        log.info('[%s][Process]["request":"%s"]' % (sender,data))
        response = requests.post(url, data, headers=headers)
        log.info('[%s][Process]["response":"%s"]' % (sender, response.content))


    except Exception as e:
        log.exception(e)


def sendredpack(id, amount, ttype, count, remark):
    sender = models.User.objects.filter(wxid=id)
    if not sender.exists():
        return False
    sender = sender[0]
    if ttype == 0:
        amount = amount * count
    #现将钱转至红包管家
    if (transfer(sender.wxid, -2, amount, 1, '发红包', '',-1)):
        #创建红包
        try:
            transA = models.Redpack.objects.create( sender=sender,
                                                    amount=amount,
                                                    amountleft=amount,
                                                    ttype=ttype,
                                                    remark=remark,
                                                    count=count,
                                                    countleft=count)
        except Exception as e:
            log.exception(e)
            transfer(-2, sender.wxid, amount, 1, '回滚红包', '',-1)
            return False
        return True
    return False

def scrapredpack(id,redpackid):
    scraper = models.User.objects.filter(wxid=id)
    redpack = models.Redpack.objects.filter(id=redpackid)
    if (not scraper.exists()) or (not redpack.exists):
        return False
    scraper = scraper[0]
    redpack = redpack[0]

    returnamount = 0
    returnlist = {}
    result = False

    mutex = threading.Lock()
    mutex.acquire()
    try:

        #先判断是否抢过这个红包如果抢过则只返回列表
        userobj = redpack.scrapredpack_to_redpack.filter(scraper=scraper)
        if (userobj.exists()):
            #已经抢过红包，直接返回抢到的金额和列表
            returnamount = userobj[0].amount
        else:
            #再判断是否有可抢的红包
            if redpack.countleft > 0:
                #剩余数量大于零，剩余金额肯定大于零。有红包可抢。
                if (redpack.ttype == 0):
                    #普通红包
                    returnamount = redpack.amount / redpack.count
                else:
                    #拼手气红包
                    returnamount = makeredpack(redpack.countleft,redpack.amountleft)
                redpack.amountleft = redpack.amountleft - returnamount
                redpack.countleft = redpack.countleft - 1
                with transaction.atomic():
                    redpack.save()
                    scrapredpack = models.Scrapredpack.objects.create(
                        scraper=scraper, amount=returnamount, redpack=redpack)

                transfer(-2, id, returnamount, 1, '抢红包', '',-1)
                result = True
        #没有红包了返回列表
        returnlist['para1'] = list(redpack.scrapredpack_to_redpack.values(
            'scraper__name', 'amount', 'transaction_time'))
        returnlist['id'] = redpack.id
        returnlist['sender'] = redpack.sender.name
        returnlist['img'] = redpack.sender.img
        returnlist['amount'] =redpack.amount
        returnlist['amountleft'] =redpack.amountleft
        returnlist['count'] =redpack.count
        returnlist['countleft'] =redpack.countleft
        returnlist['remark'] =redpack.remark
        returnlist['transaction_time'] = redpack.transaction_time
    except Exception as e:
        log.exception(e)
    finally:
        mutex.release()
    return result, returnamount, returnlist


def redpackrecorde(id, ttype, page):
    try:
        userobj = models.User.objects.filter(wxid=id)
        if (userobj.exists()):
            userobj = userobj[0]
            trans = None
            if ttype == 1:
                #抢到的红包
                trans = userobj.scrapredpack_to_user.values(
                                                        'redpack__sender__name',
                                                        'redpack',
                                                        'amount',
                                                        'transaction_time',
                                                        'redpack__ttype')
            elif ttype == 0:
                #发出去的红包
                trans = userobj.redpack_to_user.values('sender__name',
                                                       'id', 'amount',
                                                       'transaction_time',
                                                       'ttype',
                                                       'count',
                                                       'countleft',
                                                       'amountleft')

            r1 = Paginator(trans, 10)
            try:
                r2 = r1.page(page)
            except PageNotAnInteger:
                r2 = r1.page(1)
            except EmptyPage:
                r2 = r1.page(r1.num_pages)
            return r2, r1.num_pages,r2.number
    except Exception as e:
        log.exception(e)
        return None

def getopenid(js_code):
    try:
        grant_type = 'authorization_code'
        url = 'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' % (
            appid, secret, js_code)
        log.info('[%s][Process]["RequestUrl":"%s"]' % (js_code, url))

        response = requests.get(url)
        log.info('[%s][Process]["Response.Status":"%s","Response.text":"%s"]' %
                 (js_code, response.status_code, response.text))

        if (response.status_code == 200):
            result = json.loads(response.text)
            return result.get('openid','')
        else:
            return ''
    except Exception as e:
        log.exception(e)
        return ''

def getaccesstoken():
    if cache.get('token') == None:
        try:
            url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (
                appid, secret)
            log.info('[%s][Process]["RequestUrl":"%s"]' % ('',url))
            response = requests.get(url)
            log.info(
                '[%s][Process]["Response.Status":"%s","Response.text":"%s"]' %
                ('', response.status_code, response.text))

            if (response.status_code == 200):
                result = json.loads(response.text)
                cache.set('token', result['access_token'],60*60)
                return result['access_token']
            else:
                return ''
        except Exception as e:
            log.exception(e)
            return ''
    else:
        return cache.get('token')


def makeredpack(count, amount):
    if count == 1:
        return amount
    amountleft = amount - (count - 1) * 1
    return random.randint(1, amountleft)
