from QQLoginTool.QQtool import OAuthQQ
from django import http
from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from apps.oauth.models import OAuthQQUser


# 判断是否绑定
def is_bind_openid(openid, request):
    # 绑定过----首页
    try:
        qq_user = OAuthQQUser.objects.get(openid=openid)
    except OAuthQQUser.DoesNotExist:
        # 未绑定---绑定页面
        return render(request, 'oauth_callback.html')
    else:
        user = qq_user.user
        # 绑定---首页
        # 保持登陆状态
        login(request, user)

        # 重定向首页
        response = redirect(reverse("contents:index"))

        # 设置cookie
        response.set_cookie('username', user.username, max_ge=14*24*3600)

        return response


# 用户扫码登录的回调处理QQAuthUserView
# code--token--openid--是否绑定
class QQAuthCallBackView(View):
    def get(self, request):
        # / oauth_callback?code = 31FFB8402D24214889BA444821D3CC3E & state = % 2Finfo % 2F
        # 1.解析code
        code = request.GET.get('code')

        if not code:
            return http.HttpResponseForbidden('无效的code!')

        # 获取QQ登录页面网址
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)
        try:
            # code --- token
            token = oauth.get_access_token(code)

            # token --- openid
            openid = oauth.get_open_id(token)
        except Exception as e:
            return http.HttpResponseForbidden('认证失败')

        # 是否绑定
        response = is_bind_openid(openid, request)

        return response


# 返回qq登录地址
class QQAuthURLView(View):
    """提供QQ登录页面网址
    https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=xxx&redirect_uri=xxx&state=xxx
    """
    def get(self, request):
        # next表示从哪个页面进入到的登录页面，将来登录成功后，就自动回到那个页面
        next = request.GET.get('next')

        # 获取QQ登录页面网址
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)
        # 获取QQ登录扫码页面，扫码后得到Authorization Code
        login_url = oauth.get_qq_url()

        return http.JsonResponse({'code': 0, 'errmsg': 'QQ登录页面网址', 'login_url': login_url})
