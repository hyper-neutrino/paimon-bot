import discord, json, shlex, sys, time, traceback

from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_choice, create_option
from errors import *

with open("config/config.json", "r") as f:
  config = json.load(f)

class DiscordClient(discord.Client):
  def __init__(self):
    discord.Client.__init__(self, intents = discord.Intents.all())
    self.reaction_handlers = []
    self.message_handlers = []
    self.edit_handlers = []
    self.delete_handlers = []
    self.startup_time = time.time()
    self.reaction_handler = self.reaction_handlers.append
    self.message_handler = self.message_handlers.append
    self.edit_handler = self.edit_handlers.append
    self.delete_handler = self.delete_handlers.append
  
  async def dm(self, user, *a, **k):
    try:
      channel = user.dm_channel
      if channel is None:
        channel = await user.create_dm()
      await channel.send(*a, **k)
    except:
      traceback.print_exc()
  
  async def on_reaction_add(self, reaction, user):
    for handler in self.reaction_handlers:
      await handler(reaction, user)
  
  async def on_reaction_remove(self, reaction, user):
    for handler in self.reaction_handlers:
      await handler(reaction, user)
  
  async def on_message(self, message):
    for handler in self.message_handlers:
      await handler(message)
  
  async def on_message_edit(self, before, after):
    for handler in self.edit_handlers:
      await handler(before, after)
  
  async def on_message_delete(self, message):
    for handler in self.delete_handlers:
      await handler(message)
  
  async def on_ready(self):
    print("PAIMON has started")
  
  async def on_slash_command_error(self, ctx, ex):
    if isinstance(ex, BotError):
      try:
        await ctx.respond(eat = True)
      finally:
        await ctx.send(ex.content, **ex.kwargs, hidden = True)
    elif isinstance(ex, PublicBotError):
      try:
        await ctx.respond()
      finally:
        await send_embed_channel(ctx.channel, discord.Embed(
          title = "Error",
          description = ex.message
        ), ctx.author)
    else:
      try:
        await ctx.respond()
      finally:
        await send_embed_channel(ctx.channel, discord.Embed(
          title = "Uncaught Exception",
          description = f"```{str(ex)[:1994]}```"
        ), ctx.author)
        raise ex

client = DiscordClient()
slash = SlashCommand(client, sync_commands = True)

# guilds = config["slash-command-guilds"]
guilds = None

async def send_embed_channel(channel, embed, author = None, **kwargs):
  return await channel.send(embed = embed.set_footer(text = f"Requested by {author.display_name}", icon_url = author.avatar_url) if author else embed, **kwargs)

async def send_embed(ctx, embed, eat = False, **kwargs):
  try:
    await ctx.respond(eat = eat)
  except:
    pass
  return await ctx.send(embed = embed.set_footer(text = f"Requested by {ctx.author.display_name}", icon_url = ctx.author.avatar_url), **kwargs)

def emoji(name, default = None):
  for guild in client.guilds:
    for emoji in guild.emojis:
      if emoji.name == name:
        return emoji
  if default is None:
    return ":" + name + ":"
  return default