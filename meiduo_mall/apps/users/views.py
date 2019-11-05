import json
import re
from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from pymysql import DatabaseError
from apps.users.models import User
from meiduo_mall.settings.dev import logger
from utils.response_code import RETCODE
from django.contrib.auth import authenticate, login, logout


# 新增邮箱
class EmailView(LoginRequiredMixin, View):
    """添加邮箱"""
    def put(self, request):
        """实现添加邮箱逻辑"""
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        email = json_dict.get('email')

        # 校验参数
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')

        # 赋值email字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})

        # 发邮件功能
        from apps.users.utils import generate_verify_email_url
        verify_url = generate_verify_email_url(request.user)

        from celery_tasks.email.tasks import send_verify_email
        send_verify_email.delay(email, verify_url)

        # 响应添加邮箱结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


# 用户中心
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        """提供个人信息界面"""
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }
        return render(request, 'user_center_info.html', context=context)


# 退出登陆
class LogoutView(View):
    """退出登录"""

    def get(self, request):
        """实现退出登录逻辑"""
        # 清理session
        logout(request)
        # 退出登录，重定向到登录页
        response = redirect(reverse('contents:index'))
        # 退出登录时清除cookie中的username
        response.delete_cookie('username')

        return response


# 用户登陆面显示
class LoginView(View):
    # 登陆页面显示
    def get(self, request):
        return render(request, 'login.html')

    def post(self,request):
        # 接收参数 : username password 记住登录
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # 校验参数
        if not all([username, password]):
            return HttpResponseForbidden('参数不齐全')
        #  用户名
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入5-20个字符的用户名')
        #  密码
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')

        # 验证用户名和密码--django自带的认证
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # 4.保持登录状态
        login(request, user)

        # 5.是否记住用户名
        if remembered != 'on':
            # 不记住用户名, 浏览器结束会话就过期
            request.session.set_expiry(0)
        else:
            # 记住用户名, 浏览器会话保持两周
            request.session.set_expiry(None)

        # next 获取
        next = request.GET.get('next')
        if next:
            response = redirect(reverse('users:info'))

        else:
            response = redirect(reverse('contents:index'))
        response.set_cookie("username", user.username, max_age=14 * 3600 * 24)

        # 6.返回响应结果 跳转首页
        return response


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        """
        :param request: 请求对象
        :param username: 用户名
        :return: JSON
        """
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


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
        sms_code = request.POST.get('msg_code')
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

        # 补充注册时短信验证后端逻辑
        from django_redis import get_redis_connection
        redis_code_client = get_redis_connection('sms_code')
        redis_code = redis_code_client.get("sms_%s" % mobile)

        if redis_code is None:
            return http.HttpResponseForbidden('无效的短信验证码')

        if sms_code != redis_code.decode():
            return http.HttpResponseForbidden('输入短信验证码有误')

        # 注册用户
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return http.HttpResponseForbidden('注册失败')

        # 保持登陆状态
        from django.contrib.auth import login
        login(request, user)

        # 跳转首页 redirect(reverse())
        # return redirect('/')
        return redirect(reverse('contents:index'))

