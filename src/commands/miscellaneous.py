import random, re, requests

from client import *
from db import *
from display import *
from leaderboard import format_leaderboard

lb_titles = {
  "anagram": "Anagram Leaderboard"
}

link_titles = {
  "league": "League of Legends"
}

@slash.slash(name = "say", description = "Say your message (in plaintext)", guild_ids = guilds, options = [
  create_option(
    name = "message",
    description = "The message to say",
    option_type = 3,
    required = True,
  )])
async def say(ctx, message):
  await ctx.respond(True)
  await ctx.send(message)

@slash.slash(name = "blame", description = "Blame a random user", guild_ids = guilds)
async def blame(ctx):
  await send_embed(ctx, discord.Embed(
    description = f"It was {random.choice([member for member in ctx.channel.members if not member.bot]).mention}'s fault!"
  ))

@slash.slash(name = "emoji", description = "Display an emoji (from any guild I have access to)", guild_ids = guilds, options = [
  create_option(
    name = "emoji_name",
    description = "The emoji to display",
    option_type = 3,
    required = True
  )])
async def display_emoji(ctx, emoji_name):
  await ctx.respond(True)
  await ctx.send(str(emoji(emoji_name)))

@slash.slash(name = "leaderboard", description = "Show a leaderboard (guild-specific)", guild_ids = guilds, options = [
  create_option(
    name = "category",
    description = "The leaderboard to display",
    option_type = 3,
    required = True,
    choices = [
      create_choice(name = "anagram", value = "anagram")
    ]
  )])
async def leaderboard(ctx, category):
  await send_embed(ctx, format_leaderboard(lb_titles[category], ctx.channel.members, category), True)

@slash.slash(name = "link", description = "Link/unlink yourself to an external ID", guild_ids = guilds, options = [
  create_option(
    name = "category",
    description = "The service to link to",
    option_type = 3,
    required = True,
    choices = [
      create_choice(name = "league", value = "league")
    ]
  ),
  create_option(
      name = "ext_id",
      description = "Your external id / name (leave blank to unlink)",
      option_type = 3,
      required = False
  )])
async def leaderboard(ctx, category, ext_id = None):
  entry = links.query.filter_by(user = ctx.author.id).first()
  if not entry:
    entry = links.add(user = ctx.author.id)
  setattr(entry, category, ext_id)
  commit()
  await send_embed(ctx, discord.Embed(
    description = f"Linked you to {ext_id} in {link_titles[category]}!" if ext_id else f"Unlinked you in {link_titles[category]}!"
  ), True)

@slash.slash(name = "query", description = "Make a database query", guild_ids = guilds, options = [
  create_option(
    name = "query",
    description = "SQL query",
    option_type = 3,
    required = True
  )])
async def run_query(ctx, query):
  if ctx.author.id not in config["sudo"]:
    raise BotError("You must be a sudo user to use this command!")
  result = db.engine.execute(query)
  keys = result.keys()
  if not keys:
    await send_embed(ctx, discord.Embed(
      description = "Command ran successfully but did not return any results."
    ))
    return
  cwidth = list(map(len, keys))
  rows = []
  for row in result:
    rows.append(row)
    for index in range(len(cwidth)):
      cwidth[index] = max(cwidth[index], len(str(row[index])))
  await send_embed(ctx, discord.Embed(
    description = "```" + " | ".join(key.ljust(width) for key, width in zip(keys, cwidth)) + "\n" + "-" * sum(cwidth) + "---" * (len(cwidth) - 1) + "\n" + "\n".join(" | ".join(str(val).ljust(width) for val, width in zip(row, cwidth)) for row in rows) + "```"
  ))

@slash.slash(name = "summary", description = "Summarize a website (works best on news)", guild_ids = guilds, options = [
  create_option(
    name = "url",
    description = "The website to summarize",
    option_type = 3,
    required = True
  ),
  create_option(
    name = "sentences",
    description = "The number of sentences to include",
    option_type = 4,
    required = False
  ),
  create_option(
    name = "keywords",
    description = "The number of keywords to display",
    option_type = 4,
    required = False
  )])
async def summary(ctx, url, sentences = None, keywords = None):
  await ctx.respond(True)
  rurl = f"https://api.smmry.com/?SM_API_KEY={config['api-keys']['sm']}"
  if sentences is not None:
    rurl += "&SM_LENGTH=" + str(sentences)
  if keywords is not None:
    rurl += "&SM_KEYWORD_COUNT=" + str(keywords)
  rurl += "&SM_URL=" + url
  r = requests.get(rurl)
  data = r.json()
  if "sm_api_error" in data:
    error = data["sm_api_error"]
    if error == 0:
      raise BotError("Internal server problem with the SMMRY API; this is not your fault. Try again later.")
    elif error == 1:
      raise BotError("Parameters are invalid. Check that you entered a real URL; otherwise, contact a developer.")
    elif error == 2:
      raise BotError("This request has intentionally been restricted by SMMRY. Perhaps you have expended the API key's limit (100 per day).")
    elif error == 3:
      raise BotError("Summarization error. This website might not be summarizable.")
  else:
    embed = discord.Embed(
      title = data["sm_api_title"].strip() or "(no title)",
      description = data["sm_api_content"].strip() or "(no content)"
    )
    if "sm_api_keyword_array" in data:
      embed.add_field(
        name = "Keywords",
        value = ", ".join(data["sm_api_keyword_array"])
      )
    await send_embed(ctx, embed, True)

@client.message_handler
async def ehe(message):
  if re.search(r"\b[hH]?[eE][hH][eE]\b", message.content):
    if message.author != client.user:
      await message.channel.send("**ehe te nandayo!?**")
      await message.add_reaction("❔")

@client.message_handler
async def emoji_react(message):
  for c in re.findall(r"\[(\w+)\]", message.content):
    try:
      await message.add_reaction(emoji(c))
    except:
      pass

@client.delete_handler
async def ping_delete(message):
  mentions = []
  for u in message.mentions:
    mentions.append(u.mention)
  for r in message.role_mentions:
    mentions.append(r.mention)
  if message.mention_everyone:
    mentions.append("@everyone/@here")
  if mentions:
    await message.channel.send(embed = discord.Embed(description = "A message was deleted that mentioned " + english_list(mentions)))

@client.edit_handler
async def ping_edit(before, after):
  mentions = []
  for u in before.mentions:
    if u not in after.mentions:
      mentions.append(u.mention)
  for r in before.role_mentions:
    if r not in after.role_mentions:
      mentions.append(r.mention)
  if before.mention_everyone and not after.mention_everyone:
    mentions.append("@everyone/@here")
  if mentions:
    await after.channel.send(embed = discord.Embed(description = "A message was edited that previously mentioned " + english_list(mentions)))