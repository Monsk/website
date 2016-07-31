from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
blog_entry = Table('blog_entry', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('title', VARCHAR(length=64)),
    Column('subtitle', VARCHAR(length=120)),
    Column('slug', VARCHAR(length=64)),
    Column('content', VARCHAR),
    Column('published', BOOLEAN),
    Column('timestamp', DATETIME),
    Column('content2', TEXT),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['blog_entry'].columns['content2'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['blog_entry'].columns['content2'].create()
