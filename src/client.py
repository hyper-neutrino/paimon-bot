import discord, json, shlex, sys, time, traceback

from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_choice, create_option
from errors import *

with open("config/config.json", "r") as f:
  config = json.load(f)

class FakeReaction:
  def __init__(self, emoji, message):
    self.emoji = emoji
    self.message = message

  async def create(payload, emoji = -1):
    return FakeReaction(payload.emoji if emoji == -1 else emoji, await client.get_channel(payload.channel_id).fetch_message(payload.message_id))

class DiscordClient(discord.Client):
  def __init__(self):
    discord.Client.__init__(self, intents = discord.Intents.all())
    self.reaction_add_handlers = []
    self.reaction_rm_handlers = []
    self.reaction_clear_handlers = []
    self.message_handlers = []
    self.edit_handlers = []
    self.delete_handlers = []
    self.startup_time = time.time()
    self.reaction_handler = lambda x: [self.reaction_add_handlers.append(x), self.reaction_rm_handlers.append(x)]
    self.reaction_add = self.reaction_add_handlers.append
    self.reaction_rm = self.reaction_rm_handlers.append
    self.reaction_clear = self.reaction_clear_handlers.append
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

  async def on_raw_reaction_add(self, payload):
    for handler in self.reaction_add_handlers:
      await handler(await FakeReaction.create(payload), self.get_user(payload.user_id))

  async def on_raw_reaction_remove(self, payload):
    for handler in self.reaction_rm_handlers:
      await handler(await FakeReaction.create(payload), self.get_user(payload.user_id))

  async def on_raw_reaction_clear_emoji(self, payload):
    for handler in self.reaction_rm_handlers:
      await handler(await FakeReaction.create(payload), self.get_user(payload.user_id))

  async def on_raw_reaction_clear(self, payload):
    for handler in self.reaction_clear_handlers:
      await handler(await FakeReaction.create(payload, None))

  async def on_message(self, message):
    for handler in self.message_handlers:
      await handler(message)

  async def on_message_edit(self, before, after):
    for handler in self.edit_handlers:
      await handler(before, after)

  async def on_message_delete(self, message):
    for handler in self.delete_handlers:
      await handler(message)

  async def on_bulk_message_delete(self, messages):
    for message in messages:
      await self.on_message_delete(message)

  async def on_ready(self):
    print("PAIMON has started")

  async def on_slash_command_error(self, ctx, ex):
    if isinstance(ex, BotError):
      await ctx.send(ex.content, **ex.kwargs, hidden = True)
    elif isinstance(ex, PublicBotError):
      await send_embed_channel(ctx.channel, discord.Embed(
        title = "Error",
        description = ex.message
      ), ctx.author)
    else:
      await send_embed_channel(ctx.channel, discord.Embed(
        title = "Uncaught Exception",
        description = f"```{str(ex)[:1994]}```"
      ), ctx.author)
      raise ex

client = DiscordClient()
slash = SlashCommand(client, sync_commands = True, delete_from_unused_guilds = True)

guilds = []
# guilds = config["slash-command-guilds"]
# guilds = None

async def send_embed_channel(channel, embed, author = None, **kwargs):
  return await channel.send(embed = embed.set_footer(text = f"Requested by {author.display_name}", icon_url = author.avatar_url) if author else embed, **kwargs)

# eat param only included for backwards compatibility; it doesn't do anything anymore
async def send_embed(ctx, embed, eat = False, **kwargs):
  return await ctx.send(embed = embed.set_footer(text = f"Requested by {ctx.author.display_name}", icon_url = ctx.author.avatar_url), **kwargs)

def emoji(name, default = None):
  for emoji in client.emojis:
    if emoji.name == name:
      return emoji
  if default is None:
    raise PublicBotError(f"Emoji not found: :{name}:. If this is supposed to exist, contact a developer.")
  return default
