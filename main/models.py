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
    remark = models.CharField(max_length=100)
    transaction_time = models.DateTimeField(auto_now_add=True)
    transactionid = models.CharField(max_length=100)


class Remarktag(models.Model):
    id = models.AutoField(primary_key=True)
    tag = models.CharField(max_length=100)
    bottom = models.IntegerField(default=0)
    top = models.IntegerField(default=0)