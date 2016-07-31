import datetime
import re
import cloudinary.utils
from sqlalchemy.sql import select
from unidecode import unidecode


from app import db
from app import app

# _punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


class BlogEntry(db.Model):
    __tablename__ = "blog_entry"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True)
    subtitle = db.Column(db.String(120), index=True)
    slug = db.Column(db.String(64), index=True, unique=True)
    content = db.Column(db.Text, index=False)
    image_filename = db.Column(db.String(200))
    published = db.Column(db.Boolean, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now, index=True)

    @property
    def html_content(self):
        """
        Generate HTML representation of the markdown-formatted blog entry,
        and also convert any media URLs into rich media objects such as video
        players or images.
        """
        hilite = CodeHiliteExtension(linenums=False, css_class='highlight')
        extras = ExtraExtension()
        markdown_content = markdown(self.content, extensions=[hilite, extras])
        oembed_content = parse_html(
            markdown_content,
            oembed_providers,
            urlize_all=True,
            maxwidth=app.config['SITE_WIDTH'])
        return Markup(oembed_content)

    @property
    def image_path(self):
        return cloudinary.utils.cloudinary_url(self.image_filename)[0]

    # def save(self, *args, **kwargs):
    #     # Generate a URL-friendly representation of the entry's title.
    #     if not self.slug:
    #         self.slug = re.sub('[^\w]+', '-', self.title.lower()).strip('-')
    #     ret = super(BlogEntry, self).save(*args, **kwargs)
    #
    #     # Store search content.
    #     self.update_search_index()
    #     return ret

    def update_search_index(self):
        # Create a row in the FTSEntry table with the post content. This will
        # allow us to use SQLite's awesome full-text search extension to
        # search our entries.
        try:
            fts_entry = FTSEntry.get(FTSEntry.entry_id == self.id)
        except FTSEntry.DoesNotExist:
            fts_entry = FTSEntry(entry_id=self.id)
            force_insert = True
        else:
            force_insert = False
        fts_entry.content = '\n'.join((self.title, self.content))
        fts_entry.save(force_insert=force_insert)

    @classmethod
    def public(cls):
        return select([BlogEntry]).where(BlogEntry.published == True)
        # return BlogEntry.select().where(BlogEntry.published == True)

    @classmethod
    def drafts(cls):
        return select([BlogEntry]).where(BlogEntry.published == False)

    @classmethod
    def search(cls, query):
        words = [word.strip() for word in query.split() if word.strip()]
        if not words:
            # Return an empty query.
            return BlogEntry.select().where(BlogEntry.id == 0)
        else:
            search = ' '.join(words)

        # Query the full-text search index for entries matching the given
        # search query, then join the actual Entry data on the matching
        # search result.
        return (FTSEntry
                .select(
                    FTSEntry,
                    BlogEntry,
                    FTSEntry.rank().alias('score'))
                .join(BlogEntry, on=(FTSEntry.entry_id == Entry.id).alias('entry'))
                .where(
                    (BlogEntry.published == True) &
                    (FTSEntry.match(search)))
                .order_by(SQL('score').desc()))

    def __repr__(self):  # pragma: no cover
        return '<BlogEntry %r>' % (self.title)

# class FTSEntry(FTSModel):
#     entry_id = IntegerField(BlogEntry)
#     content = TextField()
#
#     class Meta:
#         database = database
