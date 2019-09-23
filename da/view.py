from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpRequest
import json
import logging
from main import models
from main import implement
from django.db.models import Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F
import time
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
-- count:获取排行榜名单的数目
- Return:
-- para1:排名列表
--- wxid:微信openid
--- name:微信昵称
--- img:微信头像
--- balance5:累计积分余额
--- balance_redpack:可送出积分
-- para2:名次
-- para3:个人积分信息
--- para1:可用积分
--- para2:累计积分
--- para3:获得的积分
--- para4:送出的积分
--- para5:可兑换积分
-- wxid:微信openid
-- result:是否执行成功
'''
def gettop5(request):
    try:
        context = {}
        id = request.GET.get('id', '')
        count = int(request.GET.get('count', 10))
        log.info('"Method":"gettop5","ID":"%s","count":"%s"' % (id,count))
        if id == '':
            context['result'] = False
        else:

            context['para1'] = []
            r = list(
                models.User.objects.exclude(wxid=-1).annotate(
                    balance5=F('balance') - F('balance_redpack')).values(
                        'wxid', 'name','balance_redpack','img',
                        'balance5').order_by('-balance5'))  #积分排名
            me = 0
            j = 0
            for item in r:
                if item['wxid'] == id:
                    me = item
                if j < count:
                    context['para1'].append(item)
                    j = j + 1

            context['para2'] = r.index(me) + 1

            usrobj = models.User.objects.filter(wxid=id)
            curUser = None
            l = {}
            if (usrobj.exists()):
                curUser = usrobj[0]
                l['para1'] = curUser.balance_redpack  #可用积分
                l['para2'] = curUser.balance  #累计积分
                l['para3'] = curUser.transaction_to_user.aggregate(total=Sum('credit'))['total'] #获得积分
                l['para4'] = curUser.transaction_to_user.aggregate(total=Sum('debit'))['total']  #送出积分
                l['para5'] = curUser.balance - curUser.balance_redpack  #送出积分
            context['para3'] = l
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
    id = request.POST.get('id', request.GET.get('id',''))
    amount = request.POST.get('amount', request.GET.get('amount', 0))
    receiver = request.POST.get('receiver', request.GET.get('receiver', ''))
    remark = request.POST.get('remark', request.GET.get('remark', ''))
    formid = request.POST.get('formid', '')
    log.info('"Method":"transaction","ID":"%s","amount":"%s","payer":"%s","receiver":"%s"' %
             (id, amount, id, receiver))
    context['wxid'] = id
    if id =='' or amount =='' or  receiver == '' or id == receiver:
        context['result'] = False
    else:
        context['result'] = implement.transfer(id, receiver, int(amount), 2,
                                               remark, formid)
    result = json.dumps(context, ensure_ascii=False)
    log.info('"Method":"transaction","ID"="%s","Return":%s' % (id, result))




    return HttpResponse(result, content_type='application/json')


'''
### 查询交易记录
- id：微信openid
- Method: GET
- Url:   http://ip:port/transactionhistory/
- para:
-- id：微信openid,不填写则表示查询全体人员的全部交易记录
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
--- userid__img：交易方头像
--- counterparty__img：交易对手头像
--- remark: 交易备注
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
        r2, context['totalpages'], context['currentpage'] = implement.getalltransferlist(page)
    else:
        r2, context['totalpages'], context['currentpage'] = implement.gettransferlist(id, page)

    context['para1'] = list(r2)
    context['result'] = True
    result = json.dumps(context, cls=implement.DateEncoder, ensure_ascii=False)
    log.info('"Method":"transactionhistory","ID":"%s","Return":%s' %
             (id, result))
    return HttpResponse(result, content_type='application/json')


'''
### 获取标签
- Method: GET
- Url:   http://ip:port/getmarktag/
- Return
-- para1:列表
--- id:标签编号
--- tag:标签内容
--- bottom:该标签送出的积分下限
--- top:该标签送出的积分上限
-- result:是否执行成功
'''
def getmarktag(request):
    context = {}
    log.info('"Method":"getmarktag"')
    tags=models.Remarktag.objects.values('id','tag','bottom','top')
    context['para1'] = list(tags)
    context['result'] = True
    result = json.dumps(context, cls=implement.DateEncoder, ensure_ascii=False)
    log.info('"Method":"getmarktag","Return":"%s"' % result)
    return HttpResponse(result, content_type='application/json')

'''
### 发红包
- Method: GET
- Url:   http://ip:port/sendredpack/
- para:
-- id：微信openid
-- amount: 红包金额，拼手气红包为总金额，普通红包为单个红包金额
-- ttype: 红包类型,0为普通红包，1为拼手气红包
-- count: 红包数量
-- remark: 红包备注
- Return
-- result:是否执行成功
'''
def sendredpack(request):
    context = {}

    id = request.GET.get('id', '')
    amount = int(request.GET.get('amount', 0))
    ttype = int(request.GET.get('ttype', -1))
    count = int(request.GET.get('count', 0))
    remark = int(request.GET.get('remark', ''))
    log.info('"Method":"sendredpack","ID":"%s","amount":"%d","ttype":"%d","count":"%d","remark":"%s"' % (id,amount,ttype,count,remark))
    if id == '' or amount == 0 or ttype == -1 or count == 0 or remark == '':
        context['result'] = False
    else:
        context['result'] = implement.sendredpack(id,amount,ttype,count,remark)

    result = json.dumps(context, ensure_ascii=False)
    log.info('"Method":"sendredpack","Return":"%s"' % result)
    return HttpResponse(result, content_type='application/json')

'''
### 抢红包
- Method: GET
- Url:   http://ip:port/scrapredpack/
- para:
-- id：微信openid
-- redpackid: 红包id
- Return
-- para1:列表
--- amount:抢到的红包金额
--- list:抢红包的列表
-- result:是否执行成功
'''
def scrapredpack(request):
    context = {}

    id = request.GET.get('id', '')
    redpackid = int(request.GET.get('redpackid', 0))

    log.info('"Method":"scrapredpack","ID":"%s","redpackid":"%d"' % (id,redpackid))
    if (id == '' or redpackid == 0 ):
        context['result'] = False
    else:
        context['result'] = implement.scrapredpack(id, redpackid)

    result = json.dumps(context, cls=implement.DateEncoder, ensure_ascii=False)
    log.info('"Method":"scrapredpack","Return":"%s"' % result)
    return HttpResponse(result, content_type='application/json')
