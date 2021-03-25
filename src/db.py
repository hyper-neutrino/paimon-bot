from client import *

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import func

app = Flask("paimon")

app.config["SQLALCHEMY_DATABASE_URI"] = config["psql-url"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Helper():
  @classmethod
  def add(cls, **k):
    item = cls(**{a: k[a] for a in k if a != "__no_commit"})
    db.session.add(item)
    if k.get("__no_commit") != True: db.session.commit()
    return item

  @classmethod
  def remove(cls, obj, __no_commit = False):
    db.session.delete(obj)
    if not __no_commit: db.session.commit()

class anagram_puzzle(db.Model, Helper):
  channel = db.Column(db.BigInteger, primary_key = True)
  ans = db.Column(db.String(255))
  clue = db.Column(db.String(255))
  hint = db.Column(db.Integer)

class leaderboard(db.Model, Helper):
  guild = db.Column(db.BigInteger, primary_key = True)
  user = db.Column(db.BigInteger, primary_key = True)
  anagram = db.Column(db.Integer, default = 0)

class links(db.Model, Helper):
  user = db.Column(db.BigInteger, primary_key = True, unique = True)
  league = db.Column(db.String(255))

class private_channels(db.Model, Helper):
  channel_id = db.Column(db.BigInteger, primary_key = True, unique = True)

class messages(db.Model, Helper):
  message_id = db.Column(db.BigInteger, primary_key = True, unique = True)
  guild_id = db.Column(db.BigInteger, primary_key = True)
  channel_id = db.Column(db.BigInteger, primary_key = True)
  author_id = db.Column(db.BigInteger, primary_key = True)
  created_at = db.Column(db.DateTime)
  content_size = db.Column(db.Integer)
  attachment_size = db.Column(db.Integer)
  mention_everyone = db.Column(db.Boolean)

class doujins(db.Model, Helper):
  nhid = db.Column(db.Integer, primary_key = True, unique = True)
  title = db.Column(db.String(65535))
  subtitle = db.Column(db.String(65535))
  sauce = db.Column(db.BigInteger)

class doujin_urls(db.Model, Helper):
  nhid = db.Column(db.Integer, primary_key = True)
  index = db.Column(db.Integer, primary_key = True)
  url = db.Column(db.String(65535))

class nhentai_embeds(db.Model, Helper):
  nhid = db.Column(db.Integer, primary_key = True)
  message_id = db.Column(db.BigInteger, primary_key = True, unique = True)
  page = db.Column(db.Integer, default = 0)

class watch_channels(db.Model, Helper):
  channel_id = db.Column(db.BigInteger, primary_key = True, unique = True)
  genshin = db.Column(db.Boolean, default = False)

class last_genshin_remind(db.Model, Helper):
  channel_id = db.Column(db.BigInteger, primary_key = True, unique = True)
  last_remind = db.Column(db.Integer, default = 0)

class genshin_embeds(db.Model, Helper):
  message_id = db.Column(db.BigInteger, primary_key = True, unique = True)

class genshin_resin(db.Model, Helper):
  user_id = db.Column(db.BigInteger, primary_key = True, unique = True)
  reminder = db.Column(db.Integer)
  time = db.Column(db.Integer)

class channel_links(db.Model, Helper):
  src = db.Column(db.BigInteger, primary_key = True)
  dest = db.Column(db.BigInteger)

class starboards(db.Model, Helper):
  guild_id = db.Column(db.BigInteger, primary_key = True, unique = True)
  channel_id = db.Column(db.BigInteger, primary_key = True, unique = True)

class starlinks(db.Model, Helper):
  guild = db.Column(db.BigInteger, primary_key = True)
  src_channel = db.Column(db.BigInteger)
  src = db.Column(db.BigInteger, primary_key = True, unique = True)
  dest_channel = db.Column(db.BigInteger)
  dest = db.Column(db.BigInteger, primary_key = True, unique = True)

db.create_all()

commit = db.session.commit

def get_link(member, category):
  entry = links.query.filter_by(user = member.id).first()
  if entry:
    return getattr(entry, category)
  else:
    return None

def add_message(message, __no_commit = False):
  rm_message(message.id, __no_commit = __no_commit)
  db.session.add(messages(
    message_id = message.id,
    guild_id = message.guild.id,
    channel_id = message.channel.id,
    author_id = message.author.id,
    created_at = message.created_at,
    content_size = len(message.clean_content) + sum(map(len, message.embeds)),
    attachment_size = sum(attachment.size for attachment in message.attachments),
    mention_everyone = message.mention_everyone
  ))
  if not __no_commit:
    commit()

def rm_message(mid, __no_commit = False):
  for entry in messages.query.filter_by(message_id = mid).all():
    db.session.delete(entry)
  if not __no_commit:
    commit()