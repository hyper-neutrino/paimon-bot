import asyncio, datetime, inspect, random, re, requests, sys, time

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

@slash.slash(name = "kill", description = "kill the bot", guild_ids = guilds)
async def force_kill(ctx):
  await send_embed(ctx, discord.Embed(
    title = "Terminating self.",
    description = f"This was requested by {ctx.author.mention}."
  ))
  sys.exit(0)

@slash.slash(name = "starboard", description = "Set/unset the starboard channel", guild_ids = guilds, options = [
  create_option(
    name = "channel",
    description = "The starboard channel to set",
    option_type = 7,
    required = False
  )])
async def starboard(ctx, channel = None):
  entry = starboards.query.filter_by(guild_id = ctx.guild.id).first()
  if channel is None:
    if entry:
      starboards.remove(entry)
    await send_embed(ctx, discord.Embed(
      description = "This guild no longer has a starboard!"
    ), True)
  else:
    if entry:
      entry.channel_id = channel.id
      commit()
    else:
      starboards.add(guild_id = ctx.guild.id, channel_id = channel.id)
    await send_embed(ctx, discord.Embed(
      description = f"{channel.mention} is now this guild's starboard!"
    ), True)

@slash.slash(name = "say", description = "Say your message (in plaintext)", guild_ids = guilds, options = [
  create_option(
    name = "message",
    description = "The message to say",
    option_type = 3,
    required = True,
  ),
  create_option(
    name = "delay",
    description = "How long to wait before sending the message (default 0) in seconds",
    option_type = 4,
    required = False
  )])
async def say(ctx, message, delay = 0):
  await asyncio.sleep(delay)
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
  await ctx.send(str(emoji(emoji_name)))

@slash.slash(name = "emojilist", description = "Show which emojis I have access to", guild_ids = guilds, options = [
  create_option(
    name = "page",
    description = "Page (50 per page)",
    option_type = 4,
    required = False
  )])
async def emojilist(ctx, page = 1):
  emojis = sorted(client.emojis, key = lambda e: e.name)
  await send_embed(ctx, discord.Embed(
    title = f"My Emojis (Page {page} / {-(-len(emojis) // 50)})",
    description = " ".join(str(emoji) for emoji in emojis[(page - 1) * 50 : page * 50])
  ), True)

@slash.slash(name = "follow", description = "Cross-post from a channel by ID (ignores bot messages)", guild_ids = [699314655973212242, 805664230820151307], options = [
  create_option(
    name = "channel_id",
    description = "The channel ID",
    option_type = 3,
    required = True
  )])
async def channel_follow(ctx, channel_id):
  channel_id = int(channel_id)
  channel = client.get_channel(channel_id)
  if channel is None:
    raise BotError("I cannot access the channel with that ID!")
  if not isinstance(channel, discord.TextChannel):
    raise BotError("That is not a text channel!")
  if channel_links.query.filter_by(src = channel_id, dest = ctx.channel.id).count() == 0:
    channel_links.add(src = channel_id, dest = ctx.channel.id)
    await send_embed(ctx, discord.Embed(
      description = f"Now following {channel.guild.name}#{channel.name}!"
    ))
  else:
    raise BotError("I am already following this channel!")

@slash.slash(name = "unfollow", description = "Stop following a channel (takes an ID)", guild_ids = [699314655973212242, 805664230820151307], options = [
  create_option(
    name = "channel_id",
    description = "The channel ID",
    option_type = 3,
    required = True
  )])
async def channel_unfollow(ctx, channel_id):
  channel_id = int(channel_id)
  channel = client.get_channel(channel_id)
  if channel is None:
    raise BotError("I cannot access the channel with that ID!")
  if not isinstance(channel, discord.TextChannel):
    raise BotError("That is not a text channel!")
  entry = channel_links.query.filter_by(src = channel_id, dest = ctx.channel.id).first()
  if entry:
    channel_links.remove(entry)
    await send_embed(ctx, discord.Embed(
      description = f"No longer following {channel.guild.name}#{channel.name}!"
    ))
  else:
    raise BotError("I am not following this channel!")

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

@slash.slash(name = "link", description = "Link yourself to an external ID", guild_ids = guilds, options = [
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
      description = "Your external id / name",
      option_type = 3,
      required = True
  )])
async def leaderboard(ctx, category, ext_id):
  entry = links.query.filter_by(user = ctx.author.id).first()
  if not entry:
    entry = links.add(user = ctx.author.id)
  setattr(entry, category, ext_id)
  commit()
  await send_embed(ctx, discord.Embed(
    description = f"Linked you to {ext_id} in {link_titles[category]}!"
  ), True)

@slash.slash(name = "unlink", description = "Unlink yourself from an external ID", guild_ids = guilds, options = [
  create_option(
    name = "category",
    description = "The service to unlink from",
    option_type = 3,
    required = True,
    choices = [
      create_choice(name = "league", value = "league")
    ]
  )])
async def leaderboard(ctx, category):
  entry = links.query.filter_by(user = ctx.author.id).first()
  if not entry or getattr(entry, category) == None:
    raise BotError(f"You are not linked with an external ID in {link_titles[category]}!")
  ext_id = getattr(entry, category)
  setattr(entry, category, None)
  commit()
  await send_embed(ctx, discord.Embed(
    description = f"Unlinked you from {ext_id} in {link_titles[category]}!"
  ), True)

@slash.slash(name = "eval", description = "Evaluate Python code", guild_ids = guilds, options = [
  create_option(
    name = "query",
    description = "code to evaluate",
    option_type = 3,
    required = True
  )])
async def run_eval(ctx, query):
  if ctx.author.id != config["bot-owner"]:
    raise BotError("You must be the bot owner to use this command!")
  query = query.strip("`")

  try:
    result = eval(query)
  except:
    await ctx.send("```python\n%s```" % cap(query + "\n\n" + traceback.format_exc().replace("`", "\\`"), 1987))

  if inspect.isawaitable(result):
    try:
      await ctx.send("```python\n%s```" % cap(query + "\n\n" + str(await result).replace("`", "\\`"), 1987))
    except:
      await ctx.send("```python\n%s```" % cap(query + "\n\n" + traceback.format_exc().replace("`", "\\`"), 1987))
  else:
    await ctx.send("```python\n%s```" % cap(query + "\n\n" + str(result).replace("`", "\\`"), 1987))

@slash.slash(name = "query", description = "Make a database query", guild_ids = guilds, options = [
  create_option(
    name = "query",
    description = "SQL query",
    option_type = 3,
    required = True
  )])
async def run_query(ctx, query):
  if ctx.author.id != config["bot-owner"]:
    raise BotError("You must be the bot owner to use this command!")
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
    row = list(row)
    rows.append(row)
    for index in range(len(cwidth)):
      s = str(row[index])
      if s.isdigit():
        user = client.get_user(int(s))
        if user:
          s = f"<{user.name}>"
      cwidth[index] = max(cwidth[index], len(s))
      row[index] = s
  await send_embed(ctx, discord.Embed(
    description = "```" + (" | ".join(key.ljust(width) for key, width in zip(keys, cwidth)) + "\n" + "-" * sum(cwidth) + "---" * (len(cwidth) - 1) + "\n" + "\n".join(" | ".join(str(val).ljust(width) for val, width in zip(row, cwidth)) for row in rows))[:2042] + "```"
  ))

p = [-1, 2, 13, 8, 12, 10, 6, 9, 7, 5, 1, 11, 4, 14, 3, 0]
q = [-1, 14, 9, 0, 13, 11, 8, 5, 7, 2, 6, 4, 10, 3, 1, 12]

@slash.slash(name = "scramble", description = "Scramble", guild_ids = guilds, options = [
  create_option(
    name = "direction",
    description = "Direction",
    option_type = 3,
    required = True,
    choices = [
      create_choice(name = "forward", value = "forward"),
      create_choice(name = "backward", value = "backward")
    ]
  )])
async def scramble(ctx, direction):
  d = [channel.name for channel in list(ctx.guild.text_channels)[:16]]
  k = [d[i + 1] for i in (p if direction == "forward" else q)]
  for c, n in zip(ctx.guild.text_channels, k):
    await c.edit(name = n)
  await ctx.send("OK!", hidden = True)

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
      description = data["sm_api_content"].strip() or "(no content)",
      url = url
    )
    if "sm_api_keyword_array" in data:
      embed.add_field(
        name = "Keywords",
        value = ", ".join(data["sm_api_keyword_array"])
      )
    await send_embed(ctx, embed, True)

async def flatten(iterator, limit):
  output = []
  async for item in iterator:
    output.append(item)
    if len(output) > limit:
      raise BotError(f"Exceeded limit: {limit}")
  return output

@slash.slash(name = "move", description = "Move messages to another channel", guild_ids = guilds, options = [
  create_option(
    name = "selector",
    description = "move after a message ID, or move N messages",
    option_type = 3,
    required = True,
    choices = [
      create_choice(name = "after", value = "after"),
      create_choice(name = "count", value = "count")
    ]
  ),
  create_option(
    name = "selector_value",
    description = "the message ID, or N",
    option_type = 3,
    required = True
  ),
  create_option(
    name = "channel",
    description = "the channel to move to",
    option_type = 7,
    required = True
  ),
  create_option(
    name = "reverse_selector",
    description = "move before a message ID, or skip moving the last N messages",
    option_type = 3,
    required = False,
    choices = [
      create_choice(name = "before", value = "before"),
      create_choice(name = "skip", value = "skip")
    ]
  ),
  create_option(
    name = "reverse_selector_value",
    description = "the message ID, or N",
    option_type = 3,
    required = False
  ),
  create_option(
    name = "threshold",
    description = "the limit; default 500",
    option_type = 4,
    required = False
  )])
async def command_move(ctx, selector, selector_value, channel, reverse_selector = "exclude", reverse_selector_value = 0, threshold = 500):
  if ctx.author.id != config["bot-owner"]:
    raise BotError("Only the bot owner may use this command!")
  await ctx.send("Moving!", hidden = True)
  ch = ctx.channel
  au = ctx.author
  selector_value = int(selector_value)
  reverse_selector_value = int(reverse_selector_value)
  if selector == "after":
    if reverse_selector == "before":
      messages = await flatten(ch.history(after = await ch.fetch_message(selector_value), before = await ch.fetch_message(reverse_selector_value)), threshold)
    else:
      messages = await flatten(ch.history(after = await ch.fetch_message(selector_value)), threshold)
      if reverse_selector_value:
        messages = messages[:-reverse_selector_value]
  else:
    if reverse_selector == "before":
      messages = (await flatten(channel.history(limit = selector_value, before = await ch.fetch_message(reverse_selector_value)), threshold))[::-1]
    else:
      messages = (await flatten(ch.history(limit = selector_value + reverse_selector_value), threshold))[::-1]
      if reverse_selector_value:
        messages = messages[:-reverse_selector_value]
  ct = len(messages)
  prompt = await ch.send(embed = discord.Embed().add_field(
    name = f"Confirm moving {ct} messages to {channel.name}?",
    value = "Enter the number of messages that are being moved to confirm this (10 seconds).",
    inline = False
  ).add_field(
    name = "First message",
    value = to_text(messages[0], refer = True),
    inline = False
  ).add_field(
    name = "Last message",
    value = to_text(messages[-1], refer = True),
    inline = False
  ), delete_after = 13)
  try:
    message = await client.wait_for("message", check = lambda m: m.author == au and m.content == str(ct) and m.channel == ch, timeout = 10)
    await message.delete()
    await prompt.delete()
  except:
    await ch.send("Message move operation cancelled.", delete_after = 3)
    return
  contents = []
  for message in messages:
    txt = to_text(message, refer = True)
    for line in txt.splitlines():
      if contents == []: contents = [""]
      if len(contents[-1] + "\n" + line) > 2000:
        contents.append(line)
      else:
        contents[-1] += "\n" + line
  for content in contents:
    await channel.send(content[:2000])
  for m in messages[::-1]:
    await m.delete()
  await ch.send(f"Moved {len(messages)} message{'' if len(messages) == 1 else 's'}!", delete_after = 5)

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
    await message.channel.send(embed = discord.Embed(description = f"A message from {message.author.mention} was deleted that mentioned {english_list(mentions)}"))

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

@client.reaction_add
async def pin(reaction, user):
  if reaction.emoji == "📌":
    await reaction.message.pin()

@client.reaction_rm
async def unpin(reaction, user):
  if reaction.emoji == "📌":
    await reaction.message.unpin()

@slash.slash(name = "restar", description = "Redo every message in the starboard (in this guild)", guild_ids = guilds)
async def restar(ctx):
  for entry in starlinks.query.filter_by(guild = ctx.guild.id).all():
    src = await client.get_channel(entry.src_channel).fetch_message(entry.src)
    await unstar_message(src)
    await star_message(src)
  await ctx.send(embed = discord.Embed(
    description = "Re-starred all of the messages in this guild!"
  ))

async def star_message(message):
  entry = starboards.query.filter_by(guild_id = message.guild.id).first()
  if entry:
    if starlinks.query.filter_by(src = message.id).count() or starlinks.query.filter_by(dest = message.id).count():
      return
    channel = client.get_channel(entry.channel_id)
    embed = discord.Embed(
      title = f"Sent by {message.author.name} in #{message.channel.name}",
      description = "[Jump to Message](" + message.jump_url + ")\n\n" + message.content,
      color = 0xFFC93A
    )
    if message.reference and message.reference.resolved:
      embed.add_field(
        name = f"Replying to {message.reference.resolved.author.name}",
        value = message.reference.resolved.content
      )
    if message.attachments:
      embed.add_field(
        name = "Attachments",
        value = "\n".join(f"[{attachment.url.split('/')[-1]}]({attachment.url})" for attachment in message.attachments)
      )
    if message.attachments:
      embed.set_image(url = message.attachments[0].url)
    msg = await channel.send(embed = embed)
    starlinks.add(guild = message.guild.id, src_channel = message.channel.id, src = message.id, dest_channel = msg.channel.id, dest = msg.id)

async def unstar_message(message):
  entry = starlinks.query.filter_by(src = message.id).first()
  if entry:
    await (await client.get_channel(entry.dest_channel).fetch_message(entry.dest)).delete()
    starlinks.remove(entry)

@client.reaction_add
async def star(reaction, user):
  if reaction.emoji.name == "⭐":
    await star_message(reaction.message)

@client.reaction_rm
async def unstar(reaction, user):
  if reaction.emoji.name == "⭐":
    await unstar_message(reaction.message)

@client.reaction_clear
async def unstar_prime(reaction):
  await unstar_message(reaction.message)

@slash.slash(name = "kick", description = "Remove a bot from the guild", guild_ids = guilds, options = [
  create_option(
    name = "bot",
    description = "The bot to remove",
    option_type = 6,
    required = True
  )])
async def kick(ctx, member):
  if member.bot:
    await member.kick()
    await send_embed(ctx, discord.Embed(
      description = f"{ctx.author.mention} removed {member.mention} from this guild!"
    ))
  else:
    raise PublicBotError(f"{ctx.author.mention} attempted to kick {member.mention} but they are not a bot!")