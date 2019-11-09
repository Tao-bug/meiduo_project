from apps.goods import models

import json
from django import http
from django.shortcuts import render
from django.views import View


# 购物车管理
class CartsView(View):
    """购物车管理"""
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
            pass
        else:
            # 用户未登录，操作cookie购物车
            pass
        return http.JsonResponse({'code': 0, 'errmsg': '添加购物车成功'})