from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpRequest
import json
import logging
from main import models
from main import implement
from django.db.models import Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

log = logging.getLogger("collect")
'''
### 根据客户ID获取其账户信息
- Method: GET
- Url:   http://ip:port/getaccountinfo/
- para:
-- id:微信openid
- Return:
-- para1:可用积分
-- para2:累计积分
-- para3:获得的积分
-- para4:送出的积分
-- para5:可兑换积分
-- wxid:微信openid
-- result:是否执行成功
'''
def getaccountinfo(request):
    try:
        context = {}
        id = request.GET.get('id', '')
        log.info('"Method":"getaccountinfo","ID":"%s"' % id)
        if id == '':
            context['result'] = False
        else:
            usrobj = models.User.objects.filter(wxid=id)
            curUser = None
            if (usrobj.exists()):
                curUser = usrobj[0]
                context['para1'] = curUser.balance_redpack  #可用积分
                context['para2'] = curUser.balance  #累计积分
                context['para3'] = curUser.transaction_to_user.aggregate(total=Sum('credit'))['total'] #获得积分
                context['para4'] = curUser.transaction_to_user.aggregate(total=Sum('debit'))['total']  #送出积分
                context['para5'] = curUser.balance - curUser.balance_redpack  #送出积分

            context['wxid'] = id
            context['result'] = True

        result = json.dumps(context, ensure_ascii=False)
        log.info('"Method":"getaccountinfo","ID":"%s","Return":%s' % (id, result))
        return HttpResponse(result, content_type='application/json')
    except Exception as e:
        log.error(e)
        return HttpResponse('', content_type='application/json')


'''
### 根据客户ID获取积分排名,及积分TOP5名单
- Method: GET
- Url:   http://ip:port/gettop5/
- para:
-- id：微信openid
- Return:
-- para1:排名列表
--- wxid:微信openid
--- name:微信昵称
--- balance:累计积分余额
--- balance_redpack:可送出积分
-- para2:名次
-- wxid:微信openid
-- result:是否执行成功
'''
def gettop5(request):
    try:
        context = {}
        id = request.GET.get('id', '')
        log.info('"Method":"gettop5","ID":"%s"' % id)
        if id == '':
            context['result'] = False
        else:

            context['para1'] = []
            r = list(
                models.User.objects.exclude(wxid=-1).values(
                    'wxid', 'name', 'balance',
                    'balance_redpack').order_by('-balance'))  #积分排名
            i = 0
            j = 0
            for item in r:
                if item['wxid'] != id:
                    i = i + 1
                if j < 5:
                    context['para1'].append(item)
                    j = j + 1

            context['para2'] = i
            context['result'] = True
        context['wxid'] = id
        result = json.dumps(context, ensure_ascii=False)
        log.info('"Method":"gettop5","ID":"%s","Return":%s' % (id, result))
        return HttpResponse(result, content_type='application/json')
    except Exception as e:
        log.error(e)
        return HttpResponse('', content_type='application/json')


'''
### 获取二维码（需要将返回的图片缓存在客户端）
- Method: GET
- Url:   http://ip:port/getqrcode/
- para:
-- id：微信openid
- Return:
- 图片（content_type='image/jpeg'）
'''
def getqrcode(request):
    context = None
    openid = request.GET.get('id', '')
    log.info('"Method":"getqrcode","id":"%s"' % openid)
    usr = models.User.objects.filter(wxid=openid)
    if (usr.exists()):
        user = usr[0]
        context = user.qrcode
    #log.info('"Method":"getqrcode","ID":"%s","Return":%s' % (openid,context))
    return HttpResponse(context, content_type='image/jpeg')

'''
### 查询用户
- Method: GET
- Url:   http://ip:port/getuser/
- para:
-- id：微信openid
- Return
-- wxid:微信openid
-- name:用户昵称
-- url:用户头像地址
-- result:是否执行成功
'''
def getuser(request):
    context = {}
    id = request.GET.get('id', '')
    log.info('"Method":"getuser","id":"%s"' % id)
    if id == '' :
        context['result'] = False
    else:
        user = models.User.objects.filter(wxid=id)
        if (user.exists()):
            context['wxid'] = id
            context['name'] = user[0].name
            context['url'] = user[0].img
            context['result'] = True
        else:
            context['result'] = False

    result = json.dumps(context, ensure_ascii=False)
    log.info('"Method":"getuser","ID":"%s","Return":%s' % (id, result))
    return HttpResponse(result, content_type='application/json')


'''
### 新增用户(返回的openid需要缓存在客户端)
- Method: GET
- Url:   http://ip:port/adduser/
- para:
-- code：wx.login返回的code
-- name：微信昵称
- Return
-- wxid:微信openid
-- result:是否执行成功
'''
def adduser(request):
    try:
        context = {}
        id = request.GET.get('code', '')
        name = request.GET.get('name', '')
        url = request.GET.get('url', '')
        log.info('"Method":"adduser","Code"="%s","name":"%s","url":"%s"' % (id, name,url))
        if id == '' or name == '' :
            context['result'] = False
        else:
            openid = implement.getopenid(id)
            user = models.User.objects.filter(wxid=openid)
            if (not user.exists()):
                qrcode = implement.makeqrcode(openid)
                log.info("Method:adduser qrcode=%s" , qrcode)
                user = models.User.objects.create(wxid=openid,
                                                name=name,
                                                qrcode=qrcode,
                                                img=url)
                # 此处需要修改手动充值
                implement.transfer('-1', openid, 200, 0, '初始化红包')
            context['wxid'] = openid
            context['result'] = True
    except Exception as e:
        log.error(e)
    result = json.dumps(context, ensure_ascii=False)
    log.info('"Method":"adduser","ID","%s","Return":%s' % (id, result))
    return HttpResponse(result, content_type='application/json')


'''
### 收款
- Method: GET
- Url:   http://ip:port/transaction/
- para:
-- id：付款者微信openid
-- amount：转账金额
-- receiver：收款者openid
-- remark: 付款备注
- Return
-- wxid:微信openid
-- result:是否执行成功
'''
def transaction(request):
    context = {}
    id = request.GET.get('id', '')
    amount = request.GET.get('amount', 0)
    receiver = request.GET.get('receiver', '')
    remark = request.GET.get('remark', '')
    log.info('"Method":"transaction","ID":"%s","amount":"%s","payer":"%s","receiver":"%s"' %
             (id, amount, id, receiver))
    context['wxid'] = id
    if id =='' or amount =='' or  receiver == '' or id == receiver:
        context['result'] = False
    else:
        context['result'] = implement.transfer(id, receiver, int(amount), 2,
                                               remark)
    result = json.dumps(context, ensure_ascii=False)
    log.info('"Method":"transaction","ID"="%s","Return":%s' % (id, result))
    return HttpResponse(result, content_type='application/json')


'''
### 查询交易记录
- id：微信openid
- Method: GET
- Url:   http://ip:port/transactionhistory/
- para:
-- id：微信openid
-- page:页码，默认为1。
- Return
-- wxid:微信openid
-- para1:列表
--- userid__name：交易方
--- debit:支出金额
--- credit：收入金额
--- balance：累计余额
--- balance_redpack：红包余额
--- counterparty__name：交易对手
--- transaction_time：交易时间
--- transactionid:交易id
--- userid__img：交易对手头像
-- currentpage: 当前页
-- totalpages: 总页数
-- result: 是否执行成功
'''
def transactionhistory(request):
    context = {}
    id = request.GET.get('id', '')
    page = request.GET.get('page', 1)
    log.info('"Method":"transactionhistory","ID":"%s","page":"%s"' % (id,page))
    context['wxid'] = id
    if id == '':
        context['result'] = False
    else:
        r2,context['totalpages'],context['currentpage'] = implement.gettransferlist(id, page)
        context['para1'] = list(r2)
        context['result'] = True

    result = json.dumps(context, cls=implement.DateEncoder, ensure_ascii=False)
    log.info('"Method":"transactionhistory","ID":"%s","Return":%s' %
             (id, result))
    return HttpResponse(result, content_type='application/json')

def test(request):
    context = {}
    id = request.GET.get('id', '')
    log.info('Method:test ID=%s ' % (id))
    if id == '':
        context['result'] = False
    else:
        context['userid'] = id
        context['para1'] = implement.getaccesstoken()
        context['result'] = True

    result = json.dumps(context, cls=implement.DateEncoder, ensure_ascii=False)
    log.info('Method:test ID=%s       Return=%s' % (id, result))
    return HttpResponse(result, content_type='application/json')