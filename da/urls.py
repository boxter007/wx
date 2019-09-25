from django.contrib import admin
from django.urls import path
from . import view
from . import adminview
urlpatterns = [
    path('admin/', admin.site.urls),
    path('getqrcode/', view.getqrcode),
    path('getaccountinfo/', view.getaccountinfo),
    path('gettop5/', view.gettop5),
    path('adduser/', view.adduser),
    path('transaction/', view.transaction),
    path('transactionhistory/', view.transactionhistory),
    path('getuser/', view.getuser),
    path('getmarktag/', view.getmarktag),
    path('sendredpack/', view.sendredpack),
    path('scrapredpack/', view.scrapredpack),
    path('redpackrecorde/', view.redpackrecorde),
    path('admingetusers/', adminview.admingetusers),
    path('admingetuserinfobyid/', adminview.admingetuserinfobyid),
    path('admingetuseraccountinfobyid/',
         adminview.admingetuseraccountinfobyid),
    path('admingettags/', adminview.admingettags),
    path('admingetuseraccountinfobytagid/',
         adminview.admingetuseraccountinfobytagid),
    path('admingetredpacks/', adminview.admingetredpacks),
    path('admingetredpackinfobyid/', adminview.admingetredpackinfobyid),
    path('adminmodifytags/', adminview.adminmodifytags),
    path('adminreset/', adminview.adminreset),
]