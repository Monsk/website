from sqlalchemy import *
from migrate import *


from migrate.changeset import schema


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    user = Table('user', meta, autoload=True)
    user.c.user_id.alter(type=String(64))
    user.c.profile_pic.alter(type=String(120))


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    user = Table('user', meta, autoload=True)
    user.c.user_id.alter(type=Integer)
    user.c.profile_pic.alter(type=Text)
