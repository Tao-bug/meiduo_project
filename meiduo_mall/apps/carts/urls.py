
from django.conf.urls import url

from . import views

urlpatterns = [
    # 购物车
    url(r'^carts/$', views.CartsView.as_view(), name='carts'),

    # 全选购物车carts/selection/
    url(r'^carts/selection/$', views.CartsSelectAllView.as_view()),

    # 展示商品页面简单购物车 carts/simple/


]
