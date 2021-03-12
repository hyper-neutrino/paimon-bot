import asyncio, datetime, time

from client import *
from db import *
from errors import *
from mihoyo import *

async def send_info(channel, item, author):
  value = info_embed(item.replace(" ", "_"))
  if value:
    embed, emojis = value
    message = await send_embed_channel(channel, embed, author)
    genshin_embeds.add(message_id = message.id)
    for emoji in emojis:
      await message.add_reaction(emoji)
  else:
    raise BotError(f"No entry found named `{item}`!")

@slash.subcommand(base = "genshin", name = "info", description = "Get info on an item (enter internal ID, lowercase + underscores)", guild_ids = guilds, options = [
  create_option(
    name = "item",
    description = "The ID of the item. Ask a developer if you're not sure.",
    option_type = 3,
    required = True
  )])
async def genshin_info(ctx, item):
  await ctx.respond(True)
  await send_info(ctx.channel, item, ctx.author)

@slash.subcommand(base = "genshin", name = "watch", description = "Watch/unwatch genshin impact updates in this channel", guild_ids = guilds, options = [
  create_option(
    name = "watch",
    description = "Watch on / off",
    option_type = 5,
    required = False
  )])
async def genshin_watch(ctx, watch = True):
  entry = watch_channels.query.filter_by(channel_id = ctx.channel.id).first()
  if entry:
    entry.genshin = watch
    commit()
  else:
    entry = watch_channels.add(channel_id = ctx.channel.id, genshin = watch)
  await send_embed(ctx, discord.Embed(
    description = ("Now" if watch else "No longer") + " watching Genshin Impact updates in this channel!"
  ), True)

@slash.subcommand(base = "genshin", name = "resin", description = "Set your resin amount, set a reminder, or check your current resin", guild_ids = guilds, options = [
  create_option(
    name = "operation",
    description = "Whether to set, reminder, or check your resin",
    option_type = 3,
    required = True,
    choices = [
      create_choice(name = "set", value = "set"),
      create_choice(name = "remind", value = "remind"),
      create_choice(name = "now", value = "now")
    ]
  ),
  create_option(
    name = "value",
    description = "Your current resin / when to remind",
    option_type = 4,
    required = False
  )])
async def command_genshin_resin(ctx, operation, value = None):
  if operation == "set":
    entry = genshin_resin.query.filter_by(user_id = ctx.author.id).first()
    if value is None:
      if entry:
        genshin_resin.remove(entry)
      await ctx.respond(True)
      await ctx.send("Cleared your resin data including any present reminders!", hidden = True)
    elif 0 <= value <= 160:
      new_time = time.time() - 8 * 60 * value
      if entry:
        entry.time = new_time
        commit()
      else:
        entry = genshin_resin.add(user_id = ctx.author.id, time = new_time)
      reminder_message = ""
      if entry.reminder:
        reminder_message = f" Your existing reminder for {entry.reminder} resin will happen in {time_hm(new_time + 8 * 60 * entry.reminder - time.time())}."
      await ctx.respond(True)
      await ctx.send(f"Set your resin data to {value} resin!" + reminder_message, hidden = True)
    else:
      raise BotError("Resin must be in the range [0, 160]!")
  elif operation == "remind":
    entry = genshin_resin.query.filter_by(user_id = ctx.author.id).first()
    if entry:
      await ctx.respond(True)
      if value is None:
        entry.reminder = 0
        await ctx.send("Cleared your resin reminder!", hidden = True)
      elif 0 <= value <= 160:
        if entry.time + 8 * 60 * value <= time.time():
          raise BotError("You already have at least that much resin!")
        entry.reminder = value
        await ctx.send(f"I will remind you when you reach {value} resin (in {time_hm(entry.time + 8 * 60 * entry.reminder - time.time())})!", hidden = True)
      else:
        raise BotError("Resin must be in the range [0, 160]!")
      commit()
    else:
      raise BotError("You haven't told me how much resin you have yet!")
  elif operation == "now":
    entry = genshin_resin.query.filter_by(user_id = ctx.author.id).first()
    if entry:
      await ctx.respond(True)
      await ctx.send(f"You currently have {min(int((time.time() - entry.time) / 60 / 8), 160)} resin!" + (f" I will remind you when you reach {entry.reminder} resin (in {time_hm(entry.time + 8 * 60 * entry.reminder - time.time())})." if entry.reminder else ""), hidden = True)

@client.reaction_handler
async def handle(reaction, user):
  if user == client.user: return
  if genshin_embeds.query.filter_by(message_id = reaction.message.id).count() == 0: return
  try:
    name = reaction.emoji.name
  except:
    return
  try:
    await send_info(reaction.message.channel, name, user)
  except BotError:
    pass
  except Exception as e:
    await send_embed_channel(reaction.message.channel, discord.Embed(
      title = f"Exception in Genshin Info: {reaction.emoji.name}",
      description = f"```{e}```"
    ), user)

async def genshin_daily():
  await asyncio.sleep(5)
  while True:
    n = datetime.datetime.now()
    if n.hour >= 4:
      for entry in watch_channels.query.filter_by(genshin = True).all():
        watch_time = n.year * 12 * 31 + n.month * 31 + n.day
        watch_entry = last_genshin_remind.query.filter_by(channel_id = entry.channel_id).first() or last_genshin_remind.add(channel_id = entry.channel_id)
        if watch_entry.last_remind < watch_time:
          watch_entry.last_remind = watch_time
          commit()
          channel = client.get_channel(entry.channel_id)
          try:
            wd = n.weekday()
            await send_info(channel, "today", client.user)
          except BotError as e:
            await channel.send(e.message)
          except:
            await channel.send("Critical exception occurred. Check console.")
            print(traceback.format_exc())
    await asyncio.sleep(5)

async def reminder_cycle():
  await asyncio.sleep(5)
  while True:
    for entry in genshin_resin.query.all():
      if entry.reminder and (time.time() - entry.time) / 8 / 60 >= entry.reminder:
        await client.dm(client.get_user(entry.user_id), f"You have reached {entry.reminder} resin!" + " (nice)" * (entry.reminder == 69))
        entry.reminder = None
        commit()
    await asyncio.sleep(5)