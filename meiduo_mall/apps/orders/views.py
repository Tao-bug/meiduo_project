from django.shortcuts import render
from django.views import View


# 结算订单页面显示
class OrderSettlementView(View):
    def get(self, request):

        return render(request, 'place_order.html')
