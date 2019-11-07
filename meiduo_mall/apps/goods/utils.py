def get_breadcrumb(cat3):
    """
    获取面包屑导航
    :param category: 商品类别三级
    :return: 面包屑导航字典
    """
    # 2.根据三级获取二级
    cat2 = cat3.parent
    # 3.根据二级获取一级
    cat1 = cat2.parent
    # 4. 拼接前端需要的数据
    breadcrumb = {
        'cat1': {
            # 根据一级分类关联频道获取频道的url
            "url": cat1.goodschannel_set.all()[0].url,
            'name': cat1.name
        },
        "cat2": cat2,
        "cat3": cat3,
    }
    return breadcrumb
