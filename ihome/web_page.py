#coding=utf-8
#对静态文件的处理
from flask import Blueprint,make_response,current_app
from flask_wtf import csrf

#创建蓝图对象
html = Blueprint('html',__name__)

#使用蓝图对象
@html.route('/<re(".*"):file_name>')
def web_page(file_name):
    if not file_name:
        file_name = 'index.html'
    if file_name != 'favicon.ico':
        file_name = 'html/' + file_name
    #生成csrf_token
    csrf_token = csrf.generate_csrf()
    #构造响应数据  ---
    response = make_response(current_app.send_static_file(file_name))
    #把csrf_token设置到cookie
    response.set_cookie('csrf_token',csrf_token)
    return response