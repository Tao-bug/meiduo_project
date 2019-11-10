import json

from django_redis import get_redis_connection

from utils.cookiesecret import CookieSecret


def merge_cart_cookie_to_redis(request, response):
    """
    登录后合并cookie购物车数据到Redis
    :param request: 本次请求对象，获取cookie中的数据
    :param response: 本次响应对象，清除cookie中的数据
    :return: response
    """
    # cookie_dict
    cookie_str = request.COOKIES.get('carts')

    if cookie_str is not None:
        # 解密
        cookie_dict = CookieSecret.loads(cookie_str)

        # 链接 redis
        client = get_redis_connection('carts')

        # 覆盖redis数据库
        for sku_id in cookie_dict:
            client.hset(request.user.id, sku_id, json.dumps(cookie_dict[sku_id]))
        # 删除 cookie
        response.delete_cookie('carts')
