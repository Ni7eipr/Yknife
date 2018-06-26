#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from model import User
from flask_wtf import FlaskForm
from wtforms import (BooleanField, PasswordField, SelectField,
                     StringField, SubmitField, TextAreaField, ValidationError)
from wtforms.validators import (URL, Email, EqualTo, InputRequired, Length, Optional)

class SignupForm(FlaskForm):
    username = StringField('账号', validators=[
        InputRequired(),
        Length(min=4, max=18)
    ])
    email = StringField('邮箱', validators=[
        Email()
    ])
    passwd = PasswordField('密码', [
        InputRequired(),
        EqualTo('confirm', message='密码不一致'),
        Length(min=8, max=32)
    ])
    confirm = PasswordField('重复密码')
    button = SubmitField('注册')

    def validate_email(form, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('该邮箱已经注册')


class SigninForm(FlaskForm):
    email = StringField('邮箱', validators=[
        Email(),
    ])
    passwd = PasswordField('密码', validators=[
        InputRequired(),
        Length(min=8, max=32)
    ])
    remember = BooleanField('记住我', default=False)
    button = SubmitField('登陆')


class DataForm(FlaskForm):
    url = StringField('地址', validators=[URL(), InputRequired()])
    passwd = StringField('密码', validators=[InputRequired()])
    types = SelectField('类型')
    coding = SelectField('编码')
    groups = SelectField('分组')
    groupn = StringField('新建分组')
    encoder = SelectField('payload类型')
    note = TextAreaField('备注')
    headers = TextAreaField('请求头')
    cookies = TextAreaField('cookies')
    data = TextAreaField('请求体')
    proxy = StringField('代理地址', validators=[URL(), Optional()],
                        render_kw={"placeholder": "http://user:pass@127.0.0.1:8080"})
    button = SubmitField('保存')

class DatabaseForm(FlaskForm):
    types = types = SelectField('类型')
    host = StringField('地址', validators=[InputRequired()])
    port = StringField('端口', validators=[InputRequired()])
    user = StringField('账号', validators=[InputRequired()])
    passwd = StringField('密码', validators=[InputRequired()])
    button = SubmitField('修改')

class ConfigForm(FlaskForm):
    theme = SelectField('主题', validators=[InputRequired()])
    button = SubmitField('保存')
