
from django.conf.urls import url

from apps.users import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view()),

    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),

    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),

    # 登陆页面显示 login/
    url(r'^login/$', views.LoginView.as_view(), name='login'),

    # 退出登陆
    url(r'^logout/$', views.LogoutView.as_view()),
]
