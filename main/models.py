from django.db import models


# Create your models here.
class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=1000)
    img = models.CharField(max_length=1000)
    wxid = models.CharField(max_length=1000)
    balance = models.IntegerField(default=0)
    balance_redpack = models.IntegerField(default=0)
    qrcode = models.BinaryField()
    createtime = models.DateTimeField(auto_now_add=True)
    lastlogintime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Account(models.Model):
    id = models.AutoField(primary_key=True)
    userid = models.ForeignKey('User',
                               on_delete=models.CASCADE,
                               related_name='transaction_to_user')
    counterparty = models.ForeignKey('User',
                                     on_delete=models.CASCADE,
                                     related_name='counterparty_to_user')
    debit = models.IntegerField(default=0)
    credit = models.IntegerField(default=0)
    balance = models.IntegerField(default=0)
    balance_redpack = models.IntegerField(default=0)
    remark = models.CharField(max_length=1000)
    tagid = models.ForeignKey('Remarktag',
                              on_delete=models.CASCADE,
                              related_name='tagid_to_remarktag')
    transaction_time = models.DateTimeField(auto_now_add=True)
    transactionid = models.CharField(max_length=100)


class Remarktag(models.Model):
    id = models.AutoField(primary_key=True)
    tag = models.CharField(max_length=100)
    bottom = models.IntegerField(default=0)
    top = models.IntegerField(default=0)
    enable = models.IntegerField(default=1)


class Redpack(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey('User',
                               on_delete=models.CASCADE,
                               related_name='redpack_to_user')#红包发出人
    amount = models.IntegerField(default=0)  #红包金额
    amountleft = models.IntegerField(default=0)  #红包余额
    transaction_time = models.DateTimeField(auto_now_add=True)#红包发出时间
    ttype = models.IntegerField(default=0) #0表示普通红包、1表示拼手气红包
    count = models.IntegerField(default=0)  #红包数量
    countleft = models.IntegerField(default=0)  #剩余红包数量
    remark = models.CharField(max_length=1000)  #红包备注


class Scrapredpack(models.Model):
    id = models.AutoField(primary_key=True)
    scraper = models.ForeignKey('User',
                                on_delete=models.CASCADE,
                                related_name='scrapredpack_to_user')  #抢红包的人
    redpack = models.ForeignKey('Redpack',
                                on_delete=models.CASCADE,
                                related_name='scrapredpack_to_redpack')  #抢的红包
    amount = models.IntegerField(default=0)  #抢到的红包金额
    transaction_time = models.DateTimeField(auto_now_add=True)  #抢红包的时间
