
from django.conf.urls import url

from . import views

urlpatterns = [
    # 结算订单页面显示
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view(), name='settlement'),

    # 提交订单接口 orders/commit/
    url(r'^orders/commit/$', views.OrderCommitView.as_view(), name='commit'),

    # 展示提交订单成功页面orders/success/
    url(r'^orders/success/$', views.OrderSuccessView.as_view(), name='success'),

]
