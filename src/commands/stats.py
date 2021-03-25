from client import *
from db import *
from errors import *

@slash.slash(name = "sync", description = "Synchronize the entire guild or this channel to the database", guild_ids = guilds, options = [
  create_option(
    name = "scope",
    description = "The scope to synchronize",
    option_type = 3,
    required = True,
    choices = [
      create_choice(name = "guild", value = "guild"),
      create_choice(name = "channel", value = "channel")
    ]
  )])
async def sync(ctx, scope):
  await send_embed(ctx, discord.Embed(
    description = "Synchronization has been initialized. This will take a long time."
  ), True)
  channels = ctx.guild.text_channels if scope == "guild" else [ctx.channel]
  msg = await ctx.channel.send("**SYNC PROGRESS**: 0 messages")
  with db.session.no_autoflush:
    for channel in channels:
      if not isinstance(channel, discord.TextChannel): continue
      total = 0
      await msg.edit(content = f"**SYNC PROGRESS**: {total} messages ({channel.mention})")
      async for message in channel.history(limit = None):
        add_message(message, __no_commit = True)
        total += 1
        if total % 1000 == 0:
          await msg.edit(content = f"**SYNC PROGRESS**: {total} messages ({channel.mention})")
          commit()
      commit()
  commit()
  await msg.delete()
  await send_embed_channel(ctx.channel, discord.Embed(
    description = "Finished synchronizing."
  ), ctx.author)

@slash.subcommand(base = "guild", name = "stats", description = "Display message stats for the whole guild", guild_ids = guilds)
async def guild_stats(ctx):
  await ctx.respond(True)
  await ctx.send(content = "Fetching data; this may take a few seconds!", hidden = True)
  async with ctx.channel.typing():
    by_channel = {}
    by_user = {}
    users = [user.id for user in ctx.guild.members]
    for channel in ctx.guild.text_channels:
      if private_channels.query.filter_by(channel_id = channel.id).count() > 0:
        continue
      by_channel[channel.mention] = 0
      for user in users:
        count = messages.query.filter_by(channel_id = channel.id, author_id = user).count()
        by_channel[channel.mention] += count
        by_user[user] = by_user.get(user, 0) + count
    by_channel = [(a, by_channel[a]) for a in by_channel]
    by_user = [(a, by_user[a]) for a in by_user]
    by_channel.sort(key = lambda x: (-x[1], x[0]))
    by_user.sort(key = lambda x: (-x[1], x[0]))
    chtotal = sum(y for _, y in by_channel)
    ustotal = sum(y for _, y in by_user)
    await send_embed_channel(ctx.channel, discord.Embed(
      title = f"Stats for {ctx.guild.name}"
    ).add_field(
      name = "Channel",
      value = "\n".join(channel for channel, _ in by_channel[:15])
    ).add_field(
      name = "Messages",
      value = "\n".join(f"{x} ({x * 100 / chtotal:.2f}%)" for _, x in by_channel[:15])
    ).add_field(
      name = "By User",
      value = "---",
      inline = False
    ).add_field(
      name = "User",
      value = "\n".join(f"<@{uid}>" for uid, _ in by_user[:15])
    ).add_field(
      name = "Messages",
      value = "\n".join(f"{x} ({x * 100 / ustotal:.2f}%)" for _, x in by_user[:15])
    ), ctx.author)

@slash.subcommand(base = "channel", name = "stats", description = "Display message stats for a channel", guild_ids = guilds, options = [
  create_option(
    name = "channel",
    description = "The channel to show (default: this channel)",
    option_type = 7,
    required = False
  )])
async def channel_stats(ctx, channel = None):
  channel = channel or ctx.channel
  await ctx.respond(True)
  await ctx.send(content = "Fetching data; this may take a few seconds!", hidden = True)
  async with ctx.channel.typing():
    by_user = []
    for user, in db.session.query(messages.author_id).distinct():
      count = messages.query.filter_by(channel_id = channel.id, author_id = user).count()
      if count:
        by_user.append((user, count))
    by_user.sort(key = lambda x: (-x[1], x[0]))
    ustotal = sum(y for _, y in by_user)
    await send_embed_channel(ctx.channel, discord.Embed(
      title = f"Stats for {channel.name}",
      description = f"{ustotal} total messages; {ustotal * 100 / messages.query.filter_by(guild_id = ctx.guild.id).count():.2f}% of the guild"
    ).add_field(
      name = "User",
      value = "\n".join(f"<@{uid}>" for uid, _ in by_user[:15])
    ).add_field(
      name = "Messages",
      value = "\n".join(f"{x} ({x * 100 / ustotal:.2f}%)" for _, x in by_user[:15])
    ), ctx.author)

@slash.subcommand(base = "stats", name = "hide", description = "Hide a channel from stats reports", guild_ids = guilds, options = [
  create_option(
    name = "channel",
    description = "The channel to hide (default: this channel)",
    option_type = 7,
    required = False
  )])
async def channel_hide(ctx, channel = None):
  channel = channel or ctx.channel
  if private_channels.query.filter_by(channel_id = channel.id).count() == 0:
    private_channels.add(channel_id = channel.id)
  await send_embed(ctx, discord.Embed(
    description = f"{channel.mention} has been hidden from stats reports!"
  ), True)

@slash.subcommand(base = "stats", name = "unhide", description = "Unhide a channel from stats reports", guild_ids = guilds, options = [
  create_option(
    name = "channel",
    description = "The channel to unhide (default: this channel)",
    option_type = 7,
    required = False
  )])
async def channel_hide(ctx, channel = None):
  channel = channel or ctx.channel
  entry = private_channels.query.filter_by(channel_id = channel.id).first()
  if entry:
    private_channels.remove(entry)
  await send_embed(ctx, discord.Embed(
    description = f"{channel.mention} has been unhidden from stats reports!"
  ), True)