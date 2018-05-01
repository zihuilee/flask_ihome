#coding=utf-8
from . import api
from ihome import redis_store
from flask import current_app,jsonify,json,request,session,g
from ihome.models import Area,House,Facility,HouseImage
from ihome.utils.response_code import RET
from ihome import constants
from ihome.utils.commons import login_required
from ihome import db
from ihome.constants import ALIYUN_DOMIN_PREFIX
from ihome.utils.image_storage import bucket
from ihome.models import User,Order
import datetime



'''@api.route('/areas',methods=['GET'])
def get_areas_info():
    #获取城区信息
    """
    1.尝试从redis中获取城区信息
    2．判断查询结果是否有数据
    3.如果有数据就留下访问记录，在Log日志中
    4.没有数据就要从Mysql数据库查询数据
    5.判断查询结果
    6.定义容器，存储查询结果
    7.遍历查询的结果，使用 to_dict方法，把具体的对象转成键值形式的数据
    8.转成json数据
    9.存储到redis中
    10.返回结果
    """
    #尝试从redis获取城区信息 --try
    try:
        areas = redis_store.get('area_info')
    except Exception as e:
        current_app.logger.error(e)
        #如果查询发现异常，把查询结果设置成None
        areas = None
    #判断结果存在
    if areas:
        #留下访问redis数据库的记录
        current_app.logger.info('hit redis areas info')
        return '{"errno":0,"errmsg":"OK","data":%s}'% areas
    #没有就查询mysql数据库
    try:
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
    #判断查询结果
    if not areas:
        return jsonify(errno=RET.NODATA,errmsg='无城区信息')
    #定义容器，存储查询结果
    area_list = []
    #遍历查询结果，使用to_dict()方法把具体对象转成具有键值形式的数据
    for area in areas:
        area_list.append(area.to_dict())
    #把城区信息转成json
    area_json = json.dumps(area_list)
    #存储到redis中
    try:
        redis_store.setex('area_info',constants.AREA_INFO_REDIS_EXPIRES,area_json)
    except Exception as e:
        current_app.logger.error(e)
    #返回json数据，构造响应结果
    resp = '{"errno":0,"errmsg":"OK","data":%s}'%area_json
    return resp
'''
'''
@api.route('/houses',methods=['POST'])
@login_required
def save_house_info():
    #发布新房源
    """
     1.获取用户身份(user_id)
     2.获取前端post请求发送的json数据
     3.判断获取结果
     4.获取详细参数
     5.检验参数完整
     6.把价格和押金单位由元转成分
     7.构造模型类对象，准备保存数据
     8.判断配套设施的存在
     9.对配套设施进行过滤，只保存数据库定义的配套设施信息
     10.保存到数据库
     11.返回结果，---data=house.id
    """
    #确认用户身份(user_id)
    user_id = g.user_id
    #获取json数据
    house_data = request.get_json()
    #判断获取结果
    if not house_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取详细参数（房屋基本信息）
    title = house_data.get('title')  # 房屋标题
    area_id = house_data.get('area_id')  # 房屋城区
    address = house_data.get('address')  # 详细地址
    price = house_data.get('price')  # 房屋价格
    room_count = house_data.get('room_count')  # 房屋数目
    acreage = house_data.get('acreage')  # 房屋面积
    unit = house_data.get('unit')  # 房屋户型
    capacity = house_data.get('capacity')  # 人数上限
    beds = house_data.get('beds')  # 卧床配置
    deposit = house_data.get('deposit')  # 押金
    min_days = house_data.get('min_days')  # 最小入住天数
    max_days = house_data.get('max_days')  # 最大入住天数
    #检验参数完整
    if not all([title, area_id, address, price, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    #把价格和押金的单位由元转成分
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='价格数据错误')
    #构造模型类对象，准备保存信息
    house = House()
    house.user_id = user_id
    house.area_id = area_id
    house.title = title
    house.address = address
    house.price = price
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days
    #尝试获取房屋配套设施参数
    facility = house_data.get('facility')
    #判断配套设施存在
    if facility:
        #查询数据库，对房屋配套设施进行过滤
        #保存查询结果
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility)).all()
            house.facilities = facilities
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询配套设施异常')
    #保存房屋信息mysql数据库中
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存房屋信息失败')
    #返回结果---data---house.id
    return jsonify(errno=RET.OK,errmsg='OK',data={'house_id':house.id})
'''

'''@api.route('/houses/<int:house_id>/images',methods=['POST'])
@login_required
def save_house_image(house_id):
    #上传房屋图片
    """
    1.获取图片文件
    2.判断获取结果
    3.根据house_id查询数据库,House模型类
    4.判断查询结果
    5.读取图片数据
    6.调用第三方接口，上传图片
    7.保存图片名称
    8.构造HouseImage模型类，准备存储房屋图片数据
    9.判断房屋默认图片是否设置，如果未设置就把当前图片设为默认图片
    10保存房屋对象数据
    11.提交数据到数据库中
    12.拼接出图片绝对路径
    13.返回结果
    """
    #获取图片文件
    house_image = request.files.get('house_image')
    #判断获取结果
    if not house_image:
        return jsonify(errno=RET.PARAMERR,errmsg='未上传房屋图片')
    #从数据库查询房屋，确认房屋的存在
    try:
        house = House.query.filter_by(id=house_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋数据失败')
    #判断查询结果
    if not house:
        return jsonify(errno=RET.NODATA,errmsg='房屋不存在')
    #读取图片数据
    file_data = house_image.read()
    image_name = house_image.filename
    #调用阿里云上传图片
    try:
       bucket.put_object(image_name,file_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传房屋图片失败')
    #保存房屋数据，构造模型类对象
    house_image = HouseImage()
    house_image.house_id = house_id
    house_image.url = image_name
    #添加数据到数据库会话对象
    db.session.add(house_image)
    #判断房屋主图片是否设置，未设置就默认为当前图片
    if not house.index_image_url:
        house.index_image_url = image_name
        db.session.add(house)
    #提交数据到mysql数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存房屋图片数据失败')
    #拼接图片的绝对路径
    image_url = constants.ALIYUN_DOMIN_PREFIX + image_name
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'url':image_url})
'''


# 2
'''
@api.route('/areas',methods=['GET'])
def get_areas_info():
    #获取城区信息
    """
     1.尝试从redis中获取城区信息
     2.判断获取结果,有就在redis中留下访问城区信息的记录，没有获取到就设置成None
     3.从数据库查询信息
     4.定义临时容器，存储查询结果
     5.遍历查询结果，使用to_dict方法把具体的对象转成具有键值对形式的数据
     6.转成json数据
     7.添加到redis中
     8.构造响应数据，响应结果
    """
    #尝试从redis中获取城区信息
    try:
        areas = redis_store.get('area_info')
    #判断获取结果，有就在redis中留下访问记录,没有就设置成None
    except Exception as e:
        current_app.logger.error(e)
        areas = None
    if areas:
        current_app.logger.info('hit redis area info')
        return '{"errno":0,"errmsg":"OK","data":%s}'%areas
    #查询mysql数据库
    try:
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库出错')
    #判断查询结果
    if not areas:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到数据')
    #定义容器，存储查询结果
    areas_list = []
    #遍历查询结果，使用to_dict()方法
    for area in areas:
        areas_list.append(area.to_dict())
    #转成json
    areas_json = json.dumps(areas_list)
    #存储到redis中
    try:
        redis_store.setex('area_info',constants.AREA_INFO_REDIS_EXPIRES,areas_json)
    except Exception as e:
        current_app.logger.error(e)
    #响应结果
    resp = '{"errno":0,"errmsg":"OK","data":%s}'%areas_json
    return resp


@api.route('/houses',methods=['POST'])
@login_required
def save_house_info():
    #发布新房源
    """
    1.确认用户身份(user_id)
    2.获取json数据
    3.判断获取结果
    4.获取详细参数
    5.检验参数完整性
    6.把价格和押金由元转成分
    7.构建模型类，准备储存信息
    8.尝试获取配套设施
    9.判断配套设施的存在
    10.查询数据库，过滤出数据库设定的数据并添加到模型类对象中
    11.添加到数据库，提交数据
    12.返回结果
    """
    #获取用户id
    user_id = g.user_id
    #获取json数据
    house_data = request.get_json()
    #判断获取结果
    if not house_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取详细参数 -- 房屋基本信息
    title = house_data.get('title')  # 房屋标题
    area_id = house_data.get('area_id')  # 房屋城区
    address = house_data.get('address')  # 详细地址
    price = house_data.get('price')  # 房屋价格
    room_count = house_data.get('room_count')  # 房屋数目
    acreage = house_data.get('acreage')  # 房屋面积
    unit = house_data.get('unit')  # 房屋户型
    capacity = house_data.get('capacity')  # 人数上限
    beds = house_data.get('beds')  # 卧床配置
    deposit = house_data.get('deposit')  # 押金
    min_days = house_data.get('min_days')  # 最小入住天数
    max_days = house_data.get('max_days')  # 最大入住天数
    #检验参数
    if not all([title, area_id, address, price, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    #把价格和押金由元转换成分
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='价格数据错误')
    #构建模型类，准备存储数据
    house = House()
    house.user_id = user_id
    house.area_id = area_id
    house.title = title
    house.address = address
    house.price = price
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days
    #尝试获取配套设施
    facility = redis_store.get('facility')
    #判断配套设施存在
    if facility:
        #从数据库查询数据，过滤得到数据库设置好的
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility)).all()
            house.facilities = facilities
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询配套设施异常')
    #保存数据到数据库
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存房屋信息失败')
    #返回结果
    return jsonify(errno=RET.OK,ermsg='OK',data={'house_id':house.id})


@api.route('/houses/<int:house_id>/images',methods=['POST'])
@login_required
def save_home_image(house_id):
    #上传房屋图片
    """
    1.获取要上传的文件
    2.判断获取结果
    3.通过house_id确定房屋是否存在
    4.判断获取结果
    5.读取文件数据，获取文件名称---image_name = house_image.filename
    6.调用阿里云接口上传图片
    7.构建模型类对象HouseImage，house_id和url
    8.保存数据到session会话中
    9.判断是否存在主图片，没有的话就设置当前图片为默认主图片
    10.保存数据到数据库
    11.拼接出图片完整的绝对路径
    12.返回结果 data --- {'url':image_url}
    """
    #获取要上传的文件
    house_image = request.files.get('house_image')
    #判断获取结果
    if not house_image:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #根据house_id查询house是否存在
    try:
        house = House.query.filter_by(id=house_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库错误')
    #判断查询结果＇
    if not house:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到数据')
    #读取文件数据
    file_data = house_image.read()
    image_name = house_image.filename
    #调用阿里云上传图片
    try:
        bucket.put_object(image_name,file_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传房屋图片失败')
    #构建模型类HouseImage
    house_image = HouseImage()
    house_image.house_id = house_id
    house_image.url = image_name
    #添加数据到数据库会话对象
    db.session.add(house_image)
    #判断是否有默认主图片，如果没有就设置当前图片为默认主图片
    if not house.index_image_url:
        house.index_image_url = image_name
        db.session.add(house)
    #添加到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存到数据库失败')
    #拼接出图片的绝对路径
    image_url = constants.ALIYUN_DOMIN_PREFIX + image_name
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'url':image_url})

'''
@api.route('/areas',methods=['GET'])
def get_area_info():
    #尝试从redis获取areas
    try:
        areas = redis_store.get('area_info')
    except Exception as e:
        current_app.logger.error(e)
        areas = None
    #有就在redis中记录访问记录，没有就把areas设置成None
    if areas:
        current_app.logger.info('hit redis area info')
        return '{"errno":0,"errmsg":"OK","data":%s}'% areas
    #查询数据库
    try:
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询城区信息错误')
    #判断查询结果
    if not areas:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到数据')
    #定义容器,存储查询结果
    area_list = []
    #遍历查询结果,使用to_dict()转成键值形式的数据
    for area in areas:
        area_list.append(area.to_dict())
    #转成json
    area_json = json.dumps(area_list)
    #保存到redis
    try:
        redis_store.setex('area_info',constants.AREA_INFO_REDIS_EXPIRES,area_json)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存城区信息失败')
    #返回结果
    return '{"errno":0,"errmsg":"OK","data":%s}'% area_json


@api.route('/houses',methods=['POST'])
@login_required
def save_house_info():
    #发布新房源
    #获取user_id
    user_id = g.user_id
    #获取post请求的json数据
    house_data = request.get_json()
    #判断获取结果
    if not house_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取详细参数 -- 房屋基本信息
    title = house_data.get('title')  # 房屋标题
    area_id = house_data.get('area_id')  # 房屋城区
    address = house_data.get('address')  # 详细地址
    price = house_data.get('price')  # 房屋价格
    room_count = house_data.get('room_count')  # 房屋数目
    acreage = house_data.get('acreage')  # 房屋面积
    unit = house_data.get('unit')  # 房屋户型
    capacity = house_data.get('capacity')  # 人数上限
    beds = house_data.get('beds')  # 卧床配置
    deposit = house_data.get('deposit')  # 押金
    min_days = house_data.get('min_days')  # 最小入住天数
    max_days = house_data.get('max_days')  # 最大入住天数
    #检验详细参数
    if not all([title, area_id, address, price, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    #把价格和押金的单位由元转成分
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='价格数据错误')
    #构建模型类，准备存储房屋信息
    house = House()
    house.user_id = user_id
    house.area_id = area_id
    house.title = title
    house.address = address
    house.price = price
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days
    #尝试获取配套设施参数
    facility = house_data.get('facility')
    #判断配套设施存在
    if facility:
    #查询数据库,过滤出数据库设置的配套设施并且添加到模型类
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility)).all()
            house.facilities = facilities
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询配套设施异常')
    #保存数据到数据库
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,ermsg='保存房屋信息失败')
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'house_id':house.id})


@api.route('/houses/<int:house_id>/images',methods=['POST'])
@login_required
def save_house_image(house_id):
    #上传房屋图片
    #获取要上传的文件
    house_image = request.files.get('house_image')
    #判断获取结果
    if not house_image:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #根据house_id查询house是否存在
    try:
        house = House.query.filter_by(id=house_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,ermsg='查询房屋信息失败')
    #判断查询结果
    if not house:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到数据')
    #读取文件数据
    file_data = house_image.read()
    #定义图片名称
    image_name = house_image.filename
    #调用阿里云接口，尝试上传图片
    try:
        bucket.put_object(image_name,file_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传房屋图片失败')
    #构建模型类,准备存储数据
    house_image = HouseImage()
    house_image.house_id = house_id
    house_image.url = image_name
    #添加到数据库会话对象
    db.session.add(house_image)
    #如果没有默认主图片，就设置当前图片为默认的主图片
    if not house.index_image_url:
        house.index_image_url = image_name
        db.session.add(house)
    #保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存房屋图片数据失败')
    #拼接图片绝对路径
    image_url = constants.ALIYUN_DOMIN_PREFIX + image_name
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'url':image_url})

#我的房源
'''@api.route('/user/houses',methods=['GET'])
@login_required
def get_user_houses():
    #展示我的房源页面
    """
    1.获取用户身份(user_id)
    2.根据user_id查询数据库确定用户的存在（实现一对多的查询）
    3.定义容器
    4.遍历查询结果，调用模型类中的方法
    5.返回结果
    """
    #获取user_id
    user_id = g.user_id
    #查询数据库
    try:
        # user = User.query.filter_by(id=user_id).first()
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋信息失败')
    #判断查询结果
    if not houses:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到房屋数据')
    #定义一个容器
    house_list = []
    #遍历查询结果,调用模型类的to_basic_dict()
    for house in houses:
        house_list.append(house.to_basic_dict())
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={"houses":house_list})
'''

'''@api.route('/houses/index',methods=['GET'])
#首页幻灯片轮播
def get_houses_index():
    """
    缓存--数据库（磁盘）--缓存
    1.尝试从缓存中读取数据　--　try
    2.有就留下访问redis的记录，返回结果
    3.没有就查询数据库
    4.默认采用成交量最高的5条
    6.判断查询结果
    7.定义容器存储查询结果
    8.遍历查询结果，判断是否有主图片，没有的话不填加
    9.调用模型类方法中的to_basic_dict()
    10.转成json数据
    11.缓存到redis
    12.返回结果
    """
    #尝试从reids获取数据
    try:
        ret = redis_store.get('home_page_data')
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    #判断查询结果
    if ret:
        current_app.logger.info('hit redis house index info')
        return '{"errno":0,"errmsg":"OK","data":%s}'%ret
    #如未获取从数据库查询数据
    try:
        houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋数据失败')
    #判断获取结果
    if not houses:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到数据')
    #定义容器存储查询结果
    house_list = []
    #遍历查询结果,判断是否有主图片,没有就跳过，调用模型类的to_basic_dict()
    for house in houses:
        if not house.index_image_url:
            continue
        house_list.append(house.to_basic_dict())
    #转成json
    house_json = json.dumps(house_list)
    #缓存到redis
    try:
        redis_store.setex('home_page_data',constants.HOME_PAGE_DATA_REDIS_EXPIRES,house_json)
    except Exception as e:
        current_app.logger.error(e)
    #返回结果
    resp = '{"errno":0,"errmsg":"OK","data":%s}'% house_json
    return resp
'''
'''
@api.route('/houses/<int:house_id>',methods=['GET'])
#房屋详情页
def get_house_detail(house_id):
    """
    缓存---磁盘（mysql）--缓存
    1.确认访问接口的用户身份--从session对象中获取，没有就给默认值-1
    2.判断house_id参数的存在
    3.尝试读取redis缓存来获取房屋详情数据
    4.判断获取结果
    5.如果能获取到就在redis中留下访问记录
    6.没有获取到就查询mysql数据库
    7.判断查询结果
    8.调用模型类的house.to_full_dict方法
    9.转成json数据
    10.缓存到redis
    11.构造响应数据返回结果
    """
    #确认访问接口的用户身份
    user_id = session.get('user_id',-1)
    #判断house_id的存在
    if not house_id:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #尝试从redis中获取房屋详情数据
    try:
        ret = redis_store.get('house_info_%s' % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    #判断获取结果
    if ret:
        #在redis中留下访问记录,返回结果
        current_app.logger.info('hit redis house detail info')
        return '{"errno":0,"errmsg":"OK","data":{"user_id":%s,"house":%s}}'% (user_id,ret)
    #没有获取到就查询mysql数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋数据失败')
    #判断查询结果
    if not house:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到房屋数据')
    #调用模型类的to_full_dict()方法，因为涉及到了查询数据库，所以放在try中
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋详情数据失败')
    #转成json
    house_json = json.dumps(house_data)
    #把房屋详情存到redis中
    try:
        redis_store.setex('house_info_%s'%house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND,house_json)
    except Exception as e:
        current_app.logger.error(e)
    #构造响应报文，返回结果
    resp = '{"errno":0,"errmsg":"OK","data":{"user_id":%s,"house":%s}}'%(user_id,house_json)
    return resp
'''
@api.route('/user/houses',methods=['GET'])
@login_required
def get_user_houses():
    #我的房源信息
    """1.获取用户身份(user_id)
       2.查询mysql数据库，确认用户的存在，实现一对多的查询
       3.定义容器
       4.如果房屋数据存在，遍历查询结果，添加到列表中
       5.返回结果
    """
    #获取user_id
    user_id = g.user_id
    #从数据库查询数据,先查user,再一对多查houses
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋数据失败')
    #首先定义容器
    house_list = []
    #判断房屋存在
    if houses:
        #遍历查询结果,使用house.to_basic_dict()
        for house in houses:
            house_list.append(house.to_basic_dict())

    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'houses':house_list})


@api.route('/houses/index',methods=['GET'])
def get_houses_index():
    #主页图片轮播
    """
    缓存--磁盘--缓存
    1.尝试从redis中获取房屋信息
    2.判断获取结果
    3.有就在redis中留下访问记录
    4.没有就查询数据库　--　查询成交量最高的5套
    5.判断查询结果
    6.定义容器，存储查询结果
    7.遍历查询结果,判断是否有主图片，没有就跳过
    8.转成json
    9.缓存到redis中
    10.返回结果
    """
    #尝试从redis中获取房屋信息 -- try
    try:
        ret = redis_store.get('home_page_data')
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    #判断获取结果
    if ret:
        current_app.logger.info('hit redis house index info')
        return '{"errno":0,"errmsg":"OK","data":%s}'% ret
    #没有就查询mysql
    try:
        houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋信息错误')
    #判断查询结果
    if not houses:
        return jsonify(errno=RET.NODATA,errmsg='没有查询倒数据')
    #定义容器存储查询结果
    house_list = []
    #遍历查询结果,判断没有主图片就不添加跳过
    for house in houses:
        if not house.index_image_url:
            continue
        house_list.append(house.to_basic_dict())
    #转成json
    house_json = json.dumps(house_list)
    #存储到redis中
    try:
        redis_store.setex('home_page_data',constants.HOME_PAGE_DATA_REDIS_EXPIRES,house_json)
    except Exception as e:
        current_app.logger.error(e)
    #返回结果
    resp = '{"errno":0,"errmsg":"OK","data":%s}'% house_json
    return resp

@api.route('/houses/<int:house_id>',methods=['GET'])
def get_houses_detail(house_id):
    #房屋详情页
    """
    缓存--磁盘--缓存
    1.判断用户身份(user_id)--session中读取
    2.判断house_id是否存在
    3.尝试从redis中读取房屋数据
    4.判断获取结果
    5.有就在redis中留下记录
    6.没有就查询数据库
    7.判断查询结果
    8.调用模型类的to_full_dict()
    9转成json
    10存储到redis
    11返回结果
    """
    #判断用户身份（user_id），没有给默认值-1
    user_id = session.get('user_id',-1)
    #判断house_id是否存在
    if not house_id:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #尝试从redis中获取房屋数据
    try:
        ret = redis_store.get('house_info_%s'%house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    #判断查询结果
    if ret:
        current_app.logger.info('hit redis house detail info')
        return '{"errno":0,"errmsg":"OK","data":{"user_id":%s,"house":%s}}'%(user_id,ret)
    #没有就查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋数据失败')
    #判断查询结果
    if not house:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到数据')
    #调用模型类的to_full_dict()
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋详情数据失败')
    #转成json
    house_json = json.dumps(house_data)
    #存储到redis中
    try:
        redis_store.setex('house_info_%s'%house_id,constants.HOME_PAGE_DATA_REDIS_EXPIRES,house_json)
    except Exception as e:
        current_app.logger.error(e)
    #返回结果
    resp = '{"errno":0,"errmsg":"OK","data":{"user_id":%s,"house":%s}}'%(user_id,house_json)
    return resp

'''
@api.route('/houses',methods=['GET'])
def get_house_list():
    #获取房屋列表信息
    """
    缓存--磁盘--缓存
    业务流程:获取参数,校验参数,查询数据,返回结果
    1.获取参数---参数可以不传，可以设置成空值或默认值,具体参数：区域id，用户选择开始时间，结束时间,排序关键字，页数
    2.校验参数,对日期参数进行判断，并且需要格式化输出，需要对页数进行格式化--转成整型int
    3.尝试从redis中读取房屋信息，以哈希的对象存储
    4.需要构造键　--　houses_%s_%s_%s_%s,还有page
    5.如果从redis中读取到了数据,就留下访问redis的记录，直接返回读取的信息
    6.没有就需要查询数据库
    7.定义容器，存储过滤的条件
    8.依次处理参数信息，首先处理区域id
    9.处理时间，获取不冲突的房屋信息，需要分情况，不一定选择了几个参数
    10.判断排序条件，按排序条件进行排序，分情况讨论
    11.对排序结果进行分页，获取每页数据和分页之后的总页数
    12.定义容器，遍历分页厚的房屋数据，调用模型类的方法．
    13.构造响应数据
    14.转成json准备存储到redis
    15.判断用户选择的页数必须小于等于分页的总页数
    16.使用redis事务存储
    17.返回结果
    """
    #一.获取参数,aid,sd,ed,sort,page,排序条件和页数需要设置默认值
    area_id = request.args.get('aid')#区域id
    start_date_str = request.args.get('sd')#用户选择的开始时间
    end_date_str = request.args.get('ed')#用户选择的结束时间
    sort_key = request.args.get('sk','new')#排序关键字
    page = request.args.get('p',1)#页数
    #二.校验参数
    #1.检查日期参数,对其进行格式化datetime
    try:
        #定义变量存储格式化后的日期
        start_date,end_date = None,None
        #如果用户只选择了开始日期
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str,'%Y-%m-%d')
        #用户只选择了结束日期
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str,'%Y-%m-%d')
        #如果用户既选择了开始日期又选择了结束日期,判断用户选择的时间必须至少是一天
        if start_date_str and end_date_str:
            #断言用户选择的日期至少是一天
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='日期格式错误')
    #2.把页数类型转成int
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='页数格式错误')
    #3.查询数据
    #先尝试从redis中获取数据--hash类型的数据
    try:
        #构造redis_key
        redis_key = 'houses_%s_%s_%s_%s'%(area_id,start_date,end_date,sort_key)
        #获取数据
        ret = redis_store.hget(redis_key,page)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    #判断获取结果,有就在redis留下访问记录，直接返回结果
    if ret:
        current_app.logger.info('hit redis houses list info')
        return ret
    try:
        #没有就查询mysql数据库
        #首先定义一个容器，存储过滤条件
        filter_params = []
        #城区参数存在,如果有区域信息就添加到列表中
        if area_id:
            filter_params.append(House.area_id == area_id)
        #查询日期不冲突的房屋 --- (查询冲突房屋取反即可)，分情况
        if start_date and end_date:
            #先查询日期冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date<=end_date,Order.end_date>=start_date).all()
        if start_date:
            #先查询日期冲突的订单
            conflict_orders = Order.query.filter(Order.end_date>=start_date).all()
        if end_date:
            #先查询日期冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date<=end_date).all()
        #遍历有冲突的订单，获取有冲突的房屋,使用列表推导式
        conflict_house_id = [order.house_id for order in conflict_orders]
        if conflict_house_id:
            filter_params.append(House.id.notin_(conflict_house_id))
        #判断排序条件,默认按发布顺序排
        #按成交次数从高到低排，---　知识点　*filter_params拆包，意思是满足其中的所有条件
        if 'booking' == sort_key:
            houses = House.query.filter(*filter_params).order_by(House.order_count.desc())
        #按照价格从低到高排序
        if 'price-inc' == sort_key:
            houses = House.query.filter(*filter_params).order_by(House.price.asc())
        #按照价格从高到低排序
        if 'price-des' == sort_key:
            houses = House.query.filter(*filter_params).order_by(House.price.desc())
        #默认按照房屋发布时间
        else:
            houses = House.query.filter(*filter_params).order_by(House.create_time.desc())

        #分页*---sqlalchemy的分页
        house_page = houses.paginate(page,constants.HOUSE_LIST_PAGE_CAPACITY,False)
        #获取分页后的房屋数据
        house_list = house_page.items
        #获取分页后的总页数
        total_page = house_page.pages
        #定义容器，遍历分页后的房屋数据,调用模型类的方法
        houses_dict_list = []
        for house in house_list:
            houses_dict_list.append(house.to_basic_dict())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋列表信息失败')
    #构造响应数据
    resp = {"errno":0,"errmsg":"OK","data":{"houses":houses_dict_list,
                                            "total_page":total_page,
                                            "current_page":page}}
    #转成json，准备存储到redis
    resp_json = json.dumps(resp)
    #判断用户请求的页数必须小于等于总页数
    if page <= total_page:
        redis_key =  'houses_%s_%s_%s_%s' % (area_id,start_date_str,end_date_str,sort_key)
        pip = redis_store.pipeline()
    #使用redis的事务
        try:
            #开启事务
            pip.multi()
            #保存数据
            pip.hset(redis_key,page,resp_json)
            #设置过期时间
            pip.expire(redis_key,constants.HOUSE_LIST_REDIS_EXPIRES)
            #执行事务
            pip.execute()
        except Exception as e:
            current_app.logger.error(e)
    #四.返回结果
    return resp_json
'''
'''
@api.route('/houses',methods=['GET'])
def get_houses_list():
    #获取房屋列表页
    """
    1.获取参数,有的需要给默认值,区域id,用户选择的开始时间,结束时间，排序条件，页数
    2.检验参数，需要格式化输出日期参数并且把页数参数转成int
    3.先尝试从redis获取房屋信息，获取的是哈希类型的数据
    4.有就在redis中留下访问记录，直接返回结果
    5.没有就查询数据库
    6.定义容器来存储过滤条件
    7.判断城区参数，存在就加城区对象到容器中
    8.查询出日期不冲突的房屋，先查询出和日期冲突的订单，再查询出冲突的房屋，取反添加到容器中
    9.根据排序条件排序
    10.分页，获取分页数据，总页数
    11.定义容器，遍历分页数据，调用模型类的方法添加到容器中
    12.构造响应数据
    13.转成json，准备存储到redis
    14.当用户请求的页数不大于总页数才能继续执行
    15.使用redis的事务存储信息
    16.返回结果
    """
    #获取参数
    area_id = request.args.get('aid')
    start_date_str = request.args.get('sd')
    end_date_str = request.args.get('ed')
    sort_key = request.args.get('sk','new')
    page = request.args.get('p',1)
    #校验参数　--　日期参数格式化,页数转int
    try:
        #定义存储格式化后日期参数的变量
        start_date,end_date = None,None
        #如果用户选择了开始日期
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str,'%Y-%m-%d')
        #如果用户选择了结束日期
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str,'%Y-%m-%d')
        #如果用户既选择了开始日期又选择了结束日期，断言用户选择时间至少是一天
        if start_date_str and end_date_str:
            assert end_date >= start_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='日期格式错误')
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='页数格式错误')
    #先尝试从redis中获取房屋数据，查询异常就设置ret=None
    try:
        redis_key = 'houses_%s_%s_%s_%s'%(area_id,start_date,end_date,sort_key)
        ret = redis_store.hget(redis_key,page)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    #判断获取结果,在redis中留下访问记录,直接返回结果
    if ret:
        current_app.logger.info('hit redis house list info')
        return ret
    #没有就需要查询mysql数据库
    try:
        #定义一个容器来存储过滤条件
        params_filter = []
        #如果有城区信息参数就把这个对象加入到容器
        if area_id:
            params_filter.append(House.area_id == area_id)
        #需要查询出与日期不冲突的房屋，首先查询与日期冲突的订单，再遍历订单查询与日期冲突的
        #房屋，取反加到容器中
        #如果用户既选择了开始日期又选择了结束日期
        if start_date and end_date:
            #先查询与日期冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date<=end_date,Order.end_date>=start_date).all()
        if start_date:
            conflict_orders = Order.query.filter(Order.end_date>=start_date).all()
        if end_date:
            conflict_orders = Order.query.filter(Order.begin_date<=end_date).all()
        #使用列表推导式获取冲突的房屋
        conflict_houses_id = [order.house_id for order in conflict_orders]
        #判断存在取反加入到容器中
        if conflict_houses_id:
            params_filter.append(House.id.notin_(conflict_houses_id))
        #按照排序条件进行排序
        #按照成交量从高到低排序
        if 'booking' == sort_key:
            houses = House.query.filter(*params_filter).order_by(House.order_count.desc())
        #按照价格从低到高排序
        if 'price-inc' == sort_key:
            houses = House.query.filter(*params_filter).order_by(House.price.asc())
        #按照价格从高到低排序
        if 'price-des' == sort_key:
            houses = House.query.filter(*params_filter).order_by(House.price.desc())
        #没有排序条件就默认按发布时间最新的排
        else:
            houses = House.query.filter(*params_filter).order_by(House.create_time.desc())
        #分页
        houses_page = houses.paginate(page,constants.HOUSE_LIST_PAGE_CAPACITY,False)
        #获取分页数据
        house_list = houses_page.items
        #获取分页后的总页数
        total_page = houses_page.pages
        #定义容器，遍历分页后的房屋数据，，调用模型类中的方法
        house_dict_list = []
        for house in house_list:
            house_dict_list.append(house.to_basic_dict())

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='查询房屋列表信息错误')
    #构造响应数据
    resp = {"errno":0,"errmsg":"OK","data":{"houses":house_dict_list,
                                            "total_page":total_page,
                                            "current_page":page
                                            }}
    #转成json,准备存入redis
    resp_json = json.dumps(resp)
    #当用户请求的页数不大于分页后的总页数时可以存入redis，使用redis中的事务
    if page <= total_page:
        redis_key = 'houses_%s_%s_%s_%s'% (area_id,start_date,end_date,sort_key)
        pip = redis_store.pipeline()
        try:
            #开始事务
            pip.multi()
            #存储数据
            pip.hset(redis_key,page,resp_json)
            #设置过期时间
            pip.expire(redis_key,constants.HOUSE_LIST_REDIS_EXPIRES)
            #执行事务
            pip.execute()
        except Exception as e:
            current_app.logger.error(e)
    #返回结果
    return resp_json
'''

@api.route('/houses',methods=['GET'])
def get_house_list():
    """获取房屋列表页"""
    #获取参数,有的需要给默认值,区域id,用户选择的开始时间，结束时间，排序条件，页数
    area_id = request.args.get('aid')
    start_date_str = request.args.get('sd')
    end_date_str = request.args.get('ed')
    sort_key = request.args.get('sk','new')
    page = request.args.get('p',1)
    #校验参数，把日期参数格式化，页数转int
    try:
        #定义两个变量来存储格式化之后的日期参数
        start_date,end_date = None,None
        #当用户只选择了开始时间
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str,'%Y-%m-%d')
        #当用户只选择了结束时间
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str,'%Y-%m-%d')
        #如果都选了，断言用户选择的时常至少为一天
        if start_date_str and end_date_str:
           assert end_date >= start_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='日期格式错误')
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='页数格式错误')
    #尝试先从redis获取房屋列表信息
    try:
        #构造键值
        redis_key = 'houses_%s_%s_%s_%s'% (area_id,start_date,end_date,sort_key)
        ret = redis_store.hget(redis_key,page)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    #有就在redis留下访问记录，直接返回结果
    if ret:
        current_app.logger.info('hit redis house list info')
        return ret
    #没有就查询数据库
    try:
    #定义一个容器来存储过滤条件
        params_filter = []
    #如果有城区信息就把这个对象加入到容器
        if area_id:
            params_filter.append(House.area_id == area_id)
    #查询出和日期不冲突的房屋，先查询出与日期冲突的订单，在查询出与日期冲突的房屋，取反加入到容器中
        if start_date and end_date:
            conflict_orders = Order.query.filter(Order.begin_date<=end_date,Order.end_date>=start_date).all()
        if start_date:
            conflict_orders = Order.query.filter(Order.end_date>=start_date).all()
        if end_date:
            conflict_orders = Order.query.filter(Order.begin_date<=end_date)
        #使用列表推导式遍历冲突的订单得到与日期冲突的房屋
        conflict_houses_id = [order.house_id for order in conflict_orders]
        #如果存在就加入容器中
        if conflict_houses_id:
            params_filter.append(House.id.notin_(conflict_houses_id))
        #按照排序条件排序
        #按订单由多到少排序
        if 'booking' == sort_key:
            houses = House.query.filter(*params_filter).order_by(House.order_count.desc())
        #按价格由低到高排序
        if 'price-inc' == sort_key:
            houses = House.query.filter(*params_filter).order_by(House.price.asc())
        #按价格从高到低排序
        if 'price-desc' == sort_key:
            houses = House.query.filter(*params_filter).order_by(House.price.desc())
        #默认按发布时间最新排序
        else:
            houses = House.query.filter(*params_filter).order_by(House.create_time.desc())
    #分页，获取每页数据和分页之后的总页数
        houses_page = houses.paginate(page,constants.HOUSE_LIST_PAGE_CAPACITY,False)
        houses_list = houses_page.items
        total_page = houses_page.pages
    #遍历分页数据，定义一个容器调用模型类的方法添加到容器中
        houses_dict_list = []
        for house in houses_list:
            houses_dict_list.append(house.to_basic_dict())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='查询房屋列表数据失败')
    #构造响应结果
    resp = {"errno":0,"errmsg":"OK","data":{"houses":houses_dict_list,
                                            "total_page":total_page,
                                            "current_page":page
                                            }}
    #转成json准备存储到redis
    resp_json = json.dumps(resp)
    #当用户请求页数不大于总页数时，才能存入redis
    if page <= total_page:
        redis_key = 'houses_%s_%s_%s_%s'%(area_id,start_date,end_date,sort_key)
        pip = redis_store.pipeline()
    #需要调用redis的事务保存数据
        try:
            #开启事务
            pip.multi()
            #保存数据
            pip.hset(redis_key,page,resp_json)
            #设置过期时间
            pip.expire(redis_key,constants.HOUSE_LIST_REDIS_EXPIRES)
            #提交事务
            pip.execute()
        except Exception as e:
            current_app.logger.error(e)
    #返回结果
    return resp_json













