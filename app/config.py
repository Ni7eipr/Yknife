#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
# DEBUG = False

SECRET_KEY = "SECRET_KEY"

# mysql 配置
DB = {
    'host': '127.0.0.1',
    'port': '3306',
    'database': 'test',
    'username': 'root',
    'password': '',
}

# sql 链接地址
# SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8".format(DB['username'], DB['password'], DB['host'], DB['port'], DB['database'])
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

# 如果设置成 True (默认情况)，Flask-SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存， 如果不必要的可以禁用它。
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 使用本地 bootstrap
BOOTSTRAP_SERVE_LOCAL = True
