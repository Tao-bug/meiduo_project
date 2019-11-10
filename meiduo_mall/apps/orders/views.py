import json
from decimal import Decimal
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from apps.areas.models import Address
from apps.goods.models import SKU


# 结算订单页面显示
class OrderSettlementView(View):
    def get(self, request):
        """提供订单结算页面"""
        # 获取登录用户
        user = request.user

        # 查询地址
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except:
            # 如果地址为空，渲染模板时会判断，并跳转到地址编辑页面
            addresses = None

        # 查询选中的商品
        client = get_redis_connection('carts')
        carts_data = client.hgetall(user.id)
        # 转换格式
        carts_dict = {}
        for key, value in carts_data.items():
            sku_id = int(key)
            sku_dict = json.loads(value.decode())
            if sku_dict['selected']:
                carts_dict[sku_id] = sku_dict

        # 计算金额和邮费
        total_count = 0
        total_amount = Decimal(0.00)

        skus = SKU.objects.filter(id__in=carts_dict.keys())
        for sku in skus:
            sku.count = carts_dict[sku.id].get('count')
            sku.amount = sku.count * sku.price

            # 计算总数量和金额
            total_count += sku.count
            total_amount += sku.amount

        # 运费
        freight = Decimal('10.00')

        # 转换前端数据格式
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight,
            'default_address_id': user.default_address_id
        }

        return render(request, 'place_order.html', context)
