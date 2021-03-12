import asyncio

from client import *
from commands import *

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
  client.start(config["discord-token"]),
  reminder_cycle(),
  genshin_daily()
))