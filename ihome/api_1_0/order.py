#coding=utf-8
from . import api
from flask import g,current_app,request,jsonify,session
from ihome import db
from ihome.utils.response_code import RET
import datetime
from ihome.models import House,Order
from ihome.utils.commons import login_required
from ihome import redis_store

'''
@api.route('/orders',methods=['POST'])
@login_required
def save_orders():
    #保存订单信息
    """
    1.获取用户id
    2.获取json数据
    3.判断获取结果
    4.获取详细参数--start_date_str,end_date_str,house_id
    5.把日期参数格式化
    6.计算预定的天数
    7.查询房屋是否存在
    8.判断不是房东才能预订
    9.查询与日期冲突的订单数量，计算房屋总价
    10.构造模型类对象，
    11.添加数据库会话对象
    12.提交数据到数据库
    13.返回结果
    """
    #获取user_id
    user_id = g.user_id
    #获取post请求发送来的数据
    req_data = request.get_json()
    #判断获取结果
    if not req_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #进一步获取详细参数-house_id,start_date_str,end_date_str
    house_id = req_data.get('house_id')
    start_date_str = req_data.get('start_date')
    end_date_str = req_data.get('end_date')
    #检验参数完整性，把日期参数格式化datetime
    if not all([house_id,start_date_str,end_date_str]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺少')
    try:
        start_date = datetime.datetime.strptime(start_date_str,'%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str,'%Y-%m-%d')
        #断言订单天数至少一天
        assert end_date <= start_date
        # 计算出预订的天数
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='日期参数格式错误')
    #查询房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋数据失败')
    #判断查询结果
    if not house:
        return jsonify(errno=RET.NODATA,errmsg='没有查询到房屋数据')
    #判断是否是房东
    if house.user_id == user_id:
        return jsonify(errno=RET.ROLEERR,errmsg='不能预订自己的房屋')
    #查询房屋是否被预订,查询与日期冲突的订单数
    try:
        count = Order.query.filter(Order.house_id==house_id,
                                   Order.begin_date <= end_date,
                                   Order.end_date >= start_date
                                   ).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='检查出错，请稍后重试')
    #判断订单数
    if count > 0:
        return jsonify(errno=RET.DATAERR,errmsg='房屋已被预订')
    #计算总价
    amount = house.price * days
    #构建模型类对象，保存订单基本信息
    order = Order()
    order.house_id = house_id
    order.user_id = user_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = amount
    #保存订单数据到数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存订单失败')
    #返回数据
    return jsonify(errno=RET.OK,errmsg='OK',data={'order_id':order.id})

@api.route('/user/orders',methods=['GET'])
@login_required
def show_user_order():
    #展示用户订单列表，一个接口，两种实现方式
    """
    1.获取user_id
    2.获取参数role，判断是房东进来查询订单，还是房客进来查询自己预订别人房屋的订单
    3.查询订单数据，分情况查询
    4.定义容器存储查询结果
    5.遍历查新结果，调用模型类的方法
    6.返回结果
    """
    #获取user_id
    user_id = g.user_id
    #获取身份role,没有就默认为空
    role = request.args.get('role','')
    #查询订单数据
    try:
        #房东身份获取预订自己房屋的订单
        if 'landlord' == role:
        #先查询属于自己的房子
            houses = House.query.filter(House.user_id==user_id).all()
            house_ids = [house.id for house in houses]
        #再查询预订自己房屋的订单,按照房屋订单发布时间倒序排序
            orders = Order.query.filter(Order.house_id.in_(house_ids)).order_by(
            Order.create_time.desc()).all()
        else:
            #以房客的身份查询自己预订别人房屋的订单
            orders = Order.query.filter(Order.user_id==user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询订单信息失败')
    #定义容器
    orders_dict_list = []
    #遍历查询结果，调用模型类的方法
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'orders':orders_dict_list})

@api.route('/orders/<int:order_id>/status',methods=['PUT'])
@login_required
def accept_reject_order(order_id):
    #接单和拒单
    """
    1.获取user_id
    2.获取json数据
    3.判断获取结果
    4.获取action--- 确定是接单还是拒单
    5.判断获取结果是否是accept和reject中的一个
    6.查询出要操作的订单
    7.房东只能修改属于自己房屋的订单
    8.如果是接单，修改订单状态为待评价
    9.如果是拒单，就获取拒单理由，修改订单状态为已拒绝，添加拒单原因
    10.添加数据库会话对象
    11.提交数据到数据库
    12.返回结果
    """
    #获取user_id
    user_id = g.user_id
    #获取json数据
    req_data = request.get_json()
    #判断获取结果
    if not req_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取参数action
    action = req_data.get('action')
    #判断获取结果,action属性是接单和拒单其中一个
    if action not in("accept","reject"):
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #查询出要修改的订单,根据订单号查询,并且订单状态是等待接单状态
    try:
        order = Order.query.filter(Order.id==order_id,Order.status=="WAIT_ACCEPT").first()
        #查询出所属房屋
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='无法获取订单数据')
    #确保房东不能修改别人房屋的订单信息
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR,errmsg='操作无效')
    #如果是接单，就改变订单状态为待评论
    if 'accept' == action:
        order.status = "WAIT_COMMENT"
    #拒单就获取拒单原因，改变订单状态，添加拒单原因
    elif 'reject' == action:
        #尝试获取拒单原因
        reason = req_data.get('reason')
        if not reason:
            return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
        order.status = 'REJECTED'
        order.comment = reason
    #添加数据库会话对象
    try:
        db.session.add(order)
        db.session.commit()
    #提交数据到数据库
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='操作失败')
    #返回结果
    return jsonify(errno=RET.OK,errmsg="OK")

@api.route('/orders/<int:order_id>/comment',methods=['PUT'])
@login_required
def save_order_comment(order_id):
    #保存订单评论信息
    """
    1.获取user_id
    2.获取json数据
    3.判断获取结果
    4.获取评论信息
    5.判断获取结果
    6.根据order_id，订单状态为待评论查询订单
    7.查询所属房屋
    8.检查查询结果
    9.修改订单状态，添加评论信息，订单数量+1
    10.添加数据库会话对象--order,house
    11.提交数据到数据库
    12.删除redis中的信息
    13.返回结果
    """
    #获取user_id
    user_id = g.user_id
    #获取json数据
    req_data = request.get_json()
    #判断获取结果
    if not req_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取评论信息
    comment = req_data.get('comment')
    #判断获取结果
    if not comment:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #根据order_id，订单状态为待评论查询订单
    try:
        order = Order.query.filter(Order.id==order_id,Order.user_id==user_id,Order.status=='WAIT_COMMENT').first()
        #查询所属房屋
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='无法获取订单数据')
    #判断查询结果
    if not order:
        return jsonify(errno=RET.REQERR,errmsg='操作无效')
    #修改订单状态,添加订单评论，订单数量加1
    try:
        order.status = 'COMPLETE'
        order.comment = comment
        house.order_count += 1
    #添加数据库会话对象--order,house
        db.session.add(order)
        db.session.add(house)
        # 提交数据到数据库
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存订单信息失败')
    #删除缓存中的信息
    try:
        redis_store.delete('house_info_%s'% order.house_id)
    except Exception as e:
        current_app.logger.error(e)
    #返回结果
    return jsonify(errno=RET.OK,errmsg="OK")
'''

@api.route('/orders',methods=['POST'])
@login_required
def save_orders():
    """保存订单"""
    #获取user_id
    user_id = g.user_id
    #获取json数据
    req_data = request.get_json()
    #判断获取结果
    if not req_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取详细参数--house_id,start_date_str,end_date_str
    house_id = req_data.get('house_id')
    start_date_str = req_data.get('start_date')
    end_date_str = req_data.get('end_date')
    #检验参数完整性
    if not all([house_id,start_date_str,end_date_str]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #格式化日期参数，断言订单时间至少一天，计算预订天数
    try:
        start_date = datetime.datetime.strptime(start_date_str,'%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str,'%Y-%m-%d')
        assert end_date >= start_date
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='日期格式错误')
    #查询房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询房屋数据失败')
    #确保房东不能预订自己的房屋
    if house.user_id == user_id:
        return jsonify(errno=RET.REQERR,errmsg='不能预订自己的房屋')
    #查询与日期冲突的订单
    try:
        count = Order.query.filter(Order.house_id==house_id,
                                    Order.begin_date<=end_date,
                                    Order.end_date>=start_date
                                    ).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='检查出错，请稍后重试')
     #判断订单数量
    if count > 0:
        return jsonify(errno=RET.DATAERR,errmsg='房屋已被预订')
    #计算房屋总价
    amount = house.price * days
    #构建模型类，修改订单状态为待评论，添加房屋基本信息
    order = Order()
    order.house_id = house_id
    order.user_id = user_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = amount
    #添加数据库会话对象
    try:
        db.session.add(order)
        #提交数据到数据库
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存订单信息失败')
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'order_id':order.id})

@api.route('/user/orders',methods=['GET'])
@login_required
def get_user_order():
    """获取用户订单页"""
    #一个接口，两种实现方式，通过role判断用户身份，房东就查询预订自己房屋的订单，房客就查询
    #自己预订别人房屋的订单
    #获取user_id
    user_id = g.user_id
    #获取role,没有就默认是空
    role = request.args.get('role','')
    #如果是房东，查询属于自己的房屋，再查询预订自己房屋的订单
    try:
        if 'landlord' == role:
            houses = House.query.filter(House.user_id==user_id).all()
            house_ids = [house.id for house in houses]
            #查询出房屋的订单,按订单创建时间倒序排序
            orders = Order.query.filter(Order.house_id.in_(house_ids)).order_by(
               Order.create_time.desc()).all()
        # 如果是房客，查询自己预订别人房屋的订单
        else:
            orders = Order.query.filter(Order.user_id==user_id).order_by(
                Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取订单数据失败')
    #判断查询结果
    if not orders:
        return jsonify(errno=RET.NODATA,errmsg='没有获取到订单信息')
    #定义容器，存储查询结果
    orders_dict_list = []
    #遍历查询结果，调用模型类的方法
    for order in orders:
        orders_dict_list.append(order.to_dict())
    #返回数据
    return jsonify(errno=RET.OK,errmsg='OK',data={'orders':orders_dict_list})


@api.route('/orders/<int:order_id>/status',methods=['PUT'])
@login_required
def accept_reject_order(order_id):
    """接单和拒单---房东"""
    #一个接口，通过action的不同来区分接单还是拒单
    #获取user_id
    user_id = g.user_id
    #获取json数据
    req_data = request.get_json()
    #判断获取结果
    if not req_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取action参数
    action = req_data.get('action')
    #判断action是否是accept和reject其中一个
    if action not in ('accept','reject'):
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    # 查询出房屋所属的订单,根据order_id和订单状态
    try:
        order = Order.query.filter(Order.id==order_id,Order.status=='WAIT_ACCEPT').first()
        #查询出订单所属房屋
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取订单信息失败')
    #确保房东不能修改别人的订单
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR,errmsg='操作无效')
    #如果是接单，就修改订单状态为待评论
    if 'accept' == action:
        order.status = 'WAIT_COMMENT'
    # 如果是拒单就要 获取拒单理由，修改订单状态为已拒单
    elif 'reject' == action:
        order.status ='REJECTED'
        reason = req_data.get('reason')
        if not reason:
            return jsonify(errno=RET.DATAERR,errmsg='需写明拒单理由')
        order.comment = reason
    #添加数据库会话对象
    try:
        db.session.add(order)
        # 提交数据到数据库
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存订单信息失败')
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK')

@api.route('/orders/<int:order_id>/comment',methods=['PUT'])
@login_required
def save_order_comment(order_id):
    """订单评论"""
    #获取user_id
    user_id = g.user_id
    #获取json数据
    req_data = request.get_json()
    #判断获取结果
    if not req_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #获取评论信息
    comment = req_data.get('comment')
    #判断获取结果
    if not comment:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    #查询订单,根据订单id,订单状态为待评论，user_id
    try:
        order = Order.query.filter(Order.id==order_id,
                                   Order.user_id==user_id,
                                   Order.status=='WAIT_COMMENT').first()
        #查询订单所属房屋
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='无法获取订单信息')
    #判断查询结果
    if not order:
        return jsonify(errno=RET.REQERR,errmsg='操作无效')
    #使用模型类属性的方法，修改订单状态，添加订单评论，订单数量加1
    try:
        order.status = 'COMPLETE'
        order.comment = comment
        house.order_count += 1
        # 添加数据库会话对象,提交数据到数据库
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='操作错误')
    #删除缓存中的房屋信息
    try:
        redis_store.delete('house_info_%s'%order.house_id)
    except Exception as e:
        current_app.logger.error(e)
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK')

























