#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os, uuid, sys, requests, re
from datetime import datetime
from app import app, lm, db
from flask import request, g, render_template, flash, make_response, redirect, url_for, jsonify, abort
from model import Shells, User, Config
from config import basedir
from form import SigninForm, SignupForm, ConfigForm, DataForm
from request import PAYLOAD
from flask_login import login_required, login_user, current_user
from request import dataRequest
from socket import gethostbyname
from jinja2.filters import do_filesizeformat
if sys.version < '3':
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

@lm.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@lm.unauthorized_handler
def unauthorized_handler():
    return abort(404)


def get_group():
    groups = [i[0] for i in db.session.query(Shells.groups.distinct()).all()]
    return groups if groups else ['默认']


def get_payload():
    return [i for i in PAYLOAD]


@app.before_request
def first_request():
    g.group = get_group()
    g.payload = get_payload()
    g.theme = request.cookies.get('theme', 'darkly')
    g.name = 'Yknife'


def getIpInfo(url, proxy):
    try:
        ip = gethostbyname(urlparse(url).hostname)
        res = requests.get('http://ip.taobao.com/service/getIpInfo.php', params={'ip': ip},
                           ).json()
        if res['data']['city'] == res['data']['isp']:
            res = res['data']['isp']
        else:
            res = "{}{} {}".format(
                res['data']['country'], res['data']['city'], res['data']['isp'])
    except:
        raise
        ip = 'unknown'
        res = 'unknown'
    return {'ip': ip, 'location': res}


def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            id=str(uuid.uuid5(uuid.uuid4(), str(form.email.data))),
            username=form.username.data,
            email=form.email.data,
            passwd=form.passwd.data
        )
        config = Config(
            id=str(uuid.uuid5(uuid.uuid4(), str(user.id))),
            uid=user.id,
            theme='darkly',
        )
        db.session.add(user)
        db.session.add(config)
        db.session.commit()
        flash("注册成功", 'success')
        return redirect(url_for('signin'))
    return render_template('signup.html', form=form, signup_active="active")


def signin():
    if current_user.is_authenticated:
        return redirect(url_for('index', group=g.group[0]))
    form = SigninForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user and user.check_password(form.passwd.data):
            login_user(user, remember=form.remember.data)
            theme = db.session.query(Config.theme).filter_by(
                uid=current_user.id).first()[0]
            response = make_response(
                redirect(url_for('index', group=g.group[0])))
            response.set_cookie('theme', value=theme, max_age=9999999999)
            return response
        flash('账号或密码错误', 'danger')
    return render_template('signin.html', form=form, signin_active="active")


def signout():
    logout_user()
    flash('已退出', 'success')
    return redirect(url_for('signin'))


def index(group):
    shells = db.session.query(Shells).filter_by(
        groups=group, uid=current_user.id).order_by(Shells.update_time.desc()).all()
    return render_template('index.html', groups=g.group, shells=shells)


def profile():
    theme = []
    for i in os.listdir(os.path.join(basedir, 'static/bootswatch')):
        theme.append(i.split('.')[0])

    form = ConfigForm()
    form.theme.choices = [(i, i) for i in theme]

    if form.validate_on_submit():
        db.session.query(Config).filter_by(
            uid=current_user.id).update({"theme": form.theme.data})
        db.session.commit()

        response = make_response(redirect(url_for('profile')))
        response.set_cookie('theme', value=form.theme.data, max_age=9999999999)
        return response

    form.theme.data = db.session.query(
        Config.theme).filter_by(uid=current_user.id).first()[0]
    return render_template('profile.html', form=form)


def add():
    done = 0
    form = DataForm()
    form.types.choices = [(i, i) for i in g.payload]
    form.coding.choices = [(i, i) for i in ['UTF8', 'GB18030']]
    form.encoder.choices = [(i, i) for i in ['default']]
    form.groups.choices = [(i, i) for i in g.group]

    if form.validate_on_submit():
        shells = Shells(
            id=str(uuid.uuid5(uuid.uuid4(), str(form.url.data))),
            uid=current_user.id,
            url=form.url.data,
            passwd=form.passwd.data,
            types=form.types.data,
            coding=form.coding.data,
            encoder=form.encoder.data,
            note=form.note.data,
            headers=form.headers.data,
            cookies=form.cookies.data,
            data=form.data.data,
            proxy=form.proxy.data,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        shells.groups = form.groupn.data if form.groupn.data else form.groups.data

        req = dataRequest(shells)
        shells.info = req.info()
        if shells.info:
            ips = getIpInfo(shells.url, shells.proxy)
            shells.ip = ips['ip']
            shells.location = ips['location']

            db.session.add(shells)
            db.session.commit()
            done = 1
        else:
            done = 2

    return render_template('data.html', form=form, done=done)


def edit(shellid):
    if shellid:
        done = 0
        form = DataForm()
        form.types.choices = [(i, i) for i in g.payload]
        form.coding.choices = [(i, i) for i in ['UTF8', 'GB18030']]
        form.encoder.choices = [(i, i) for i in ['default']]
        form.groups.choices = [(i, i) for i in g.group]

        if form.validate_on_submit():
            shells = db.session.query(Shells).filter_by(id=shellid).first()

            shells.url = form.url.data
            shells.passwd = form.passwd.data
            shells.types = form.types.data
            shells.coding = form.coding.data
            shells.encoder = form.encoder.data
            shells.note = form.note.data
            shells.headers = form.headers.data
            shells.cookies = form.cookies.data
            shells.data = form.data.data
            shells.proxy = form.proxy.data
            shells.update_time = datetime.now()
            shells.groups = form.groupn.data if form.groupn.data else form.groups.data

            req = dataRequest(shells)
            shells.info = req.info()
            if shells.info:
                ips = getIpInfo(shells.url, shells.proxy)
                shells.ip = ips['ip']
                shells.location = ips['location']

                db.session.add(shells)
                db.session.commit()
                done = 1
            else:
                done = 2

        shell = db.session.query(Shells).filter_by(id=shellid).first()
        form.url.data = shell.url
        form.passwd.data = shell.passwd
        form.types.data = shell.types
        form.coding.data = shell.coding
        form.groups.data = shell.groups
        form.encoder.data = shell.encoder
        form.note.data = shell.note
        form.headers.data = shell.headers
        form.cookies.data = shell.cookies
        form.data.data = shell.data
        form.proxy.data = shell.proxy

        return render_template('data.html', form=form, done=done)


def delete():
    shell = request.form.get('id')
    if db.session.query(Shells).filter_by(id=shell).delete():
        db.session.commit()
        return jsonify({"status": 1, "msg": "删除成功"})
    return jsonify({"status": 0, "msg": "删除失败"})


def files(shellid):
    shells = db.session.query(Shells).filter_by(id=shellid).first()
    if request.method == 'GET':
        return render_template('files.html')
    else:
        req = dataRequest(shells)
        p = request.form.get('path').encode(shells.coding)
        path = shells.info.splitlines()[5] if p == 'false' else p
        # 获取文件夹列表
        files = req.files(path)
        if not files:
            return jsonify({"status": -1, "msg": '连接失败!'})
        files = files.decode(shells.coding).splitlines()
        # 解析文件夹列表
        fileslist = []
        for i in files:
            i = i.split('\t')
            if i[1] not in ('.', '..'):
                i[4] = do_filesizeformat(i[4]) if i[4] else '-'
                fileslist.append(i)
        # jstree列表
        lists = [{'text': i[1], 'children': True}
                 for i in fileslist if i[1] not in ['.', '..'] and i[0]]

        if p == 'false':
            # 解析shell路径
            path = re.split(r'[/\\]', path)
            path[0] = path[0] if path[0] else '/'
            # jstree列表
            for i in path[::-1]:
                if path.index(i) == len(path) - 1:
                    lists = [{'text': i, 'children': lists,
                              "state": {"opened": True, "selected": True}}]
                else:
                    lists = [{'text': i, 'children': lists,
                              "state": {"opened": True}}]
            # 获取磁盘信息
            disk = req.disk().splitlines()
            # jstree列表
            disk = [{'text': i, 'children': True}
                    for i in disk if i != path[0]]
            # 整合磁盘
            for k, v in enumerate(disk):
                if ord(lists[0]['text'][0]) >= ord(v['text'][0]):
                    disk.insert(k + 1, lists[0])
                    break
            else:
                disk = lists[0]
        else:
            disk = lists
        return jsonify({"status": 1, "msg": '打开文件夹成功!', "data": {"lists": disk, "files": fileslist}})


def fileo(shellid, op):
    shells = db.session.query(Shells).filter_by(id=shellid).first()
    req = dataRequest(shells)
    filename = request.args.get('f', '')
    filename = filename.encode(shells.coding)
    # 提交页面
    if filename and request.method == 'POST':
        if op == 'edit':
            content = req.read(filename)
            if not content:
                return jsonify({"status": 0, 'msg': '打开文件失败!'})
            _ = ['UTF8', 'GB18030']
            _.remove(shells.coding)
            _.insert(0, shells.coding)
            for i in _:
                try:
                    content = content.decode(i)
                    return jsonify({"status": 1, "data": {'content': content, 'coding': i}})
                except:
                    raise
        elif op == 'save':
            coding = request.form.get('coding', shells.coding)
            content = request.form.get('content').encode(coding)
            result = req.save(filename, content)
            if result:
                return jsonify({"status": 1, "msg": "保存成功", "data": result})
            else:
                return jsonify({"status": 0, "msg": "保存失败", "data": result})
        elif op == 'upload':
            upload = request.files['upload']
            result = req.upload(filename, upload)
            if result:
                return jsonify({"status": 1, "msg": "上传成功!"})
            else:
                return jsonify({"status": 0, "msg": "上传失败!"})
    # 显示页面
    if op == 'add':
        return render_template('add.html')
    elif op == 'del':
        result = req.delete(filename)
        if not result:
            return jsonify({"status": 1, "msg": '删除成功!', 'data': result})
        else:
            return jsonify({"status": 0, "msg": '删除失败：'+result})
    elif op == 'edit':
        return render_template('file.html')
    elif op == 'rename':
        oldname = request.args.get('n').encode(shells.coding)
        result = req.rename(filename, oldname)
        return jsonify({"status": 1, "msg": "", "data": ''})
    elif op == 'download':
        result = req.read(filename)
        response = make_response(result)
        response.headers['Content-Disposition'] = 'attachment; filename={}'.format(
            filename)
        return response
    elif op == 'newfiles':
        result = req.newfiles(filename)
        if request:
            return jsonify({"status": 1, "msg": "新建成功"})
    elif op == 'changetime':
        t = request.args.get('t')
        result = req.changetime(filename, t)
        if result:
            return jsonify({"status": 1, "msg": "更改成功"})


def terminal(shellid):
    shells = db.session.query(Shells).filter_by(id=shellid).first()
    info = shells.info.splitlines()
    if request.method == 'POST':
        command = request.form.get('command')
        cwd = request.form.get('cwd')
        command = "cmd /c \"cd /d %s&%s&echo \v&cd&echo \v\"" % (cwd, command) if info[0].startswith(
            'W') else "cd %s;%s;echo \v;pwd;echo \v" % (cwd, command)
        result = dataRequest(shells).command(command.encode(
            shells.coding)).decode(shells.coding, errors='ignore')
        result = [i.strip() for i in result.split('\v')]
        return jsonify({"status": 1, "msg": "", "data": result}) if result else jsonify({"status": 0, "msg": "", "data": ''})
    return render_template('terminal.html', cwd=info[5], greetings=info[0])


def database(shellid):
    shells = db.session.query(Shells).filter_by(id=shellid).first()
    req = dataRequest(shells)
    form = DatabaseForm()
    form.types.choices = [(i, i) for i in ['mysql', 'mssql']]

    if form.validate_on_submit():
        shells.database = json.dumps({
            'types': form.types.data,
            'host': form.host.data,
            'port': form.port.data,
            'user': form.user.data,
            'passwd': form.passwd.data
        })
        db.session.add(shells)
        db.session.commit()

    elif request.method == 'POST':
        path = request.form.get('path')
        sql = request.form.get('sql')
        types = request.form.get('types')
        lists = []
        data = []
        if types == 'database':
            sql = "SELECT schema_name FROM information_schema.schemata"
        elif types == 'table':
            sql = "SELECT table_name FROM information_schema.tables WHERE table_schema='%s'" % path
        elif types == 'columns':
            sql = "SELECT * FROM %s LIMIT 0, 10" % path if path else sql
        res = req.query(sql).splitlines()
        msg = res.pop(0).split('\t')[1]
        if msg:
            return jsonify({"status": -2, "msg": msg})
        else:
            if types == 'columns':
                data = []
                for i in res:
                    ir = {}
                    for j in i.split('\t'):
                        j = j.split('\v')
                        ir[j[0]] = j[1]
                    data.append(ir)
            else:
                lists = [{'text': i.split('\v')[1], 'children': True}
                         for i in res]

        return jsonify({"status": 1, "msg": "查询成功", "data": {'lists': lists, 'sql': sql, 'data': data}})

    database = json.loads(shells.database) if shells.database else {}
    form.types.data = database.get('types', '')
    form.host.data = database.get('host', '')
    form.port.data = database.get('port', '')
    form.user.data = database.get('user', '')
    form.passwd.data = database.get('passwd', '')

    return render_template('database.html', form=form)


app.add_url_rule('/', methods=['GET', 'POST'], view_func=signin)
app.add_url_rule('/signin/', methods=['GET', 'POST'], view_func=signin)
app.add_url_rule('/signup/', methods=['GET', 'POST'], view_func=signup)

app.add_url_rule('/signout/', view_func=login_required(signout))
app.add_url_rule(
    '/profile/', methods=['GET', 'POST'], view_func=login_required(profile))

app.add_url_rule('/<group>/', view_func=login_required(index))
app.add_url_rule(
    '/data/', methods=['GET', 'POST'], view_func=login_required(add))
app.add_url_rule('/data/<shellid>',
                 methods=['GET', 'POST'], view_func=login_required(edit))

app.add_url_rule('/terminal/<shellid>/',
                 methods=['GET', 'POST'], view_func=login_required(terminal))
app.add_url_rule('/files/<shellid>/',
                 methods=['GET', 'POST'], view_func=login_required(files))
app.add_url_rule('/files/<shellid>/<op>/',
                 methods=['GET', 'POST'], view_func=login_required(fileo))
app.add_url_rule('/database/<shellid>/',
                 methods=['GET', 'POST'], view_func=login_required(database))
app.add_url_rule('/delete/', methods=['POST'],
                 view_func=login_required(delete))
