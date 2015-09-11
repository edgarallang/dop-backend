# -*- coding: utf-8 -*-

from flask.ext.script import Manager

from fbone import create_app
from fbone.extensions import db
from flask_apscheduler import APScheduler
from fbone.user import User, UserImage, UserLevel, ADMIN, ACTIVE
from fbone.utils import MALE


app = create_app()
app.test_request_context().push()
scheduler = APScheduler()
scheduler.init_app(app)
manager = Manager(app)


@manager.command
def run():
    """Run in local machine."""
    scheduler.start()
    app.run(host='0.0.0.0', use_reloader=False)

@manager.command
def initdb():
    """Init/reset database."""

    # db.drop_all()
    db.create_all()

    #admin = BranchUser(
    #        branch_id=2,
    #        name=u'Edgar',
    #        email=u'admin@fucking.com',
    #        password=u'123456')
    #db.session.add(admin)
    #db.session.commit()


manager.add_option('-c', '--config',
                   dest="config",
                   required=False,
                   help="config file")

if __name__ == "__main__":
    manager.run()
