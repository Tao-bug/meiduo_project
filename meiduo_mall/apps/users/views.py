import re

from django import http


from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from pymysql import DatabaseError

from apps.users.models import User


class RegisterView(View):

    # 1、注册页面显示
    def get(self, request):
        return render(request, 'register.html')

    # 2、 注册功能实现
    def post(self, request):
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        password2 = data.get('password2')
        mobile = data.get('mobile')
        # 短信验证码
        # sms_code = request.POST.get('sms_code')
        allow = data.get('allow')

        # 判断参数是否齐全
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        # 注册用户
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})

        # 保持登陆状态
        from django.contrib.auth import login
        login(request, user)

        # 跳转首页 redirect(reverse())
        # return redirect('/')
        return redirect(reverse('contents:index'))

