
from django.conf.urls import url

from . import views

urlpatterns = [
    # 结算订单页面显示
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view(), name='settlement'),

]
