from django.shortcuts import render
from django.views import View
from apps.contents.utils import get_categories


# 1.首页 广告页
class IndexView(View):
    """首页广告"""

    def get(self, request):
        """提供首页广告界面"""
        # 查询商品频道和分类
        categories = get_categories()

        # 渲染模板的上下文
        context = {
            'categories': categories,
        }
        return render(request, 'index.html', context)

