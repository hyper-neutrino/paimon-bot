import datetime, discord, edit_distance, requests, traceback

from riotwatcher import LolWatcher, ApiError

from client import *
from display import english_list
from errors import *

watcher = LolWatcher(config["api-keys"]["riot"], timeout = 5)
lol_region = config["league-region"]
lol_version = watcher.data_dragon.versions_for_region(lol_region)["n"]["champion"]

# CHAMPIONS

champs = {}
cmap = {}

champ_list = watcher.data_dragon.champions(lol_version, False, "en_US")["data"]

for key in champ_list:
  row = champ_list[key]
  champs[int(row["key"])] = row["name"]
  cmap[row["id"].lower()] = cmap[row["name"].lower()] = row["id"]

# RUNES

runes = {}

for tree in watcher.data_dragon.runes_reforged(lol_version):
  runes[tree["id"]] = tree
  for slot in tree["slots"]:
    for rune in slot["runes"]:
      runes[rune["id"]] = rune

shard_name = {
  5001: "HP",
  5002: "ARMOR",
  5003: "MR",
  5005: "AS",
  5007: "CDR",
  5008: "AF"
}

# SPELLS

summoner_spells = {}

spell_list = watcher.data_dragon.summoner_spells(lol_version)["data"]

for spell in spell_list.values():
  summoner_spells[spell["key"]] = spell["name"]

# ITEMS

lolitems = watcher.data_dragon.items(lol_version)["data"]

name_map = {}

lower_names = {}

for key in lolitems:
  lk = "".join(lolitems[key]["name"].lower().split())
  lower_names[lk] = {**lolitems[key], "id": key}
  name_map[lk] = lolitems[key]["name"]

def build_path(key, prefix = 0):
  item = lolitems[key]
  output = "|---" * prefix + f"{item['name']} - {item['gold']['total']} {emoji('gold')}" + (f" ({item['gold']['base']} {emoji('gold')})" if item["gold"]["total"] != item["gold"]["base"] else "")
  for sub in item.get("from", []):
    output += "\n" + build_path(sub, prefix + 1)
  return output

def soft_match(a, b):
  for c in a:
    f = b.find(c)
    if f == -1:
      return False
    b = b[f + 1:]
  return True

def find_item(name):
  prefix = []
  suffix = []
  inner = []
  soft = []
  for realname in lower_names:
    if name == realname:
      return lower_names[name]
    if realname.startswith(name):
      prefix.append(realname)
    if realname.endswith(name):
      suffix.append(realname)
    if name in realname:
      inner.append(realname)
    if soft_match(name, realname):
      soft.append(realname)
  if len(prefix) == 0:
    if len(suffix) == 0:
      if len(inner) == 0:
        if len(soft) == 0:
          raise BotError(f"No such item found matching '{name}'!")
        elif len(soft) == 1:
          return lower_names[soft[0]]
        else:
          raise BotError(f"Multiple items found matching '{name}' ({english_list(map(name_map.__getitem__, soft))}); please narrow your search query!")
      elif len(inner) == 1:
        return lower_names[inner[0]]
      else:
        raise BotError(f"Multiple items found containing '{name}' in its name ({english_list(map(name_map.__getitem__, inner))}); please narrow your search query!")
    elif len(suffix) == 1:
      return lower_names[suffix[0]]
    else:
      raise BotError(f"Multiple items found ending with '{name}' ({english_list(map(name_map.__getitem__, suffix))}); please narrow your search query!")
  elif len(prefix) == 1:
    return lower_names[prefix[0]]
  else:
    raise BotError(f"Multiple items found starting with '{name}' ({english_list(map(name_map.__getitem__, prefix))}); please narrow your search query!")

# QUEUES

with open("config/league-queues.json", "r") as f:
  q = json.load(f)

queues = {}

for queue in q:
  queues[queue["queueId"]] = (queue["map"], queue["description"])

# BEGIN FUNCTIONS

def find_position(role, lane):
  if role == "SOLO":
    if lane == "TOP":
      return 0
    return 2
  elif role == "DUO_CARRY":
    return 3
  elif role == "DUO_SUPPORT":
    return 4
  else:
    return 1

async def lol_game_embed(guild, game, skip_remake = False):
  details = watcher.match.by_id(lol_region, game)
  if skip_remake and details["gameDuration"] < 300:
    return "remake"
  pteams = [[None] * 5, [None] * 5]
  pfill = [[], []]
  id_to_name = {}
  for ident in details["participantIdentities"]:
    id_to_name[ident["participantId"]] = ident["player"]["summonerName"]
  for participant in details["participants"]:
    attrs = (
      champs[participant["championId"]],
      id_to_name[participant["participantId"]]
    ) + (
      "/".join(str(participant["stats"][x]) for x in ["kills", "deaths", "assists"]),
      str(participant["stats"]["totalMinionsKilled"] + participant["stats"]["neutralMinionsKilled"]),
      str(participant["stats"]["goldEarned"])
    )
    ii = participant["teamId"] == 200
    index = find_position(participant["timeline"]["role"], participant["timeline"]["lane"])
    if pteams[ii][index] is None:
      pteams[ii][index] = attrs
    else:
      pfill[ii].append(attrs)
  for ii in range(2):
    for i in range(5):
      if pteams[ii][i] is None:
        pteams[ii][i] = pfill[ii].pop()
  players = pteams[0] + pteams[1]
  vicleft = (details["teams"][0]["teamId"] == 100) == (details["teams"][0]["win"] == "Win")
  dmin, dsec = divmod(details["gameDuration"], 60)
  timedisplay = str(dmin) + ":" + str(dsec).zfill(2)
  teams = details["teams"] if details["teams"][0]["teamId"] == 100 else details["teams"][::-1]
  indexes = {team["teamId"]: i for i, team in enumerate(teams)}
  plists = [[] for _ in range(len(teams))]
  for participant in details["participants"]:
    plists[indexes[participant["teamId"]]].append(participant)
  gold = [sum(participant["stats"]["goldEarned"] for participant in plist) for plist in plists]
  embed = discord.Embed(
    title = "Game Report (" + ("%s - %s" % queues.get(details["queueId"], ("Unknown Map", "Unknown Gamemode"))) + ")"
  ).add_field(
    name = "Game Data",
    value = "Patch " + ".".join(details["gameVersion"].split(".")[:2]) + "\n"
      + datetime.datetime.fromtimestamp(details["gameCreation"] / 1000).strftime("%B %d, %Y at %H:%M") + "\n"
      + "Game Duration: " + timedisplay + "\n",
    inline = False
  )
  for i in [0, 1]:
    embed.add_field(
      name = "Team %s - " % (i + 1) + ("Victory" if vicleft ^ bool(i) else "Defeat"),
      value = "/".join(str(sum(participant["stats"][stat] for participant in plists[i])) for stat in ["kills", "deaths", "assists"]) + " - " + str(gold[i]) + " G" + "\n" + "%s " * 10 % sum([(teams[i][x], emoji(y)) for x, y in [("towerKills", "turret"), ("inhibitorKills", "inhibitor"), ("baronKills", "baron_nashor"), ("dragonKills", "drake"), ("riftHeraldKills", "rift_herald")]], ()) + "\n\n" + ("**Bans**\n" + "\n".join(champs.get(ban["championId"], "No Ban") for ban in teams[i]["bans"]) + "\n\n" if teams[i].get("bans") else "") + "**Players**\n" + "\n\n".join(("%s (%s)\n%s - %s CS - %s " + str(emoji("gold", "G"))) % tuple(player) for player in players[i * 5:i * 5 + 5])
    )
  return embed

async def lol_player_embed(guild, game, name, skip_remake = False):
  details = watcher.match.by_id(lol_region, game)
  if skip_remake and details["gameDuration"] < 300:
    return "remake"
  pid = None
  for ident in details["participantIdentities"]:
    if ident["player"]["summonerName"] == name:
      pid = ident["participantId"]
  if not pid:
    raise PublicBotError("The player was not found in this game. This should never happen, so probably contact the developers.")
  for participant in details["participants"]:
    if participant["participantId"] == pid:
      break
  for team in details["teams"]:
    if team["teamId"] == participant["teamId"]:
      break
  sumstat = lambda key: sum(p["stats"][key] for p in details["participants"] if p["teamId"] == team["teamId"])
  stats = participant["stats"]
  CS = stats["totalMinionsKilled"] + stats["neutralMinionsKilled"]
  return discord.Embed(
    title = "Game Report - Detailed Player Report (%s - %s)" % queues.get(details["queueId"], ("Unknown Map", "Unknown Gamemode"))
  ).add_field(
    name = "Build Information",
    value = "__%s__ (lvl %s) - %s\n\n%s __%s__ | %s + %s + %s\n%s %s | %s + %s | %s/%s/%s\n\n%s\n\n%s + %s" % (
      champs.get(participant["championId"], "Unknokwn Champion"),
      stats["champLevel"],
      "Victory" if stats["win"] else "Defeat",
      emoji(runes[stats["perk0"]]["name"].lower().replace(" ", "_"), ""),
      *[runes[stats["perk%d" % i]]["name"] for i in range(4)],
      emoji(runes[stats["perkSubStyle"]]["name"].lower().replace(" ", "_"), ""),
      runes[stats["perkSubStyle"]]["name"],
      *[runes[stats["perk%d" % i]]["name"] for i in range(4, 6)],
      *[shard_name[stats["statPerk%d" % i]] for i in range(3)],
      ", ".join(x["name"] for x in [lolitems.get(str(stats["item%d" % i])) for i in range(7)] if x),
      emoji(summoner_spells[str(participant["spell1Id"])].lower()),
      emoji(summoner_spells[str(participant["spell2Id"])].lower())
    ),
    inline = False
  ).add_field(
    name = "Performance",
    value = "%s/%s/%s - %s CS (%.1f / min) - %s %s - %s%% KP\nVision: %s (Control Wards: %s; Wards Placed: %s; Wards Destroyed: %s)\nCC Score: %s\nKilling Sprees: %s (Largest: %s)\nMultikills: %s × Double, %s × Triple, %s × Quadra, %s × Penta\nLongest time alive: %s:%s" % (
      stats["kills"],
      stats["deaths"],
      stats["assists"],
      CS,
      CS / details["gameDuration"] * 60,
      stats["goldEarned"],
      emoji("gold", "G"),
      int((stats["kills"] + stats["assists"]) * 100 / (sumstat("kills") or 1)),
      stats["visionScore"],
      stats["visionWardsBoughtInGame"],
      stats["wardsPlaced"],
      stats["wardsKilled"],
      stats["timeCCingOthers"],
      stats["killingSprees"],
      stats["largestKillingSpree"],
      stats["doubleKills"],
      stats["tripleKills"],
      stats["quadraKills"],
      stats["pentaKills"],
      stats["longestTimeSpentLiving"] // 60 if stats["longestTimeSpentLiving"] else "--",
      str(stats["longestTimeSpentLiving"] % 60).zfill(2) if stats["longestTimeSpentLiving"] else "--",
    ),
    inline = False
  ).add_field(
    name = "Damage/Healing Stats",
    value = "(Total, Magic, Physical, True)\nTotal Damage: %s (%s%%), %s (%s%%), %s (%s%%), %s (%s%%)\nChampion Damage: %s (%s%%), %s (%s%%), %s (%s%%), %s (%s%%)\nDamage Taken: %s (%s%%), %s (%s%%), %s (%s%%), %s (%s%%)\nDamage to turrets: %s (%s%%)\nDamage to objectives: %s (%s%%)\nSelf-mitigated damage: %s\nHealing done: %s (%s%%)" % (
      *sum([
        (lambda q: [
          stats[q],
          int(stats[q] * 100 / (sumstat(q) or 1))
        ])("magicalDamageTaken" if suff == "Taken" and key == "magicDamage" else key + suff) for suff in ("Dealt", "DealtToChampions", "Taken") for key in ("totalDamage", "magicDamage", "physicalDamage", "trueDamage")
      ], []),
      stats["damageDealtToTurrets"],
      int(stats["damageDealtToTurrets"] * 100 / (sumstat("damageDealtToTurrets") or 1)),
      stats["damageDealtToObjectives"],
      int(stats["damageDealtToObjectives"] * 100 / (sumstat("damageDealtToObjectives") or 1)),
      stats["damageSelfMitigated"],
      stats["totalHeal"],
      int(stats["totalHeal"] * 100 / (sumstat("totalHeal") or 1))
    ),
    inline = False
  ).add_field(
    name = "Timeline",
    value = "First Blood: %s\nFirst Tower: %s\nFirst Inhibitor: %s" % (
      *["✅" if stats.get("first%sKill" % val, False) else "Assisted" if stats.get("first%sAssist" % val, False) else "❌" for val in ["Blood", "Tower", "Inhibitor"]],
    )
  )

async def lol_current_embed(guild, game):
  teams = [[], []]
  bans = game["bannedChampions"]
  for participant in game["participants"]:
    teams[participant["teamId"] // 100 - 1].append(participant)
  dmin, dsec = divmod(game["gameLength"] + 180, 60)
  timedisplay = str(dmin) + ":" + str(dsec).zfill(2)
  embed = discord.Embed(
    title = "Game Report (" + ("%s - %s" % queues.get(game["gameQueueConfigId"], ("Unknown Map", "Unknown Gamemode"))) + ")"
  ).add_field(
    name = "Game Data",
    value = "Patch " + ".".join(lol_version.split(".")[:2]) + "\n"
      + datetime.datetime.fromtimestamp(game["gameStartTime"] / 1000).strftime("%B %d, %Y at %H:%M") + "\n"
      + "Game Duration: " + timedisplay + "\n",
    inline = False
  )
  for i, team in enumerate(teams):
    embed.add_field(
      name = f"Team {i + 1}",
      value = "\n" + (
        "**Bans**\n" + "\n".join(champs.get(ban["championId"], "No Ban") for ban in sorted([b for b in bans if b["teamId"] == (i + 1) * 100], key = lambda x: x["pickTurn"])) + "\n"
        if bans else ""
      ) + "\n**Players**\n" + "\n\n".join(
        "%s (%s)\n%s %s | %s + %s" % (
          champs.get(participant["championId"], "Unknown Champion"),
          participant["summonerName"],
          emoji(runes[participant["perks"]["perkIds"][0]]["name"].lower().replace(" ", "_"), ""),
          emoji(runes[participant["perks"]["perkSubStyle"]]["name"].lower().replace(" ", "_"), ""),
          emoji(summoner_spells[str(participant["spell1Id"])].lower()),
          emoji(summoner_spells[str(participant["spell2Id"])].lower())
        )
        for participant in team
      )
    )
  return embed

async def lol_current_player_embed(guild, game, name):
  dmin, dsec = divmod(game["gameLength"] + 180, 60)
  timedisplay = str(dmin) + ":" + str(dsec).zfill(2)
  embed = discord.Embed(
    title = "Game Report (" + ("%s - %s" % queues.get(game["gameQueueConfigId"], ("Unknown Map", "Unknown Gamemode"))) + ")"
  ).add_field(
    name = "Game Data",
    value = "Patch " + ".".join(lol_version.split(".")[:2]) + "\n"
      + datetime.datetime.fromtimestamp(game["gameStartTime"] / 1000).strftime("%B %d, %Y at %H:%M") + "\n"
      + "Game Duration: " + timedisplay + "\n",
    inline = False
  )
  for participant in game["participants"]:
    if participant["summonerName"].lower() == name.lower():
      embed.add_field(
        name = "%s (%s)" % (champs.get(participant["championId"], "Unknown Champion"), name),
        value = "%s__%s__ | %s + %s + %s\n%s%s | %s + %s | %s/%s/%s\n%s + %s" % (
          emoji(runes[participant["perks"]["perkIds"][0]]["name"].lower().replace(" ", "_"), ""),
          *[runes[participant["perks"]["perkIds"][i]]["name"] for i in range(4)],
          emoji(runes[participant["perks"]["perkSubStyle"]]["name"].lower().replace(" ", "_"), ""),
          runes[participant["perks"]["perkSubStyle"]]["name"],
          *[runes[participant["perks"]["perkIds"][i]]["name"] for i in range(4, 6)],
          *[shard_name[participant["perks"]["perkIds"][i]] for i in range(6, 9)],
          emoji(summoner_spells[str(participant["spell1Id"])].lower()),
          emoji(summoner_spells[str(participant["spell2Id"])].lower())
        ),
        inline = False
      )
      break
  return embed