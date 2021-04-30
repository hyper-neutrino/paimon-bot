import asyncio, discord, html

from client import *

from chatbot import *

channels = {
  1  : 831366152571322418,
  240: 831366130316345354
}

def handler(room):
  def _inner(activity):
    if "e" in activity: e = activity["e"]
    else: return
    for x in e:
      if x["event_type"] == 1 and x["room_id"] == room:
        client.loop.create_task(client.get_channel(channels[room]).send(html.unescape(f"**{x['user_name']}** [{x['message_id']}]: {x['content'].replace('@hyper-neutrino', '<@251082987360223233>')}")))
  return _inner

chatbot = Chatbot()
chatbot.login()

rooms = {
  k  : chatbot.joinRoom(k, handler(k))
for k in [1, 240]}

@client.message_handler
async def receive(message):
  if message.channel.id == 831366152571322418 and message.author.id == 251082987360223233:
    rooms[1].sendMessage(message.content)
    await message.delete(delay = 5)
  if message.channel.id == 831366130316345354 and message.author.id == 251082987360223233:
    rooms[240].sendMessage(message.content)
    await message.delete(delay = 5)