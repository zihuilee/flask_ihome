#coding=utf-8
#导入蓝图对象
from . import api
#导入图片验证码扩展包
from ihome.utils.captcha.captcha import captcha
#导入短信发送扩展包
from ihome.utils import sms
#导入数据库实例
from ihome import redis_store,constants
from flask import current_app,jsonify,make_response,request,session
from ihome import db
#导入自定义的状态码
from ihome.utils.response_code import RET
from ihome.models import User
import re
import random

#定义路由
@api.route('/imagecode/<image_code_id>',methods=['GET'])
def generate_image_code(image_code_id):
    #调用captcha扩展包　--　需要在上面导入才能使用
    name,text,image = captcha.generate_captcha()
    #调用redis数据库实例存储验证码，放在try中 -- 需要导入数据库实例
    try:
        redis_store.setex('ImageCode_'+image_code_id,constants.IMAGE_CODE_REDIS_EXPIRES,text)
    #没有保存成功就调用应用上下文，记录项目错误日志信息，提示错误信息
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno = RET.DBERR,errmsg= '保存图片验证码失败')
    #成功就使用响应对象，设置Content-Type为image/jpg,返回结果
    else:
        #构造响应对象用make_response
        response = make_response(image)
        #设置响应报文的Content-Type是image/jpg
        response.headers['Content-Type'] = 'image/jpg'
        #返回响应response
        return response

#定义路由---发送短信获取验证码
#基本业务流程--获取参数，校验参数，查询数据，返回结果
@api.route('/smscode/<mobile>',methods=['GET'])
def send_sms_code(mobile):
    #获取参数,除了传递的mobile外,还有图片验证码（内容数据）text，图片验证码id(模板id)--id
    image_code = request.args.get('text')
    image_code_id = request.args.get('id')
    #校验是否缺少参数,mobile,text,id
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')
    #校验mobile手机号格式
    if not re.match(r'1[3456789]\d{9}',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机格式错误')
    #获取本地存储redis中存储的真实图片验证码
    try:
        real_image_code = redis_store.get('ImageCode_'+image_code_id)
    #判断获取结果，放在try中，图片验证码是否过期
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询图片验证码失败')
    #判断是否过期
    if not real_image_code:
        return jsonify(errno=RET.NODATA,errmsg='图片验证码过期')
    #删除图片验证码,图片验证码只能操作一次
    try:
        redis_store.delete('ImageCode' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
    #比较真实的图片验证码与获取的是否一致，不区分大小写
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR,errmsg='图片验证码错误')
    #查询数据库，看手机号是否已经注册,也就是是否存在这个手机的用户
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST,errmsg='手机号已注册')
    #构造短信随机码并保存
    sms_code = '%06d'%random.randint(0,999999)
    try:
        redis_store.setex('SMSCode_' + mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存短信验证码失败')
    #调用云通讯扩展包发送短信，模板方法
    try:
        ccp = sms.CCP()
        result = ccp.send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='发送短信异常')
    #通过返回结果判断是否成功
    if 0 == result:
        return jsonify(errno=RET.OK,errmsg='发送成功')
    else:
        return jsonify(errno=RET.THIRDERR,errmsg='发送失败')

#定义路由--用户注册
@api.route('/users',methods=['POST'])
def register():
    """
    1.获取参数--request.get_json()
    2.判断获取结果
    3.获取详细的参数，mobile,sms_code,password
    4.校验是否缺少参数
    5.检查手机号格式
    6.查询数据库判断用户是否已注册--放在try中，查到说明已注册
    7.获取本地存储的真实短信验证码，放在try中
    8.判断查询redis的结果,没有就说明验证码过期
    9.比较获取的短信验证码和本地存储的是否一致
    10.正确就删除短信验证码
    11.保存用户信息
    12.缓存用户信息
    13.返回结果
    """
    user_data = request.get_json()
    if not user_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    mobile = user_data['mobile']
    sms_code = user_data['sms_code']
    password = user_data['password']
    if not all([mobile,sms_code,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='缺少参数')
    if not re.match(r'1[3456789]\d{9}',mobile):
        return jsonify(errno=RET.PARAMERR,errmgs='手机格式错误')
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库错误')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST,errmsg='用户已注册')
    try:
        real_sms_code = redis_store.get('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
    if not real_sms_code:
        return jsonify(errno=RET.NODATA,errmsg='用户验证码过期')
    #比较真实sms_code和获取到的sms_code
    if real_sms_code != str(sms_code):
        return jsonify(errno=RET.DATAERR,errmsg='验证码错误')
    #删除短信验证码
    try:
        redis_store.delete('SMSCode_'+mobile)
    except Exception as e:
        current_app.logger.error(e)
    #保存用户信息
    user = User(mobile=mobile,name=mobile)
    user.password = password
    #提交数据到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        #提交数据发生异常，需要回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存用户信息失败')
    #缓存用户信息
    session['user_id']= user.id
    session['mobile']= mobile
    session['name'] = mobile
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data=user.to_dict())

