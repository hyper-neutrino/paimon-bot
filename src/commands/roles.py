import re

from client import *
from errors import BotError

# @slash.subcommand(base = "role", name = "add", description = "Grant a role to a user", guild_ids = guilds, options = [create_option(name = "user", description = "The user to target", option_type = 6, required = True), create_option(name = "role", description = "The role to grant", option_type = 8, required = True)])
# async def role_add(ctx, user, role):
#   if role in user.roles:
#     await send_embed(ctx, discord.Embed(description = f"{user.mention} already has {role.mention}!"), True)
#     return
#   try:
#     await user.add_roles(role)
#     await send_embed(ctx, discord.Embed(description = f"{user.mention} has been granted {role.mention}!"), True)
#   except:
#     await send_embed(ctx, discord.Embed(description = f"Could not grant {role.mention} to {user.mention}! Make sure I have the permission level to do so."), True)

# @slash.subcommand(base = "role", name = "remove", description = "Remove a role from a user", guild_ids = guilds, options = [create_option(name = "user", description = "The user to target", option_type = 6, required = True), create_option(name = "role", description = "The role to remove", option_type = 8, required = True)])
# async def role_remove(ctx, user, role):
#   if role not in user.roles:
#     await send_embed(ctx, discord.Embed(description = f"{user.mention} does not have {role.mention}!"), True)
#     return
#   try:
#     await user.remove_roles(role)
#     await send_embed(ctx,  discord.Embed(description = f"Removed {role.mention} from {user.mention}!"), True)
#   except:
#     await send_embed(ctx, discord.Embed(description = f"Could not remove {role.mention} from {user.mention}! Make sure I have the permission level to do so."), True)

@slash.subcommand(base = "role", name = "color", description = "Set a role's color (or remove it)", guild_ids = guilds, options = [create_option(name = "role", description = "The role to target", option_type = 8, required = True), create_option(name = "color", description = "The color to assign (leave blank to fetch) (supports hex-code, discord default colors, random, none)", option_type = 3, required = False)])
async def role_color(ctx, role, color = None):
  if color == None:
    await send_embed(ctx, discord.Embed(
      description = f"{role.mention}'s color is {hex(role.color.r)[2:].zfill(2)}{hex(role.color.g)[2:].zfill(2)}{hex(role.color.b)[2:].zfill(2)}"
    ), True)
    return
  if color == "none":
    color = 0
  elif color == "random":
    color = discord.Color.random()
  elif color in "teal dark_teal green dark_green blue dark_blue purple dark_purple magenta dark_magenta gold dark_gold orange dark_orange red dark_red lighter_grey lighter_gray dark_grey dark_gray light_grey light_gray darker_grey darker_gray blurple greyple dark_theme".split():
    color = getattr(discord.Color, color)()
  elif re.match(r"[A-Za-z0-9]{6}", color):
    rgb = int(color, 16)
    color = discord.Color.from_rgb((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)
  else:
    raise BotError("Not a recognized color! Please enter the ID of a discord built-in color, the hex-code of a color, `random`, or leave it blank")
  await role.edit(color = color)
  await send_embed(ctx, discord.Embed(
    description = f"Updated {role.mention}'s color!"
  ), True)

@slash.subcommand(base = "role", name = "rename", description = "Set a role's name", guild_ids = guilds, options = [create_option(name = "role", description = "The role to target", option_type = 8, required = True), create_option(name = "name", description = "The name to set it to", option_type = 3, required = True)])
async def role_rename(ctx, role, name):
  await role.edit(name = name)
  await send_embed(ctx, discord.Embed(
    description = f"Updated {role.mention}'s name!"
  ), True)