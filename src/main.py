import asyncio, json

from client import DiscordClient

client = DiscordClient()

from commands import *

with open("config/config.json", "r") as f:
  config = json.load(f)

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
  client.start(config["discord-token"])
))