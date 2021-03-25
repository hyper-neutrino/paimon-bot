import asyncio, traceback

from client import *
from db import *
from display import to_text

@client.event
async def on_message(message):
  if not message.author.bot and message.type == discord.MessageType.default:
    try:
      for entry in channel_links.query.filter_by(src = message.channel.id).all():
        channel = client.get_channel(entry.dest)
        if not channel:
          channel_links.remove(entry)
          continue
        await channel.send(to_text(message, True), allowed_mentions = discord.AllowedMentions.none())
    except:
      traceback.print_exc()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
  client.start(config["discord-token"])
))