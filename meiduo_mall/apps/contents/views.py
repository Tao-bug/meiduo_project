from django.shortcuts import render
from django.views import View

from apps.contents.models import ContentCategory
from apps.contents.utils import get_categories


# 1.首页 广告页
class IndexView(View):
    """首页广告"""

    def get(self, request):
        """提供首页广告界面"""
        # 查询商品频道和分类
        categories = get_categories()

        content_categories =ContentCategory.objects.all()
        contents = {
            cat.key: cat.content_set.filter(status=True).order_by('sequence')
            for cat in content_categories
        }

        # 渲染模板的上下文
        context = {
            'categories': categories,
            'contents': contents
        }
        return render(request, 'index.html', context)
