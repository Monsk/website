from sqlalchemy import *
from migrate import *
import datetime


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
blog_entry = Table('blog_entry', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('title', String(length=64)),
    Column('subtitle', String(length=120)),
    Column('slug', String(length=64)),
    Column('content', Text),
    Column('image_filename', String(length=200)),
    Column('published', Boolean),
    Column('timestamp', DateTime, default=datetime.datetime.now),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['blog_entry'].columns['image_filename'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['blog_entry'].columns['image_filename'].drop()
