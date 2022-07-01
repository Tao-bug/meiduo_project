import pickle
import base64


class CookieSecret(object):
    # 加密
    @classmethod
    def dumps(cls, data):
        # 1.将数据装换成bytes
        data_bytes = pickle.dumps(data)
        # 2.将bytes使用base64序列化加密
        base64_bytes = base64.b64encode(data_bytes)
        return base64_bytes.decode()

    # 解密
    @classmethod
    def loads(cls, data):
        # 1.将数据解密转成bytes
        base64_bytes = base64.b64decode(data)
        return pickle.loads(base64_bytes)
