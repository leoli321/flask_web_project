# -*- coding: cp936 -*-
#����author�����������û���֤ϵͳ
from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import views
