import time

from client import *
from db import *
from display import *

@slash.slash(name = "uptime", description = "Check how long I have been running for", guild_ids = guilds)
async def uptime(ctx):
  seconds = int(time.time() - client.startup_time)
  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  days, hours = divmod(hours, 24)
  
  components = []
  
  if days:
    components.append(f"{days} day{'' if days == 1 else 's'}")
  if hours:
    components.append(f"{hours} hour{'' if hours == 1 else 's'}")
  if minutes:
    components.append(f"{minutes} minute{'' if minutes == 1 else 's'}")
  if seconds:
    components.append(f"{seconds} second{'' if seconds == 1 else 's'}")
    
  if len(components) == 1:
    message = components[0]
  elif len(components) == 2:
    message = " and ".join(components)
  else:
    message = ", ".join(components[:-1]) + ", and " + components[-1]
    
  await send_embed(ctx, discord.Embed(description = f"I have been running for {message}!"))

@slash.subcommand(base = "user", name = "info", description = "Get info on a guild member (default: yourself)", guild_ids = guilds, options = [create_option(name = "user", description = "The user to investigate", option_type = 6, required = False)])
async def user_info(ctx, user = None):
  user = user or ctx.author
  await send_embed(ctx, discord.Embed(
    title = f"{user.name}#{user.discriminator}" + (" (BOT)" if user.bot else ""),
    description = user.nick or ""
  ).add_field(
    name = "Joined",
    value = user.joined_at.strftime("%B %d, %Y at %H:%M:%S"),
    inline = False
  ).add_field(
    name = "User since",
    value = user.created_at.strftime("%B %d, %Y at %H:%M:%S"),
    inline = False
  ).add_field(
    name = "Messages sent",
    value = str(messages.query.filter_by(guild_id = ctx.guild.id, author_id = user.id).count()),
    inline = False
  ).add_field(
    name = "ID",
    value = str(user.id),
    inline = False
  ).set_thumbnail(
    url = user.avatar_url
  ))

@slash.subcommand(base = "channel", name = "info", description = "Get info on a channel (default: this channel)", guild_ids = guilds, options = [create_option(name = "channel", description = "The channel to investigate", option_type = 7, required = False)])
async def channel_info(ctx, channel = None):
  channel = channel or ctx.channel
  embed = discord.Embed(
    title = channel.name,
    description = (channel.topic or "") + ("\n\n_This is the guild's system messages channel_" if channel == channel.guild.system_channel else "") if isinstance(channel, discord.TextChannel) else "_This is a channel category_" if isinstance(channel, discord.CategoryChannel) else "_This is the guild's AFK voice channel_" if channel == channel.guild.afk_channel else "_This is a voice channel_" if isinstance(channel, discord.VoiceChannel) else ""
  ).add_field(
    name = "Created",
    value = channel.created_at.strftime("%B %d, %Y at %H:%M:%S"),
    inline = False
  )
  
  if not isinstance(channel, discord.CategoryChannel):
    embed.add_field(
      name = "Category",
      value = channel.category.name if channel.category else "(None)",
      inline = False
    )
  
  if isinstance(channel, discord.TextChannel):
    embed.add_field(
      name = "Users",
      value = ", ".join(member.mention for member in channel.members if not member.bot),
      inline = False
    ).add_field(
      name = "Messages",
      value = str(messages.query.filter_by(channel_id = channel.id).count()),
      inline = False
    )
    
    if channel.slowmode_delay:
      embed.add_field(
        name = "Slowmode Delay",
        value = str(channel.slowmode_delay),
        inline = False
      )
  
  embed.add_field(
    name = "ID",
    value = str(channel.id),
    inline = False
  )
  
  await send_embed(ctx, embed)

@slash.subcommand(base = "guild", name = "info", description = "Get info on this guild", guild_ids = guilds)
async def guild_infp(ctx):
  guild = ctx.guild
  real_members = [member for member in guild.members if not member.bot]
  bot_members = [member for member in guild.members if member.bot]
  await send_embed(ctx, discord.Embed(
    title = guild.name,
    description = guild.description or ""
  ).add_field(
    name = "Created",
    value = guild.created_at.strftime("%B %d, %Y at %H:%M:%S"),
    inline = False
  ).add_field(
    name = "Members",
    value = f"{len(real_members) + len(bot_members)} ({len(real_members)} users, {len(bot_members)} bots)",
    inline = False
  ).set_thumbnail(
    url = guild.icon_url
  ))