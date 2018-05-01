#coding=utf-8
from werkzeug.routing import BaseConverter
from functools import wraps
from flask import Flask,session,jsonify,g
from ihome.utils.response_code import RET
class Regex(BaseConverter):
    def __init__(self,map,*args):
        super(Regex,self).__init__(map)
        self.regex = args[0]

#用户登陆权限验证
def login_required(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        user_id = session.get('user_id')
        if user_id is None:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
        else:
            g.user_id = user_id
            return f(*args,**kwargs)

    return wrapper