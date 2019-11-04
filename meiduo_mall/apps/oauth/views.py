from QQLoginTool.QQtool import OAuthQQ
from django import http
from django.conf import settings
from django.shortcuts import render
from django.views import View


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

        login_url = oauth.get_qq_url()

        return http.JsonResponse({'code': 0, 'errmsg': 'QQ登录页面网址', 'login_url': login_url})