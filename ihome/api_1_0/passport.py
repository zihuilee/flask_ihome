#coding=utf-8
from  . import api
from flask import request,jsonify,current_app,session,g
from ihome.utils.response_code import RET
import re
from ihome.models import User
from ihome.utils.commons import login_required
from ihome import db
from ihome.utils.image_storage import bucket,key
from ihome import constants

# @api.route('/sessions',methods=['POST'])
# def login():
#     """
#     1.获取参数　--　get_json()
#     2.判断是否获取到参数
#     3.获取详细参数，mobile,password
#     4.判断是否缺少参数
#     5.校验手机格式
#     6.根据手机查询用户是否已注册
#     7.检查密码，使用用户模型类的check_password_hash(password)
#     8.缓存用户信息
#     9.返回结果
#     """
#     #获取参数
#     user_data = request.get_json()
#     #判断参数
#     if not user_data:
#         return jsonify(errno=RET.PARAMERR,errmsg='没有获取到参数')
#     #获取详细的参数信息,mobile,password
#     mobile = user_data['mobile']
#     password = user_data['password']
#     #校验参数是否完整
#     if not all([mobile,password]):
#         return jsonify(errno=RET.PARAMERR,errmsg='缺少参数')
#     #校验手机号码格式
#     if not re.match(r'1[3456789]\d{9}',mobile):
#         return jsonify(errno=RET.PARAMERR,errmsg='手机号格式错误')
#     #根据手机号查询数据库查看是否已注册
#     try:
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
#     #检查查询结果，确保用户已注册并且密码正确
#     if not user or not user.check_password(password):
#         return jsonify(errno=RET.DATAERR,errmsg='用户名或密码错误')
#     #缓存信息
#     session['user_id'] = user.id
#     session['mobile'] = mobile
#     session['name'] = user.name
#     #返回结果
#     return jsonify(errno=RET.OK,errmsg='OK',data={'user_id':user.id})


"""@api.route('/user',methods = ['GET'])
@login_required
def get_user_profile():
    #获取用户信息展示个人中心

    # 1.获取用户身份（user_id）
    # 2.查询数据库
    # 3.校验查询结果
    # 4.返回结果
    #获取用户id
    user_id = g.user_id
    #查询数据库
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
    #判断查询结果
    if not user:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到')
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data=user.to_dict())

"""
'''@api.route('/user/name',methods=['PUT'])
@login_required
def change_user_profile():
    #修改用户信息
    """
    1.获取用户身份，user_id
    2.获取put请求发送的json数据
    3.判断是否获取到
    4.获取要修改的参数信息name,并且判断参数的存在
    5.查询数据库．执行update({})更新数据库信息 --try,操作错误需要回滚，正确就提交
    6.缓存用户信息
    7.返回结果
    """
    #获取用户id
    user_id = g.user_id
    #获取ＰＵＴ请求的json数据
    user_data = request.get_json()
    #判断是否获取到信息
    if not user_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取要修改的参数信息
    name = user_data['name']
    #检查参数的存在
    if not name:
        return jsonify(errno=RET.PARAMERR,errmsg='缺少参数')
    #更新数据库
    try:
        User.query.filter_by(id=user_id).update({'name':name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存用户信息异常')
    #更新缓存的用户信息
    session['name'] = name
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'name':name})
'''

# '''@api.route('/user/avatar',methods=['POST'])
# @login_required
# def set_user_avatar():
# #     #设置用户头像
# #     """
# #     1.获取用户身份(user_id)
# #     2.获取前端传过来的图片文件
# #     3.读取图片文件，转类型
# #     4.把图片文件名保存到mysql数据库，update
# #     5.拼接图片绝对路径
# #     6.返回结果
# #     """
#     #获取用户ｉｄ
#     user_id = g.user_id
#     avatar = request.files.get('avatar')
#     #读取文件内容
#     file_data = avatar.read()
#     #读取图片文件，转类型
#     try:
#         bucket.put_object(avatar.filename,file_data)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.THIRDERR,errmsg='上传图片失败')
#     #把图片名称保存到mysql
#     try:
#         User.query.filter_by(id=user_id).update({'avatar_url':avatar.filename})
#         db.session.commit()
#     except Exception as e:
#         current_app.logger.error(e)
#         db.session.rollback()
#         return jsonify(errno=RET.DBERR,errmsg='保存用户头像失败')
#     #拼接图片的绝对路径
#     image_url = constants.ALIYUN_DOMIN_PREFIX + avatar.filename
#     #返回结果
#     return jsonify(errno=RET.OK,errmsg='OK',data={'avatar_url':image_url})
# #
# '''

'''@api.route('/user/auth',methods=['POST'])
@login_required
def set_user_auth():
    #设置用户实名信息
    """
    1.获取用户身份（user_id）
    2.获取json数据--get_json()
    3.判断获取的参数
    4.获取详细参数real_name,id_card
    5.判断参数是否完整
    6.保存用户实名信息到数据库
    7.返回结果
    """
    #获取用户user_id
    user_id = g.user_id
    #判断post请求的json字符串
    user_data = request.get_json()
    #判断获取结果
    if not user_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取详细的参数
    real_name = user_data.get('real_name')
    id_card = user_data.get('id_card')
    #校验参数的完整性
    if not all([real_name,id_card]):
        return jsonify(errno=RET.PARAMERR,errmsg='缺少参数')
    #保存用户信息到数据库
    try:
        User.query.filter_by(id=user_id,real_name=None,id_card=None).update({'real_name':real_name,'id_card':id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存用户实名信息失败')
        # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK',data={'real_name':real_name,'id_card':id_card})
'''

@api.route('/sessions',methods=['POST'])
def login():
    #登录
    """
    1.获取POST请求发送的数据
    2.判断获取的结果
    3.获取详细参数 mobile,password
    4.校验参数完整
    5.判断手机格式
    6.通过手机查询此用户是否注册
    7.当用户注册并且密码正确才能登录
    8.缓存用户信息
    9.返回结果
    """
    #获取post请求发送的json数据
    user_data = request.get_json()
    #判断获取的结果
    if not user_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取详细参数
    mobile = user_data.get('mobile')
    password = user_data.get('password')
    #校验参数完整
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺少')
    #检验手机号格式
    if not re.match(r'1[3456789]',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机号格式错误')
    #通过手机号去数据库查询用户
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
    #校验查询结果当用户已注册并且密码正确时才能登录
    if not user or not user.check_password(password):
        return jsonify(errno=RET.NODATA,errmsg='用户名或密码错误')
    #缓存用户信息
    session['mobile'] = mobile
    session['user_id'] =user.id
    session['name'] = user.name
    return jsonify(errno=RET.OK,errmsg='OK',data={'user_id':user.id})

@api.route('/user',methods=['GET'])
@login_required
def get_user_profile():
    #展示个人中心
    """
    1.获取用户身份(user_id)
    2.查询mysql数据库
    3.判断查询结果
    4.返回结果
    """
    #获取用户ｉｄ
    user_id = g.user_id
    #查询数据库
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库错误')
    #判断查询结果
    if not user:
        return jsonify(errno=RET.NODATA,errmsg='未查询到数据')
    return jsonify(errno=RET.OK,errmsg='OK',data=user.to_dict())

@api.route('/user/name',methods=['PUT'])
@login_required
def chang_user_profile():
    #修改用户信息
    """
    1.获取用户身份(user_id)
    2.获取参数
    3.检验参数
    4.获取参数name
    5.检验参数存在
    6.更新数据到数据库
    7.缓存用户信息
    8.返回结果
    """
    #获取用户id
    user_id = g.user_id
    #获取json数据
    user_data = request.get_json()
    #判断参数
    if not user_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取参数name
    name = user_data.get('name')
    #判断参数存在
    if not name:
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺少')
    #更新数据库
    try:
        User.query.filter_by(id=user_id).update({'name':name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存用户信息失败')
    #缓存用户信息
    session['name'] = name
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'name':name})

@api.route('/user/avatar',methods=['POST'])
@login_required
def set_user_avatar():
    #设置用户头像
    """
    1.获取用户身份(user_id)
    2.获取文件
    3.读取文件内容
    4.上传到阿里云---try
    5.保存到数据库--try --update()
    6.拼接出图片绝对路径
    7.返回结果
    """
    #获取用户id
    user_id = g.user_id
    #获取要上传的文件
    avatar = request.files.get('avatar')
    #读取文件内容
    file_data = avatar.read()
    #上传到阿里云
    try:
        bucket.put_object(avatar.filename,file_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传图片失败')
    #保存到数据库--update
    try:
        User.query.filter_by(id=user_id).update({'avatar_url':avatar.filename})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存用户头像失败')
    #拼接出图片绝对路径
    image_url= constants.ALIYUN_DOMIN_PREFIX + avatar.filename
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'avatar_url':image_url})

@api.route('/user/auth',methods=['POST'])
@login_required
def set_user_auth():
    #设置用户实名信息
    """
    0.获取用户身份(user_id)
    1.获取参数
    2.判断参数
    3.获取详细参数real_name,id_card
    4.保存到数据库
    5.返回结果
    """
    #获取用户Ｉｄ
    user_id = g.user_id
    #获取json数据
    user_data = request.get_json()
    #判断结果
    if not user_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取详细参数real_name,id_card
    real_name = user_data.get('real_name')
    id_card = user_data.get('id_card')
    #检验参数完整
    if not all([real_name,id_card]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺少')
    #保存用户信息到数据库
    try:
        user = User.query.filter_by(id=user_id).update({'real_name':real_name,'id_card':id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存用户真实信息失败')
    return jsonify(errno=RET.OK,errmsg='OK',data={'real_name':real_name,'da_card':id_card})

# @api.route('/user/auth',methods=['GET'])
# @login_required
# def show_user_auth():
#     #获取用户ｉｄ
#     user_id = g.user_id
#     #查询数据库
#     try:
#         user = User.query.filter_by(id=user_id).first()
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
#     #判断user
#     if not user:
#         return jsonify(errno=RET.NODATA,errmsg='没有查询到数据')
#     return jsonify(errno=RET.OK,errmsg='OK',data=user.auth_to_dict())



'''@api.route('/user/auth',methods=['GET'])
@login_required
def show_user_auth():
    #展示实名信息
    #获取user_id
    user_id = g.user_id
    #查询数据库
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
    #判断查询结果
    if not user:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到数据')
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data=user.auth_to_dict())
'''

@api.route('/user/auth',methods=['GET'])
@login_required
def show_user_auth():
    #获取user_id
    user_id = g.user_id
    #从数据库查询信息
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
    #判断查询结果
    if not user:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到数据')
    #返回数据---data
    return jsonify(errno=RET.OK,errmsg='OK',data=user.auth_to_dict())

# @api.route('/session',methods=['DELETE'])
# #退出
# @login_required
# def logout():
#     session.clear()
#     return jsonify(errno=RET.OK,errmsg='OK')

# @api.route('/session',methods=['GET'])
# #检查用户登录状态
# def check_user_login():
#     """
#     1.从redis中获取用户缓存的用户名信息
#     2.判断获取结果
#     3.返回结果
#     """
#     #使用session对象获取用户名
#     name = session.get('name')
#     #判断获取结果分别返回数据
#     if name:
#         return jsonify(errno=RET.OK,errmsg='OK',data={'name':name})
#     else:
#         return jsonify(errno=RET.SESSIONERR,errmsg='false')


@api.route('/session',methods=['DELETE'])
@login_required
#退出
def logout():
    csrf_token = session.get('csrf_token')
    session.clear()
    session['csrf_token']= csrf_token
    return jsonify(errno=RET.OK,errmsg='OK')

@api.route('/session',methods=['GET'])
def check_user_login():
    #检查用户登录状态
    """
    1.从redis中获取用户名
    2.判断结果是否存在
    3.返回结果
    """
    #从redis中获取用户名
    name = session.get('name')
    #判断获取结果
    if name:
        return jsonify(errno=RET.OK,errmsg='OK',data={'name':name})
    else:
        return jsonify(errno=RET.SESSIONERR,errmsg='false')










