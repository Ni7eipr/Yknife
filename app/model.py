#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    passwd = db.Column(db.String(128), nullable=False)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__()
        self.id = kwargs.get('id')
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        self.passwd = generate_password_hash(kwargs.get('passwd'))

    def check_password(self, rawpwd):
        return check_password_hash(self.passwd, rawpwd)

    def __repr__(self):
        return self.username

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def get_id(self):
        return self.id


class Shells(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    uid = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    passwd = db.Column(db.String(512), nullable=False)
    # coding = db.Column(db.Enum("UTF8", "GB18030"), default="UTF8")
    coding = db.Column(db.String(6), nullable=False)
    # types = db.Column(db.Enum("php", "ASP", "ASPX", "JSP"), default="php")
    types = db.Column(db.String(6), nullable=False)
    note = db.Column(db.Text)
    info = db.Column(db.String(512))
    encoder = db.Column(db.String(6), nullable=False)
    headers = db.Column(db.Text)
    cookies = db.Column(db.Text)
    data = db.Column(db.Text)
    proxy = db.Column(db.String(128))
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    ip = db.Column(db.String(15), nullable=False)
    location = db.Column(db.String(32), nullable=False)
    groups = db.Column(db.String(32), nullable=False)
    database = db.Column(db.String(512))


class Config(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    uid = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    theme = db.Column(db.String(20), default='darkly')