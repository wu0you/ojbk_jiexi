#-*- coding=utf-8 -*-
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from app import app, db
from config import *
from app.models import *


manager = Manager(app)
migrate = Migrate(app, db)

app.jinja_env.globals['domain'] = domain
app.jinja_env.globals['mm2'] = mm2
app.jinja_env.globals['porn91'] = porn91

def make_shell_context():
    return dict(app=app, db=db)


manager.add_command('Shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
