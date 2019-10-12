from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from main import adminimplement
from main import util
from django.http import HttpResponse, HttpRequest

log = logging.getLogger("collect")
'''
获取用户列表
'''
def admingetusers(request):
    context = {}
    page = request.GET.get('page', 1)
    log.info('[%s][Request][%s]' %
                 ('', json.dumps(request.GET, ensure_ascii=False)))
    page, context['totalpages'], context['currentpage'] = adminimplement.admingetusers(page)


    context['list'] = list(page)
    context['result'] = True

    result = json.dumps(context, cls=util.DateEncoder, ensure_ascii=False)
    log.info('[%s][Response][%s]' % ('', result))
    return HttpResponse(result, content_type='application/json')


'''
获取用户信息
'''
def admingetuserinfobyid(request):

    context = {}
    id = int(request.GET.get('id', -1))
    log.info('[%s][Request][%s]' %
                 (id, json.dumps(request.GET, ensure_ascii=False)))
    if id == '':
        context['result'] = False
    else:
        context['userinfo'] = adminimplement.admingetuserinfobyid(id)
        context['result'] = True

    result = json.dumps(context, cls=util.DateEncoder, ensure_ascii=False)
    log.info('[%s][Response][%s]' % (id, result))

    return HttpResponse(result, content_type='application/json')


'''
获取用户账户信息
'''
def admingetuseraccountinfobyid(request):
    context = {}
    id = int(request.GET.get('id', -1))
    page = request.GET.get('page', 1)
    log.info('[%s][Request][%s]' %
             (id, json.dumps(request.GET, ensure_ascii=False)))
    if id == '':
        context['result'] = False
    else:
        page, context['totalpages'], context['currentpage'] = adminimplement.admingetuseraccountinfobyid(id,page)
        context['accountinfo'] = list(page)
        context['result'] = True

    result = json.dumps(context, cls=util.DateEncoder, ensure_ascii=False)
    log.info('[%s][Response][%s]' % (id, result))


    return HttpResponse(result, content_type='application/json')


'''
根据tagid获取账户信息
'''


def admingetuseraccountinfobytagid(request):
    context = {}
    id = int(request.GET.get('id', -1))
    page = request.GET.get('page', 1)
    log.info('[%s][Request][%s]' %
             (id, json.dumps(request.GET, ensure_ascii=False)))
    if id == '':
        context['result'] = False
    else:
        page, context['totalpages'], context[
            'currentpage'] = adminimplement.admingetuseraccountinfobytagid(
                id, page)
        context['accountinfo'] = list(page)
        context['result'] = True

    result = json.dumps(context, cls=util.DateEncoder, ensure_ascii=False)
    log.info('[%s][Response][%s]' % (id, result))

    return HttpResponse(result, content_type='application/json')


'''
获取用户红包信息
'''
def admingetuserredpackinfo(request):
    pass

'''
获取所有红包信息
'''
def admingetredpacks(request):
    context = {}
    page = request.GET.get('page', 1)
    log.info('[%s][Request][%s]' %
             ('', json.dumps(request.GET, ensure_ascii=False)))

    context['list'], context['totalpages'], context['currentpage'] = adminimplement.admingetredpacks(page)
    context['list'] = list(context['list'])
    result = json.dumps(context, cls=util.DateEncoder, ensure_ascii=False)

    log.info('[%s][Response][%s]' % ('', result))
    return HttpResponse(result, content_type='application/json')

'''
获取红包明细
'''
def admingetredpackinfobyid(request):
    context = {}
    id = int(request.GET.get('id', -1))
    log.info('[%s][Request][%s]' %
             (id, json.dumps(request.GET, ensure_ascii=False)))
    context = list(adminimplement.admingetredpackinfobyid(id))

    result = json.dumps(context, cls=util.DateEncoder, ensure_ascii=False)

    log.info('[%s][Response][%s]' % (id, result))
    return HttpResponse(result, content_type='application/json')


'''
获取标签信息
'''
def admingettags(request):
    context = {}
    log.info('[%s][Request][%s]' %
             ('', json.dumps(request.GET, ensure_ascii=False)))

    context['tags'] = list(adminimplement.admingettags())
    context['result'] = True

    result = json.dumps(context, cls=util.DateEncoder, ensure_ascii=False)
    log.info('[%s][Response][%s]' % ('', result))
    return HttpResponse(result, content_type='application/json')


'''
回收全部可送余额并充值指定金额可送金额
'''
def adminreset(request):
    context = {}
    amount = int(request.GET.get('amount', -1))
    ttype = int(request.GET.get('ttype', -1))
    id = int(request.GET.get('id', -1))

    log.info('[%s][Request][%s]' %
             (id, json.dumps(request.GET, ensure_ascii=False)))

    context['result'] = adminimplement.adminreset(id, ttype, amount)

    result = json.dumps(context, cls=util.DateEncoder, ensure_ascii=False)
    log.info('[%s][Response][%s]' % (id, result))
    return HttpResponse(result, content_type='application/json')


'''
自动对账
'''
def reconciliation(request):
    pass


'''
修改标签信息
'''


def adminmodifytags(request):
    context = {}
    id = int(request.GET.get('id', -1))
    top = int(request.GET.get('top', -1))
    bottom = int(request.GET.get('bottom', -1))
    tag = request.GET.get('tag', '')
    ttype = int(request.GET.get('ttype', -1))
    enable = int(request.GET.get('enable', -1))

    log.info('[%s][Request][%s]' %
             (id, json.dumps(request.GET, ensure_ascii=False)))

    context['result'],context['id'] = adminimplement.adminmodifytags(id, ttype, tag, enable,
                                                    top, bottom)

    result = json.dumps(context, cls=util.DateEncoder, ensure_ascii=False)
    log.info('[%s][Response][%s]' % (id, result))
    return HttpResponse(result, content_type='application/json')


'''
获取和修改重要参数
'''
def admingetpara(request):
    #appid,secret
    pass