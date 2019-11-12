import json
from decimal import Decimal
from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils.datetime_safe import datetime
from django.views import View
from django_redis import get_redis_connection

from apps.areas.models import Address
from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from utils.response_code import RETCODE


# 提交订单成功
class OrderSuccessView(LoginRequiredMixin, View):
    def get(self, request):
        """提交订单成功"""
        # 接收参数
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')

        # 修改为前端数据格式
        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)


#  提交订单
class OrderCommitView(LoginRequiredMixin, View):
    """订单提交"""
    def post(self, request):
        """保存订单信息和订单商品信息"""
        # 获取当前要保存的订单数据
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        # 校验参数
        if not all([address_id, pay_method]):
            return http.HttpResponseForbidden('缺少必传参数')

        # 判断address_id 是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Exception:
            return http.HttpResponseForbidden('参数address_id错误')

        # 判断pay_method 是否合法
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('参数pay_method错误')

        # 获取登录用户
        user = request.user
        # 生成订单编号：年月日时分秒+用户编号
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        # 显式的开启一个事务
        from django.db import transaction
        # --------设置事物起始--------
        with transaction.atomic():

            # --------事物保存点--------
            save_id = transaction.savepoint()

            try:
                # 保存订单基本信息 OrderInfo（一）
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                # 从购物车 取出选中的商品
                client = get_redis_connection('carts')
                carts_data = client.hgetall(user.id)
                carts_dict = {}
                for key, value in carts_data.items():
                    sku_id = key
                    sku_dict = json.loads(value.decode())
                    if sku_dict['selected']:
                        carts_dict[sku_id] = sku_dict

                # 遍历 商品信息
                sku_ids = carts_dict.keys()
                for sku_id in sku_ids:

                    while True:
                        sku = SKU.objects.get(id=sku_id)

                        # 原始销量 和  库存量
                        origin_sales = sku.sales
                        origin_stock = sku.stock

                        # 判断货源是否充足
                        cart_count = carts_dict[sku_id]['count']
                        if cart_count > sku.stock:

                            # --------事物回滚--------
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})

                        # 延迟测试 bug
                        # import time
                        # time.sleep(10)

                        # sku减少库存, 增加销量
                        sku.stock -= cart_count
                        sku.sales += cart_count
                        sku.save()

                        # 使用乐观锁 更新库存量
                        new_stock = origin_stock - cart_count
                        new_sales = origin_sales + cart_count
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                          sales=new_sales)
                        # 如果下单下单失败,库存足够则继续下单,直到下单成功或者库存不足
                        if result == 0:
                            continue

                        # SPU 增加销量
                        sku.spu.sales += cart_count
                        sku.spu.save()

                        # 保存订单商品信息
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=cart_count,
                            price=sku.price,
                        )

                        # 保存商品订单中总价和总数量
                        order.total_count += cart_count
                        order.total_amount += (cart_count * sku.price)

                        # 下单成功 或失败跳出
                        break

                # 添加邮费和保存订单
                order.total_amount += order.freight
                order.save()

            except Exception as e:

                # --------事物回滚--------
                transaction.savepoint_rollback(save_id)
                return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单失败'})

            # --------提交事物--------
            transaction.savepoint_commit(save_id)

        # 清除购物车已经结算过的商品
        client.hdel(user.id, *carts_dict)

        # 返回响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order.order_id})


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
