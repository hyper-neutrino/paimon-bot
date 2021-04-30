from client import *

ch = None

def channel():
  global ch
  if ch is None:
    ch = client.get_channel(831680286617501696)
  return ch

@client.edit_handler
async def log_edit(before, after):
  if before.guild.id != 699314655973212242: return
  if before.channel.id == 831680286617501696: return
  if before.content == after.content: return
  await channel().send(embed = discord.Embed(
    title = "Message Edited",
    description = f"Sent by {before.author.mention} in {before.channel.mention}"
  ).add_field(
    name = "Previously",
    value = before.content,
    inline = False
  ).add_field(
    name = "Currently",
    value = after.content,
    inline = False
  ))

@client.delete_handler
async def log_delete(message):
  if message.guild.id != 699314655973212242: return
  if message.channel.id == 831680286617501696: return
  await channel().send(embed = discord.Embed(
    title = "Message Deleted",
    description = f"Sent by {message.author.mention} in {message.channel.mention}"
  ).add_field(
    name = "Content",
    value = message.content,
    inline = False
  ))