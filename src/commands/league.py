import re, requests, time, traceback

from client import *
from db import *
from riot import *

def summoner_name_by_user(ctx, user):
  summoner_name = get_link(user, "league")
  if summoner_name is None:
    if user.id == ctx.author.id:
      raise BotError("Please link yourself with `/link league` first!")
    else:
      raise PublicBotError(f"{user.mention} is not linked; they will need to link themselves with `/link league` first!")
  return summoner_name

def summoner_by_name(summoner_name):
  try:
    return watcher.summoner.by_name(lol_region, summoner_name)
  except:
    if user.id == ctx.author.id:
      raise BotError(f"Could not find {lol_region.upper()}/{summoner_name}! Please check your spelling and re-link yourself.")
    else:
      raise PublicBotError(f"Could not find {lol_region.upper()}/{summoner_name}! {user.mention} will need to check their spelling and re-link themselves.")

def get_game(summoner, index):
  try:
    return watcher.match.matchlist_by_account(lol_region, summoner["accountId"], end_index = index)["matches"][index - 1]
  except:
    if user.id == ctx.author.id:
      raise BotError("Could not find a valid game! Make sure you have played enough games recently.")
    else:
      raise PublicBotError("Could not find a valid game for {lol_region.upper()}/{summoner_name}! Make sure {user.mention} has played enough games recently.")

user_option = [
  create_option(
    name = "user",
    description = "The user to fetch a game for (default: yourself)",
    option_type = 6,
    required = False
  )
]

name_option = [
  create_option(
    name = "name",
    description = "The name of the summoner to fetch a game for",
    option_type = 3,
    required = True
  )
]

index_option = [
  create_option(
    name = "index",
    description = "The index of the game (1 is the most recent one, default 1)",
    option_type = 4,
    required = False
  )
]

@slash.subcommand(base = "lol", name = "report", description = "Report a game from a user", guild_ids = guilds, options = user_option + index_option)
async def lol_report(ctx, user = None, index = None):
  user = user or ctx.author
  summoner_name = summoner_name_by_user(ctx, user)
  await _lol_report(ctx, summoner_name, index)

@slash.subcommand(base = "lol", name = "name-report", description = "Report a game from a summoner by name", guild_ids = guilds, options = name_option + index_option)
async def lol_name_report(ctx, name, index = None):
  await _lol_report(ctx, name, index)
  
async def _lol_report(ctx, summoner_name, index):
  index = index or 1
  summoner = summoner_by_name(summoner_name)
  game = get_game(summoner, index)
  try:
    await send_embed(ctx, await lol_game_embed(ctx.guild, game["gameId"]), True)
  except:
    traceback.print_exc()
    raise PublicBotError("Error generating the embed! Check console / contact a developer.")

@slash.subcommand(base = "lol", name = "report-player", description = "Report a game from a user (focus on the player details)", guild_ids = guilds, options = user_option + index_option)
async def lol_report_player(ctx, user = None, index = None):
  user = user or ctx.author
  summoner_name = summoner_name_by_user(ctx, user)
  _lol_report_player(ctx, summoner_name, index)

@slash.subcommand(base = "lol", name = "name-report-player", description = "Report a game from a summoner (focus on the player details)", guild_ids = guilds, options = name_option + index_option)
async def lol_name_report_player(ctx, name, index = None):
  await _lol_report_player(ctx, name, index)

async def _lol_report_player(ctx, summoner_name, index):
  index = index or 1
  summoner = summoner_by_name(summoner_name)
  game = get_game(summoner, index)
  try:
    await send_embed(ctx, await lol_player_embed(ctx.guild, game["gameId"], summoner_name), True)
  except:
    traceback.print_exc()
    raise PublicBotError("Error generating the embed! Check console / contact a developer.")

@slash.subcommand(base = "lol", name = "current", description = "Report the user's current game", guild_ids = guilds, options = user_option)
async def lol_current(ctx, user = None):
  user = user or ctx.author
  summoner_name = summoner_name_by_user(ctx, user)
  await _lol_current(ctx, summoner_name)

@slash.subcommand(base = "lol", name = "name-current", description = "Report the summoner's current game", guild_ids = guilds, options = name_option)
async def lol_name_current(ctx, name):
  await _lol_current(ctx, name)

async def _lol_current(ctx, summoner_name):
  summoner = summoner_by_name(summoner_name)
  game = watcher.spectator.by_summoner(lol_region, summoner["id"])
  try:
    await send_embed(ctx, await lol_current_embed(ctx.guild, game), True)
  except:
    traceback.print_exc()
    raise PublicBotError("Error generating the embed! Check console / contact a developer.")

@slash.subcommand(base = "lol", name = "current-player", description = "Report the user's current game (focus on the player details)", guild_ids = guilds, options = user_option)
async def lol_current_player(ctx, user = None):
  user = user or ctx.author
  summoner_name = summoner_name_by_user(ctx, user)
  await _lol_current_player(ctx, summoner_name)

@slash.subcommand(base = "lol", name = "name-current-player", description = "Report the summoner's current game (focus on the player details)", guild_ids = guilds, options = name_option)
async def lol_name_current_player(ctx, name):
  await _lol_current_player(ctx, name)

async def _lol_current_player(ctx, summoner_name):
  summoner = summoner_by_name(summoner_name)
  game = watcher.spectator.by_summoner(lol_region, summoner["id"])
  try:
    await send_embed(ctx, await lol_current_player_embed(ctx.guild, game, summoner_name), True)
  except:
    traceback.print_exc()
    raise PublicBotError("Error generating the embed! Check console / contact a developer.")

@slash.subcommand(base = "lol", name = "ranges", description = "Get info on the ranges for champion(s)", guild_ids = guilds, options = [
  create_option(
    name = "champions",
    description = "Champions, comma-separated",
    option_type = 3,
    required = True
  )])
async def lol_ranges(ctx, champions):
  champs = set()
  for champ in map(str.strip, champions.split(",")):
    champ = champ.lower()
    if champ not in cmap:
      raise BotError(f"{champ} is not a recognized champion name or ID!")
    champs.add(cmap[champ])
  items = []
  for champ in champs:
    data = requests.get(f"http://ddragon.leagueoflegends.com/cdn/{lol_version}/data/en_US/champion/{champ}.json").json()
    items.append((data["data"][champ]["stats"]["attackrange"], data["data"][champ]["name"], "Basic Attack"))
    for i, spell in enumerate(data["data"][champ]["spells"]):
      ident = data["data"][champ]["name"] + " " + ("QWER"[i] if 0 <= i < 4 else "?")
      if len(set(spell["range"])) == 1:
        items.append((spell["range"][0], ident, spell["name"]))
      else:
        clusters = {}
        for i, r in enumerate(spell["range"]):
          if r not in clusters:
            clusters[r] = []
          clusters[r].append(i + 1)
        for key in clusters:
          items.append((key, ident, spell["name"] + " Rank " + "/".join(map(str, clusters[key]))))
  items.sort()
  stacked = []
  for item in items:
    if stacked == [] or item[0] != stacked[-1][0]:
      stacked.append([item[0], []])
    stacked[-1][1].append((item[1], item[2]))
  info = "**Range Analysis**\n"
  for rng, stack in stacked:
    stack = ", ".join(f"{ident} ({name})" for ident, name in stack)
    info += f"\n__{rng}__: {stack}"
  await send_embed(ctx, discord.Embed(
    description = info
  ), True)

@slash.subcommand(base = "lol", name = "item", description = "Get info about a League of Legends item", guild_ids = guilds, options = [
  create_option(
    name = "item_name",
    description = "Item Name",
    option_type = 3,
    required = True
  )])
async def lol_item(ctx, item_name):
  item = find_item("".join(item_name.split()).lower())
  await send_embed(ctx, discord.Embed(
    title = f"League of Legends Item: {item['name']} (#{item['id']})",
    description = re.sub("(\\() (.)|(.) (\\))", "\\1\\2\\3\\4", re.sub(" +", " ", re.sub("<[^>]+?>", "", re.sub("<br>|<li>", "\n", item["description"])))),
    url = f"https://leagueoflegends.fandom.com/wiki/{item['name'].replace(' ', '_')}"
  ).add_field(
    name = "Build Path",
    value = build_path(item["id"]) + ("\n\nBuilds into: " + english_list(lolitems[key]["name"] for key in item.get("into")) if item.get("into") else "")
  ).add_field(
    name = "Tags",
    value = "\n".join("- " + {
      "CriticalStrike": "Critical Strike",
      "NonbootsMovement": "Movement Speed",
      "SpellDamage": "Ability Power",
      "MagicPenetration": "Magic Penetration",
      "ArmorPenetration": "Armor Penetration",
      "SpellBlock": "Magic Resistance",
      "Slow": "Movement Reduction",
      "Jungle": "Jungling",
      "Health": "Health",
      "Lane": "Laning",
      "Aura": "Aura",
      "HealthRegen": "Health Regeneration",
      "SpellVamp": "Spell Vamp",
      "GoldPer": "Gold Income",
      "Mana": "Mana",
      "Vision": "Vision",
      "LifeSteal": "Physical Vamp",
      "Consumable": "Consumable",
      "Armor": "Armor",
      "Stealth": "Stealth",
      "ManaRegen": "Mana Regeneration",
      "OnHit": "On-Hit",
      "Active": "Active",
      "CooldownReduction": "Cooldown Reduction",
      "Trinket": "Trinket",
      "AttackSpeed": "Attack Speed",
      "Boots": "Boots",
      "AbilityHaste": "Ability Haste",
      "Tenacity": "Tenacity",
      "Damage": "Attack Damage"
    }[tag] for tag in item["tags"])
  ).set_thumbnail(
    url = f"http://ddragon.leagueoflegends.com/cdn/{lol_version}/img/item/{item['id']}.png"
  ), True)