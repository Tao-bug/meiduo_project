from django.shortcuts import render
from django_redis import get_redis_connection
import json
from django import http
from django.views import View

from apps.goods import models
from apps.goods.models import SKU
from utils.cookiesecret import CookieSecret


# 购物车管理
class CartsView(View):
    """购物车管理"""

    # 展示购物车
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            # 连接redis
            client = get_redis_connection('carts')
            # redis取
            carts_data = client.hgetall(request.user.id)
            # 转换格式-->和cookie一样的字典 方便后面构建数据
            # cart_dict = {}
            # for key, value in carts_data.items():
            #     sku_id = int(key.decode())
            #     sku_dict = json.loads(value.decode())
            #     cart_dict[sku_id] = sku_dict

            carts_dict = {
                int(k.decode()): json.loads(v.decode()) for k, v in carts_data.items()
            }

        else:
            # 从cookie取
            cookie_str = request.COOKIES.get('carts')
            # 判断有无---有---解密
            if cookie_str:
                carts_dict = CookieSecret.loads(cookie_str)
            else:
                carts_dict = {}

        sku_ids = carts_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts_dict.get(sku.id).get('count'),
                'selected': str(carts_dict.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts_dict.get(sku.id).get('count')),
            })
        context = {
            'cart_skus': cart_skus,
        }

        return render(request, 'cart.html', context)

    # 增加
    def post(self, request):
        """添加购物车"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 判断参数是否齐全
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断sku_id是否存在
        try:
            models.SKU.objects.get(id=sku_id)
        except models.SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception:
            return http.HttpResponseForbidden('参数count有误')
        # 判断selected是否为bool值
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected有误')

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，操作redis购物车
            # 3.1 登录 使用redis存储
            carts_redis_client = get_redis_connection('carts')

            # 3.2 获取以前数据库的数据
            client_data = carts_redis_client.hgetall(user.id)

            # 如果商品已经存在就更新数据
            if str(sku_id).encode() in client_data:
                # 根据sku_id 取出商品
                child_dict = json.loads(client_data[str(sku_id).encode()].decode())
                #  个数累加
                child_dict['count'] += count
                # 更新数据
                carts_redis_client.hset(user.id, sku_id, json.dumps(child_dict))

            else:
                # 如果商品已经不存在--直接增加商品数据
                carts_redis_client.hset(user.id, sku_id, json.dumps({'count': count, 'selected': selected}))
                return http.JsonResponse({'code': 0, 'errmsg': '添加购物车成功'})
        else:
            # 用户未登录，操作cookie购物车
            # 用户未登录，操作cookie购物车
            cart_str = request.COOKIES.get('carts')
            # 如果用户操作过cookie购物车
            if cart_str:
                # 解密出明文
                cart_dict = CookieSecret.loads(cart_str)
            else:  # 用户从没有操作过cookie购物车
                cart_dict = {}

            # 判断要加入购物车的商品是否已经在购物车中,如有相同商品，累加求和，反之，直接赋值
            if sku_id in cart_dict:
                # 累加求和
                origin_count = cart_dict[sku_id]['count']
                count += origin_count
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 转成密文
            cookie_cart_str = CookieSecret.dumps(cart_dict)

            # 创建响应对象
            response = http.JsonResponse({'code': 0, 'errmsg': '添加购物车成功'})
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', cookie_cart_str, max_age=24 * 30 * 3600)
            return response



