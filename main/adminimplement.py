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
from django.db.models import Sum
from django.db.models import Count
from main import implement
log = logging.getLogger("collect")


'''
获取用户列表
'''


def admingetusers(page):
    try:
        users = models.User.objects.exclude(Q(id=1) | Q(id=2)).values(
                                                                'id',
                                                                'name',
                                                                'img',
                                                                'wxid',
                                                                'balance',
                                                                'balance_redpack',
                                                                'createtime',
                                                                'lastlogintime')
        r1 = Paginator(users, 10)
        try:
            r2 = r1.page(page)
        except PageNotAnInteger:
            r2 = r1.page(1)
        except EmptyPage:
            r2 = r1.page(r1.num_pages)
        return r2, r1.num_pages,r2.number
    except Exception as e:
        log.error(e)
        return '', 0, 0



'''
获取用户信息
'''


def admingetuserinfobyid(id):
    result = {}
    usrobj = models.User.objects.filter(id=id)
    curUser = None
    if (usrobj.exists()):
        curUser = usrobj[0]
        result['credittotal'] = curUser.transaction_to_user.aggregate(
            total=Sum('credit'))['total']  #获得积分
        result['debittotal'] = curUser.transaction_to_user.aggregate(
            total=Sum('debit'))['total']  #送出积分
        result['canuse'] = curUser.balance - curUser.balance_redpack  #可兑换积分
        result.update(
            usrobj.values(  'id',
                            'name',
                            'img',
                            'wxid',
                            'balance',
                            'balance_redpack',
                            'createtime',
                            'lastlogintime')[0])
    return result


'''
获取用户账户信息
'''


def admingetuseraccountinfobyid(id,page):
    try:
        usrobj = models.User.objects.filter(id=id)
        curUser = None
        if (usrobj.exists()):
            curUser = usrobj[0]
            trans = curUser.transaction_to_user.values(
                                        'userid__name',
                                        'debit',
                                        'credit',
                                        'balance',
                                        'balance_redpack',
                                        'counterparty__name',
                                        'transaction_time',
                                        'transactionid',
                                        'userid__img',
                                        'counterparty__img',
                                        'remark',
                                        'tagid__tag').order_by('-transaction_time')

            r1 = Paginator(trans, 10)
            try:
                r2 = r1.page(page)
            except PageNotAnInteger:
                r2 = r1.page(1)
            except EmptyPage:
                r2 = r1.page(r1.num_pages)
            return r2, r1.num_pages, r2.number
        return '', 0, 0
    except Exception as e:
        log.error(e)
        return '', 0, 0



'''
根据tagid获取账户信息
'''


def admingetuseraccountinfobytagid(id, page):
    try:
        tags = models.Remarktag.objects.filter(id=id)
        tag = None
        if (tags.exists()):
            tag = tags[0]
            trans = tag.tagid_to_remarktag.values(
                                        'userid__name',
                                        'debit',
                                        'credit',
                                        'balance',
                                        'balance_redpack',
                                        'counterparty__name',
                                        'transaction_time',
                                        'transactionid',
                                        'userid__img',
                                        'counterparty__img',
                                        'remark',
                                        'tagid__tag').order_by('-transaction_time')

            r1 = Paginator(trans, 10)
            try:
                r2 = r1.page(page)
            except PageNotAnInteger:
                r2 = r1.page(1)
            except EmptyPage:
                r2 = r1.page(r1.num_pages)
            return r2, r1.num_pages, r2.number
        return '', 0, 0

    except Exception as e:
        log.error(e)
        return '', 0, 0



'''
获取用户红包信息
'''


def admingetuserredpackinfo(request):
    pass


'''
获取所有红包信息
'''


def admingetredpacks(page):
    try:
        redpacks = models.Redpack.objects.values(   'id',
                                                    'sender__name',
                                                    'sender__id',
                                                    'sender__img',
                                                    'amount',
                                                    'amountleft',
                                                    'ttype',
                                                    'count',
                                                    'countleft',
                                                    'transaction_time',
                                                    'remark')

        r1 = Paginator(redpacks, 10)
        try:
            r2 = r1.page(page)
        except PageNotAnInteger:
            r2 = r1.page(1)
        except EmptyPage:
            r2 = r1.page(r1.num_pages)
        return r2, r1.num_pages, r2.number
    except Exception as e:
        log.error(e)
        return '', 0, 0

'''
获取红包明细
'''


def admingetredpackinfobyid(id):
    result = {}
    redpack = models.Redpack.objects.filter(id=id)
    if (redpack.exists()):
        redpack = redpack[0]
        result = redpack.scrapredpack_to_redpack.values('id',
                                               'scraper__name',
                                               'scraper__id',
                                               'amount',
                                               'transaction_time',
                                               'scraper__img')
    return result


'''
获取标签信息
'''


def admingettags():
    try:
        tags = models.Remarktag.objects.values('id').annotate(
            count=Count('tagid_to_remarktag')).values(  'id',
                                                        'tag',
                                                        'top',
                                                        'bottom',
                                                        'count')

        return tags
    except Exception as e:
        log.error(e)
        return ''


'''
回收全部可送余额并充值指定金额可送金额
'''


def adminreset(id,ttype,amount):
    result = []
    if (ttype > 2 or ttype < 0 or amount <= 0):
        return result
    if (id == -1):
        #全部用户
        users = models.User.objects.exclude(Q(id=1) | Q(id=2)).values(
            'id', 'wxid', 'name', 'balance_redpack')
        for user in users:
            item = {}
            r = implement.transfer(user['wxid'], '-1', user['balance_redpack'], ttype,
                            '回收红包', '',-1)
            log.info('回收%s的红包 %d' % (user['name'], user['balance_redpack']))

            r = r and implement.transfer('-1', user['wxid'], amount, ttype, '发放红包','', -1)
            log.info('给%s发放红包 %d' % (user['name'], amount))
            item['id'] = user['id']
            item['result'] = r
            result.append(item)

    else:
        user = models.User.objects.filter(id=id).values('id','wxid', 'name', 'balance_redpack')
        if (user.exists()):
            user = user[0]
            item = {}
            r = True
            if ttype == 0:
                r = implement.transfer(user['wxid'], '-1', user['balance_redpack'], ttype,
                    '回收红包', '',-1)
                log.info('回收%s的红包 %d' % (user['name'], user['balance_redpack']))

            r = r and implement.transfer('-1', user['wxid'], amount, ttype, '发放', '',-1)
            log.info('给%s发放 %d' % (user['name'], amount))
            item['id'] = user['id']
            item['result'] = r
            result.append(item)
    return result


'''
自动对账
'''


def reconciliation(request):
    '''
    0、单人对账和全部对账
    1、每个transactionid都对应两条交易记录，这两条交易记录的debit和credit交叉相等，userid和counterpartyid交叉相等
    2、
    '''
    
    pass


'''
修改标签信息
'''


def adminmodifytags(id,ttype,newtag,enable,top,bottom):
    #禁用或者新增，不能删除和修改已有的文本
    try:
        tag = ''
        if ttype == 0:
            #新增tag
            tag = models.Remarktag.objects.create(tag=newtag,
                                                  top=top,
                                                  bottom=bottom,
                                                  enable=enable)
        elif ttype == 1:
            #禁用tag或者启用tag
            tag = models.Remarktag.objects.filter(id=id)
            if (tag.exists()):
                tag = tag[0]
                tag.enable = enable
                tag.save()
        return True, tag.id

    except Exception as e:
        log.error(e)
        return False,''


'''
获取和修改重要参数
'''


def admingetpara(request):
    #appid,secret
    pass