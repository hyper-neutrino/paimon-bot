import asyncio

from client import *
from db import *

@client.event
async def on_message(message):
  add_message(message)

@client.event
async def on_raw_message_delete(payload):
  rm_message(payload.message_id)

@client.event
async def on_raw_bulk_message_delete(payload):
  for mid in payload.message_ids:
    rm_message(mid)

@client.event
async def on_raw_message_edit(payload):
  add_message(await client.get_channel(payload.channel_id).fetch_message(payload.message_id))

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
  client.start(config["discord-token"])
))