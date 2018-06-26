#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
import config

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)
lm = LoginManager(app)
Bootstrap(app)
CSRFProtect(app)

lm.session_protection = 'strong'

import view