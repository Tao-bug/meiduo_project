# 导包
from django_redis import get_redis_connection


def redis_demo():
    # 实例化
    client = get_redis_connection('default')

    # 增删改查
    client.set('django_redis_key', 'itheima')
