from django.shortcuts import render
from django_redis import get_redis_connection
import json
from django import http
from django.views import View

from apps.goods import models
from apps.goods.models import SKU
from utils.cookiesecret import CookieSecret


# 商品页面右上角购物车
class CartsSimpleView(View):
    def get(self, request):
        """商品页面右上角购物车"""
        # 判断用户是否登陆
        user = request.user
        if user.is_authenticated:
            # 用户已登录，查询Redis购物车
            client = get_redis_connection('carts')
            carts_data = client.hgetall(user.id)
            # 转换格式
            carts_dict = {int(k.decode()): json.loads(v.decode()) for k, v in carts_data.items()}
        elif carts_str := request.COOKIES.get('carts'):
            carts_dict = CookieSecret.loads(carts_str)
        else:
            carts_dict = {}

        sku_ids = carts_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = [
            {
                'id': sku.id,
                'name': sku.name,
                'count': carts_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image.url,
            }
            for sku in skus
        ]

        return http.JsonResponse({'code': 0, 'errmsg': 'OK', 'cart_skus': cart_skus})


# 全选购物车
class CartsSelectAllView(View):
    """全选购物车"""
    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected', True)

        # 校验参数
        if selected and not isinstance(selected, bool):
            return http.HttpResponseForbidden('参数selected有误')

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，操作redis购物车
            client = get_redis_connection('carts')
            carts_data = client.hgetall(user.id)

            # 将所有商品的 选中状态修改
            for key, value in carts_data.items():
                sku_id = int(key.decode())
                carts_dict = json.loads(value.decode())

                # 修改所有商品的 选中状态
                carts_dict['selected'] = selected
                client.hset(user.id, sku_id, json.dumps(carts_dict))
            return http.JsonResponse({'code': 0, 'errmsg': '全选购物车成功'})
        else:
            # 用户未登录，操作cookie购物车
            carts_str = request.COOKIES.get('carts')
            response = http.JsonResponse({'code': 0, 'errmsg': '全选购物车成功'})
            if carts_str is not None:
                carts_dict = CookieSecret.loads(carts_str)
                for sku_id in carts_dict:
                    carts_dict[sku_id]['selected'] = selected
                cookie_cart = CookieSecret.dumps(carts_dict)
                response.set_cookie('carts', cookie_cart, max_age=14*24*3600)
            return response


# 购物车管理
class CartsView(View):
    """购物车管理"""
    # 删除购物车
    def delete(self, request):
        """删除购物车"""
        # 接受参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 判断 sku_id 是否存在
        try:
            models.SKU.objects.get(id=sku_id)
        except models.SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')

        # 判断用户是否登陆
        user = request.user
        if user is not None and user.is_authenticated:
            # 用户登录，删除redis购物车
            client = get_redis_connection('carts')
            # 根据用户id 删除商品sku
            client.hdel(user.id, sku_id)
            # 删除结束后，没有响应的数据，只需要响应状态码即可
            return http.JsonResponse({'code': 0, 'errmsg': '删除购物车成功'})
        else:
            if cart_str := request.COOKIES.get('carts'):
                # 解密
                cart_dict = CookieSecret.loads(cart_str)
            else:
                cart_dict = {}
        # 创建响应对象
        response = http.JsonResponse({'code': 0, 'errmsg': '删除购物车成功'})
        if sku_id in cart_dict:
            # 删除数据
            del cart_dict[sku_id]
            # 加密
            cart_str = CookieSecret.dumps(cart_dict)
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', cart_str, max_age=24 * 30 * 3600)
        return response

    # 修改购物车
    def put(self, request):

        # 接受参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 校验参数
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断sku_id是否存在
        try:
            sku = models.SKU.objects.get(id=sku_id)
        except models.SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception:
            return http.HttpResponseForbidden('参数count有误')
        # 判断selected是否为bool值
        if selected and not isinstance(selected, bool):
            return http.HttpResponseForbidden('参数selected有误')

        # 判断是否登陆
        user = request.user
        # 接收cookie最后的数据
        cart_str = ""
        if user.is_authenticated:
            # 登陆 -- redis
            client = get_redis_connection('carts')
            # 覆盖redis以前的数据
            new_cart_dict = {'count': count, 'selected': selected}
            client.hset(user.id, sku_id, json.dumps(new_cart_dict))

        else:
            # 用户未登录，删除cookie购物车
            cart_str = request.COOKIES.get('carts')
            cart_dict = CookieSecret.loads(cart_str) if cart_str else {}
            # 覆盖以前的数据
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 转换成 密文数据
            cart_str = CookieSecret.dumps(cart_dict)

        # 构建前端的数据
        cart_sku = {
            'id': sku_id,
            'count': count,
            'selected': selected,
            'name': sku.name,
            'default_image_url': sku.default_image.url,
            'price': sku.price,
            'amount': sku.price * count,
        }
        response = http.JsonResponse({'code': 0, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})
        if not user.is_authenticated:
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', cart_str, max_age=24 * 30 * 3600)
        # 局部刷新--返回改完数据  字典
        return response

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

        elif cookie_str := request.COOKIES.get('carts'):
            carts_dict = CookieSecret.loads(cookie_str)
        else:
            carts_dict = {}

        sku_ids = carts_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = [
            {
                'id': sku.id,
                'name': sku.name,
                'count': carts_dict.get(sku.id).get('count'),
                'selected': str(
                    carts_dict.get(sku.id).get('selected')
                ),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts_dict.get(sku.id).get('count')),
            }
            for sku in skus
        ]

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
        if selected and not isinstance(selected, bool):
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
            if cart_str := request.COOKIES.get('carts'):
                # 解密出明文
                cart_dict = CookieSecret.loads(cart_str)
            else:
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



