# 1. 导入FastDFS客户端扩展
from fdfs_client.client import Fdfs_client
# 2. 创建FastDFS客户端实例
client = Fdfs_client('client.conf')
# 3. 调用FastDFS客户端上传文件方法
ret = client.upload_by_filename('/Users/lcf/Desktop/meizi.png')

ret = {
'Group name': 'group1',
'Remote file_id': 'group1/M00/00/00/wKhnnlxw_gmAcoWmAAEXU5wmjPs35.jpeg',
'Status': 'Upload successed.',
'Local file name': '/Users/zhangjie/Desktop/kk.jpeg',
'Uploaded size': '69.00KB',
'Storage IP': '192.168.103.158'
 }

ret = {
'Group name': 'Storage组名',
'Remote file_id': '文件索引，可用于下载',
'Status': '文件上传结果反馈',
'Local file name': '上传文件全路径',
'Uploaded size': '文件大小',
'Storage IP': 'Storage地址'
 }