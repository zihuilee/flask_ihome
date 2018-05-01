#coding=utf-8
from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
from ihome import create_app,db
from ihome import models


#调用init文件中的create_app获取app
app = create_app('developement')
Migrate(app,db)
manager = Manager(app)
#给flask-script添加db命令
manager.add_command('db',MigrateCommand)


if __name__ == '__main__':
    # app.run()
    print app.url_map
    manager.run()