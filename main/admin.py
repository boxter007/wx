from django.contrib import admin

# Register your models here.
from . import models
admin.site.register(models.User)
admin.site.register(models.Account)
admin.site.register(models.Remarktag)
admin.site.register(models.Redpack)
admin.site.register(models.Scrapredpack)