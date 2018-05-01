#coding=utf-8
import redis
class Config(object):
    # 配置SECREK_KEY
    SECRET_KEY = "jlhqsDJKREWASDFGJKLNSALFJKLHNSLJFKHGNLMSW"
    #配置mysql数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@localhost/love_home"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    #配置redis
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379

    #将session信息存到redis
    SESSION_TYPE = "redis"
    #构造redis数据库的实例
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 86400

class DevelopementConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    pass

config = {
    'developement':DevelopementConfig,
    'production':ProductionConfig
}