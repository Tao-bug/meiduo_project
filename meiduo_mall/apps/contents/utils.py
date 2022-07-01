from collections import OrderedDict
from apps.goods.models import GoodsChannel


# 封装首页商品频道分类
def get_categories():
    """
    提供商品频道和分类
    :return 菜单字典
    """
    # 查询商品频道和分类
    categories = OrderedDict()
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    for channel in channels:
        group_id = channel.group_id  # 当前组

        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}

        cat1 = channel.category  # 当前频道的类别
        cat1.url = channel.url
        # 追加当前频道
        categories[group_id]['channels'].append(cat1)
        # categories[group_id]['channels'].append({
        #     'id': cat1.id,
        #     'name': cat1.name,
        #     'url': channel.url
        # })
        # 构建当前类别的子类别
        for cat2 in cat1.subs.all():
            cat2.sub_cats = list(cat2.subs.all())
            categories[group_id]['sub_cats'].append(cat2)

    return categories
