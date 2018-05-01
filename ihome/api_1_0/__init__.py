#coding=utf-8
#导入蓝图
from flask import Blueprint



#创建蓝图
api = Blueprint('api',__name__)
#把拆分出去的视图导入到创建蓝图的文件
from . import register
from . import passport
from . import house
from . import order
#使用蓝图
@api.after_request
def after_request(response):
    """设置响应报文的格式为application/json"""
    #如果响应报文response的Content-Type是以text开头，则将其改为默认的json类型
    if response.headers.get('Content-Type').startswith('text'):
        response.headers['Content-Type'] = 'application/json'
    return response