from django.conf import settings
from django.contrib.auth.backends import ModelBackend
import re
from itsdangerous import BadData
from meiduo_mall.settings.dev import logger
from utils.secret import SecretOauth
from .models import User


# 验证token并提取user
def check_verify_email_token(token):
    """
    验证token并提取user
    :param token: 用户信息签名后的结果
    :return: user, None
    """
    try:
        # 接受token
        token_dict = SecretOauth().loads(token)
    except BadData:
        return None

    try:
        user = User.objects.get(id=token_dict['user_id'], email=token_dict['email'])
    except Exception as e:
        logger.error(e)
        return None
    else:
        return user


# 生成 激活 链接
def generate_verify_email_url(user):
    # 1. user_id email
    dict_data = {'user_id': user.id, 'email': user.email}

    # 2.参数加密
    from utils.secret import SecretOauth
    secret_data = SecretOauth().dumps(dict_data)

    # 3.拼接 完整的路由
    verify_url = settings.EMAIL_ACTIVE_URL + '?token=' + secret_data

    return verify_url


# 封装函数
def get_user_by_account(account):
    """
    根据account查询用户
    :param account: 用户名或者手机号
    :return: user
    """
    try:
        if re.match('^1[3-9]\d{9}$', account):
            # 手机号登录
            user = User.objects.get(mobile=account)
        else:
            # 用户名登录
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """自定义用户认证后端"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方法，实现多账号登录
        :param request: 请求对象
        :param username: 用户名
        :param password: 密码
        :param kwargs: 其他参数
        :return: user
        """
        # 根据传入的username获取user对象。username可以是手机号也可以是账号
        user = get_user_by_account(username)
        # 校验user是否存在并校验密码是否正确
        if user and user.check_password(password):
            return user
