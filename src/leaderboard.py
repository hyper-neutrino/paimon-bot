import discord

from db import leaderboard, commit

def get_entry(member):
  return leaderboard.query.filter_by(guild = member.guild.id, user = member.id).first()

def make_entry(member):
  return leaderboard.add(guild = member.guild.id, user = member.id)

def score(member, category):
  entry = get_entry(member)
  if entry:
    return getattr(entry, category)
  else:
    return 0

def set_score(member, category, value):
  entry = get_entry(member) or make_entry(member)
  setattr(entry, category, value)
  commit()
  return value

def add_score(member, category, value):
  return set_score(member, category, score(member, category) + value)

def score_pairs(members, category):
  ids = {member.id: member for member in members}
  scores = []
  for entry in leaderboard.query.all():
    if entry.user in ids:
      scores.append((ids[entry.user], getattr(entry, category)))
  scores.sort(key = lambda x: (-x[1], x[0].display_name))
  return scores

def format_leaderboard(title, members, category, empty = ""):
  return discord.Embed().add_field(
    name = title,
    value = "\n".join(f"{member.mention} - {points}" for member, points in score_pairs(members, category)) or empty or "(this leaderboard is empty!)"
  )