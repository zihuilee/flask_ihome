# -*- coding: utf-8 -*-

import oss2


endpoint = 'http://oss-cn-beijing.aliyuncs.com' # 假设你的Bucket处于杭州区域

auth = oss2.Auth('LTAI7CBEOnxf3SOH', '2VIdzUiOns6z4pMWRLtCyh9A3RXKA9')
bucket = oss2.Bucket(auth, endpoint, 'flask-ihome')

# Bucket中的文件名（key）为story.txt
key = 'yihu.jpg'

# 上传
bucket.put_object(key, 'Ali Baba is a happy youth.')

# 下载
bucket.get_object(key).read()

# 删除
bucket.delete_object(key)

# 遍历Bucket里所有文件
# for object_info in oss2.ObjectIterator(bucket):
#     print(object_info.key)