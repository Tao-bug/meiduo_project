
from django.conf.urls import url

from apps.users import views

urlpatterns = [
    # 1.注册页面 显示
    url(r'^register/$', views.RegisterView.as_view()),

    # 2. 判断用户名是否重复 usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),

    # 3. 判断手机号 是否 重复 mobiles/(?P<mobile>1[3-9]\d{9})/count/
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),

    # 4.登陆页面显示 login/
    url(r'^login/$', views.LoginView.as_view(), name='login'),

    # 5.退出登陆
    url(r'^logout/$', views.LogoutView.as_view()),

    # 6.用户中心 info/
    url(r'^info/$', views.UserInfoView.as_view(), name='info'),

    # 7.新增邮箱 emails/
    url(r'^emails/$', views.EmailView.as_view(), name='emails'),

    # 8.激活邮箱  emails/verification/
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),

    # 9. 收货地址  address/
    url(r'^address/$', views.AddressView.as_view()),

    # 10. 新增 收货地址 addresses/create/
    url(r'^addresses/create/$', views.AddressCreateView.as_view()),



]
