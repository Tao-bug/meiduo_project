from django.shortcuts import render


# 1.首页 广告页
from django.views import View


class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')
