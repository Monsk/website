from playhouse.migrate import *

# SQLite example:
my_db = SqliteDatabase('blog.db')
migrator = SqliteMigrator(my_db)

subtitle = CharField(default='')

migrate(
    migrator.add_column('BlogEntry', 'subtitle', subtitle)
)
