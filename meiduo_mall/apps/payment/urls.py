
from django.conf.urls import url

from . import views

urlpatterns = [
    # 获取支付宝的支付网址
    url(r'^payment/(?P<order_id>\d+)/$', views.PaymentView.as_view()),

]
