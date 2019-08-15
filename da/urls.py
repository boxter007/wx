from django.contrib import admin
from django.urls import path
from . import view
urlpatterns = [
    path('admin/', admin.site.urls),
    path('getqrcode/', view.getqrcode),
    path('getaccountinfo/', view.getaccountinfo),
    path('gettop5/', view.gettop5),
    path('adduser/', view.adduser),
    path('transaction/', view.transaction),
    path('transactionhistory/', view.transactionhistory),
    path('test/', view.test),
]