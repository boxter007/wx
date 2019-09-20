import logging
from main import models
from main import implement

log = logging.getLogger("collect")


def monthly():
    log.info("start")
    users = models.User.objects.values('wxid', 'name','balance_redpack')
    for user in users:
        implement.transfer(user['wxid'], '-1', user['balance_redpack'], 0, '回收红包')
        log.info('回收%s的红包 %d' % (user['name'],user['balance_redpack']))
        implement.transfer('-1', user['wxid'], 200, 0, '月初红包')
        log.info('发放%s的月初红包 200' % (user['name']))
