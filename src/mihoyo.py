import json, datetime, re

from client import *
from display import *

# with open("config/genshin.json", "r") as f:
#   genshin_data = json.load(f)

genshin_data = {}

def emojilist(key, count, sep = None):
  a = [emoji(key + str(i)) for i in range(1, count + 1)]
  if sep is None:
    return a
  return sep.join(map(str, a))

def charfield(characters):
  return {
    "name": "Characters",
    "value": "\n".join("- " + str(emoji("traveler" if cid.endswith("_mc") else cid)) + " " + cdata["name"] for cid, cdata in characters) or "N/A",
    "inline": False
  }

def charfilter(field, value):
  return [(cid, cdata) for cid, cdata in genshin_data["characters"].items() if cdata[field] == value]

def enemydropfilter(id, type, group = False):
  return [(eid, edata) for eid, edata in genshin_data["enemy_groups" if group else "enemies"].items() if "drops" in edata and {"id": id, "type": type} in edata["drops"]]

def char_reacts(characters):
  return [emoji("traveler" if cid.endswith("_mc") else cid) for cid, _ in characters]

def enemy_reacts(enemies):
  return [emoji(edata["emoji"]) for _, edata in enemies]

def name_item(item, type):
  if type == "ascension_gems":
    return genshin_data["elements"][item] + " Ascension Gem (" + genshin_data["ascension_gems"][item] + ")"
  elif type == "elemental_materials":
    return genshin_data["elemental_materials"][item]["name"]
  elif type == "general_ascension":
    return genshin_data["general_ascension"][item]["category_name"]
  elif type == "regional_specialties":
    return genshin_data["regional_specialties"][item]["name"]
  elif type == "artifacts":
    data = genshin_data["artifacts"][item]
    return data["set_name"] + f" (Artifact Set)"
  elif type == "talent_boss":
    return genshin_data["talent_boss"][item]["name"]
  else:
    return item + " [" + type + "]"

def emoji_item(item, type):
  if type == "ascension_gems":
    return item + "_chunk"
  elif type == "elemental_materials":
    return item
  elif type == "general_ascension":
    return item + "3"
  elif type == "regional_specialties":
    return item
  elif type == "artifacts":
    return item
  elif type == "talent_boss":
    return item
  else:
    return "[??]"

def query(category, day, region):
  for key, value in genshin_data[category].items():
    if day in value["days"] and region == value["region"]:
      return (key, value)
  return ("null", {})

rome_numerals = {
  "M": 1000,
  "CM": 900,
  "D": 500,
  "CD": 400,
  "C": 100,
  "XC": 90,
  "L": 50,
  "XL": 40,
  "X": 10,
  "IX": 9,
  "V": 5,
  "IV": 4,
  "I": 1
}

def roman(n):
  if n == 0: return ""
  if n < 0: return "-" + roman(-n)
  for k in rome_numerals:
    if rome_numerals[k] <= n:
      return k + roman(n - rome_numerals[k])

def daily_embed(key):
  if key == 6:
    return discord.Embed(
      title = "Sunday",
      description = "**All talent books and weapon ascension materials** are available for farming today; you may select the reward type you want before entering each Domain of Mastery and Forgery. If you wish to get details about these items, run `/genshin info`."
    ), []
  else:
    embed = discord.Embed(
      title = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][key],
      description = "It is the weekly reset, so all bosses (Stormterror, Wolf of the North, Tartaglia) are available again." if key == 0 else ""
    )
    el = []
    for region in genshin_data["regions"]:
      tid, tval = query("talent_books", key, region)
      wid, wval = query("weapon_ascension", key, region)
      el.append(emoji(f"{tid}2"))
      el.append(emoji(f"{wid}3"))
      te = [str(emoji(f"{tid}{i}")) for i in range(1, 4)]
      we = [str(emoji(f"{wid}{i}")) for i in range(1, 5)]
      embed.add_field(
        name = genshin_data["regions"][region]["name"],
        value = f"- {tval['category_name']} ({''.join(te)})" + "\n" +
                f"- {wval['category_name']} ({''.join(we)})" + "\n",
        inline = False
      )
    return embed, el

def info_embed(name):
  months = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
  weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
  for key, value in enumerate(weekdays):
    if value.lower() == name:
      return daily_embed(key)
  if name == "today":
    n = datetime.datetime.now()
    return daily_embed((n.weekday() - (n.hour < 4)) % 7)
  for key, value in genshin_data["talent_books"].items():
    if re.match(key + "\\d?$", name):
      chars = [k for k in genshin_data["characters"] if genshin_data["characters"][k].get("talent_book") == key]
      if value["region"] == "mondstadt":
        chars.append("anemo_mc")
      elif value["region"] == "liyue":
        chars.append("geo_mc")
      return discord.Embed(
        title = value["category_name"],
        description = f"{value['category_name']} can be farmed from {genshin_data['domains'][value['source']]['name']} in {genshin_data['regions'][value['region']]['name']} on {english_list(weekdays[x] for x in value['days'])}."
      ).add_field(
        name = "Items",
        value = f"- {emoji(key + '1')} Teachings of {value['name']}" + "\n" +
                f"- {emoji(key + '2')} Guide to {value['name']}" + "\n" +
                f"- {emoji(key + '3')} Philosophies of {value['name']}",
        inline = False
      ).add_field(
        **charfield([(k, genshin_data["characters"][k]) for k in chars])
      ).set_thumbnail(url = emoji(key + "2").url), [emoji(value["region"])] + [emoji("traveler" if "_mc" in k else k) for k in chars]
  for key, value in genshin_data["weapon_ascension"].items():
    if re.match(key + "\\d?$", name):
      return discord.Embed(
        title = value["category_name"],
        description = f"{value['category_name']} can be farmed from {genshin_data['domains'][value['source']]['name']} in {genshin_data['regions'][value['region']]['name']} on {english_list(weekdays[x] for x in value['days'])}."
      ).add_field(
        name = "Items",
        value = "\n".join(f"- {emoji(key + str(i + 1))} {value['names'][i]}" for i in range(4))
      ).set_thumbnail(url = emoji(key + "3").url), [emoji(value["region"])]
  for key, value in genshin_data["characters"].items():
    if key == name:
      return discord.Embed(
        title = value["name"],
        description = value["title"]
      ).add_field(
        name = "Element",
        value = genshin_data["elements"][value["element"]] + " " + str(emoji(value["element"]))
      ).add_field(
        name = "Weapon",
        value = genshin_data["weapon_types"][value["weapon"]] + " " + str(emoji(value["weapon"]))
      ).add_field(
        name = "Rarity",
        value = "⭐" * value["tier"]
      ).add_field(
        name = "Region",
        value = genshin_data["regions"][value["region"]]["name"] + " " + str(emoji(value["region"]))
      ).add_field(
        name = "Birthday",
        value = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][value["birthmonth"]] + " " + str(value["birthdate"])
      ).add_field(
        name = "Constellation",
        value = value["constellation"]
      ).add_field(
        name = "HP",
        value = str(value["stats"]["hp"])
      ).add_field(
        name = "ATK",
        value = str(value["stats"]["atk"])
      ).add_field(
        name = "DEF",
        value = str(value["stats"]["def"])
      ).add_field(
        name = value["stats"]["secondary_stat"],
        value = str(value["stats"]["secondary"]) + ("%" if value["stats"]["secondary_stat"] != "Elemental Mastery" else "")
      ).add_field(
        name = "Character Ascension Materials",
        value = "- " + genshin_data["elements"][value["element"]] + " Gem (" + genshin_data["ascension_gems"][value["element"]] + ") (" + "".join(str(emoji(value["element"] + k)) for k in ["_sliver", "_fragment", "_chunk", "_gemstone"]) + ")\n" +
                "- " + genshin_data["elemental_materials"][value["boss_drop"]]["name"] + " (" + str(emoji(value["boss_drop"])) + ")\n" +
                "- " + genshin_data["regional_specialties"][value["specialty"]]["name"] + " (" + str(emoji(value["specialty"])) + ")\n" +
                "- " + genshin_data["general_ascension"][value["ascension"]]["category_name"] + " (" + emojilist(value["ascension"], 3, "") + ")" + "\n",
        inline = False
      ).add_field(
        name = "Talent Ascension Materials",
        value = "- " + genshin_data["talent_books"][value["talent_book"]]["category_name"] + " (" + emojilist(value["talent_book"], 3, "") + ")" + "\n" +
                "- " + genshin_data["general_ascension"][value["talent_common"]]["category_name"] + " (" + emojilist(value["talent_common"], 3, "") + ")" + "\n" +
                "- " + genshin_data["talent_boss"][value["weekly"]]["name"] + "(" + str(emoji(value["weekly"])) + ")",
        inline = False
      ).set_thumbnail(url = emoji(key).url), [emoji(value["region"]), emoji(value["element"]), emoji(value["weapon"]), emoji(value["element"] + "_chunk"), emoji(value["boss_drop"]), emoji(value["specialty"]), emoji(value["talent_book"] + "2"), emoji(value["talent_common"] + "3"), emoji(value["ascension"] + "3"), emoji(value["weekly"])]
  for key, value in genshin_data["elements"].items():
    if key == name:
      characters = charfilter("element", key)
      regions = [(rid, rdata) for rid, rdata in genshin_data["regions"].items() if rdata["element"] == key]
      return discord.Embed(
        title = value,
        description = ""
      ).add_field(
        name = "Region",
        value = "\n".join(rdata["name"] for _, rdata in regions) or "N/A"
      ).add_field(
        **charfield(characters)
      ).add_field(
        name = "Ascension Gem",
        value = genshin_data["ascension_gems"][key] + " Sliver (" + str(emoji(key + "_sliver")) + ") / Fragment (" + str(emoji(key + "_fragment")) + ") / Chunk (" + str(emoji(key + "_chunk")) + ") / Gemstone (" + str(emoji(key + "_gemstone")) + ")",
        inline = False
      ).set_thumbnail(url = emoji(key).url), [emoji(rid) for rid, _ in regions] + [emoji(key + "_chunk")] + char_reacts(characters)
  for key, value in genshin_data["weapon_types"].items():
    if key == name:
      characters = charfilter("weapon", key)
      return discord.Embed(
        title = value,
        description = ""
      ).add_field(
        **charfield(characters)
      ).set_thumbnail(url = emoji(key).url), char_reacts(characters)
  for key, value in genshin_data["elements"].items():
    for suffix in ["_sliver", "_fragment", "_chunk", "_gemstone"]:
      if key + suffix == name:
        class_name = genshin_data["ascension_gems"][key]
        characters = charfilter("element", key)
        return discord.Embed(
          title = value + " Ascension Gem (" + class_name + ")",
          description = ""
        ).add_field(
          name = "Items",
          value = "\n".join("- " + str(emoji(key + suffix)) + " " + class_name + " " + suffname for suffix, suffname in [("_sliver", "Sliver"), ("_fragment", "Fragment"), ("_chunk", "Chunk"), ("_gemstone", "Gemstone")])
        ).add_field(
          **charfield(characters)
        ).set_thumbnail(url = emoji(key + "_chunk").url), [emoji(key)] + char_reacts(characters)
  for key, value in genshin_data["elemental_materials"].items():
    if key == name:
      characters = charfilter("boss_drop", key)
      return discord.Embed(
        title = value["name"] + " (Normal Boss Material)",
        description = value["name"] + " can be obtained from the " + value["boss"]
      ).add_field(
        **charfield(characters)
      ).set_thumbnail(url = emoji(key).url), char_reacts(characters)
  for key, value in genshin_data["domains"].items():
    if key == name:
      embed = discord.Embed(
        title = value["name"],
        description = ""
      ).add_field(
        name = "Region",
        value = genshin_data["regions"][value["region"]]["name"] + " " + str(emoji(value["region"]))
      ).add_field(
        name = "Type",
        value = genshin_data["domain_types"][value["type"]]
      )
      er = []
      if value["type"] == "mastery":
        embed.add_field(
          name = "Drops",
          value = "\n".join("- [" + days + "] " + genshin_data["talent_books"][item]["category_name"] + " (" + emojilist(item, 3, "") + ")" for days, item in zip(["Mon/Thu/Sun", "Tue/Fri/Sun", "Wed/Sat/Sun"], value["drops"])),
          inline = False
        )
        er.extend(item + "2" for item in value["drops"])
      elif value["type"] == "forgery":
        embed.add_field(
          name = "Drops",
          value = "\n".join("- [" + days + "] " + genshin_data["weapon_ascension"][item]["category_name"] + " (" + emojilist(item, 4, "") + ")" for days, item in zip(["Mon/Thu/Sun", "Tue/Fri/Sun", "Wed/Sat/Sun"], value["drops"])),
          inline = False
        )
        er.extend(item + "3" for item in value["drops"])
      elif value["type"] == "blessing":
        embed.add_field(
          name = "Drops",
          value = "\n".join(f"- {emoji(id)} {name_item(id, 'artifacts')}" for id in value["drops"]),
          inline = False
        )
        er.extend(value["drops"])
      eg = []
      for i, tier in enumerate(value["tiers"]):
        embed.add_field(
          name = f"{value['name']} {roman(i + 1)}",
          value = "__" + tier["objective"] + "__ " + tier["disorder"] + "\n" + "\n".join(f"**Wave {j + 1}**: " + ", ".join(str(emoji(edata["emoji"])) + " " + edata["name"] + " x " + str(count) for edata, count in [(genshin_data["enemies"][cluster["enemy"]], cluster["count"]) for cluster in wave]) for j, wave in enumerate(tier["waves"])),
          inline = False
        )
        for wave in tier["waves"]:
          for cluster in wave:
            group = genshin_data["enemies"][cluster["enemy"]]["group"]
            if group not in eg:
              eg.append(group)
      return embed, [emoji(value["region"])] + [emoji(e) for e in er] + [emoji(genshin_data["enemy_groups"][g]["emoji"]) for g in eg]
  for key, value in genshin_data["regions"].items():
    if key == name:
      return discord.Embed(
        title = value["name"],
        description = ""
      ).add_field(
        name = "Element",
        value = genshin_data["elements"][value["element"]] + " " + str(emoji(value["element"]))
      ).add_field(
        name = "Archon",
        value = value["archon"]
      ).add_field(
        name = "Governing Entity",
        value = value["government"]
      ).add_field(
        name = "Domains",
        value = "\n".join("- " + genshin_data["domain_types"][ddata["type"]] + ": " + ddata["name"] for did, ddata in genshin_data["domains"].items() if ddata["region"] == key)
      ).set_thumbnail(url = emoji(key).url), [emoji(value["element"])]
  for key, value in genshin_data["general_ascension"].items():
    if re.match(key + "\\d?$", name):
      characters = charfilter("talent_common", key)
      for q in charfilter("ascension", key):
        if q not in characters:
          characters.append(q)
      groups = enemydropfilter(key, "general_ascension", True)
      enemies = enemydropfilter(key, "general_ascension")
      return discord.Embed(
        title = value["category_name"],
        description = ""
      ).add_field(
        name = "Items",
        value = "\n".join("- " + str(emoji(key + str(i + 1))) + " " + value["tiers"][i] for i in range(3))
      ).add_field(
        **charfield(characters)
      ).add_field(
        name = "Enemies",
        value = "\n".join(["- " + str(emoji(gdata["emoji"])) + " " + gdata["name"] + " (Group)" for gid, gdata in groups] + ["- " + str(emoji(edata["emoji"])) + " " + edata["name"] for eid, edata in enemies])
      ).set_thumbnail(url = emoji(key + "3").url), char_reacts(characters) + enemy_reacts(groups + enemies)
  for key, value in genshin_data["enemy_emoji_map"].items():
    if re.match(key + "$", name):
      id = value["id"]
      if value["group"]:
        group = genshin_data["enemy_groups"][id]
        embed = discord.Embed(
          title = group["name"] + " (Group)",
          description = ""
        )
        drops = group["drops"]
      else:
        enemy = genshin_data["enemies"][value["id"]]
        group = genshin_data["enemy_groups"][enemy["group"]]
        embed = discord.Embed(
          title = enemy["name"],
          description = ""
        ).add_field(
          name = "Group",
          value = group["name"]
        )
        drops = enemy.get("drops", []) + group.get("drops", [])
      embed = embed.add_field(
        name = "Faction",
        value = genshin_data["enemy_factions"][group["faction"]]
      ).add_field(
        name = "Tier",
        value = genshin_data["enemy_tiers"][group["type"]]
      ).add_field(
        name = "Drops",
        value = "\n".join("- " + str(emoji(emoji_item(drop["id"], drop["type"]))) + " " + name_item(drop["id"], drop["type"]) for drop in drops),
        inline = False
      )
      if value["group"]:
        embed = embed.add_field(
          name = "Enemies",
          value = "\n".join("- " + str(emoji(edata["emoji"])) + " " + edata["name"] for _, edata in genshin_data["enemies"].items() if edata["group"] == id),
          inline = False
        )
      try:
        embed.set_thumbnail(url = emoji(name).url)
      except:
        pass
      return embed, [emoji(emoji_item(drop["id"], drop["type"])) for drop in drops]
  for key, value in genshin_data["talent_boss"].items():
    if key == name:
      characters = charfilter("weekly", key)
      return discord.Embed(
        title = name_item(key, "talent_boss"),
        description = genshin_data["enemies"][genshin_data["talent_boss"][key]["boss"]]["name"]
      ).add_field(
        **charfield(characters)
      ).set_thumbnail(url = emoji(key).url), [emoji(genshin_data["talent_boss"][key]["boss"])] + char_reacts(characters)
  for key, value in genshin_data["artifacts"].items():
    if key == name:
      # TODO domain emojis
      sources = [("", val["name"]) for dkey, val in genshin_data["domains"].items() if key in val["drops"]] + \
                [(emoji(val["emoji"]), val["name"]) for ekey, val in genshin_data["enemies"].items() if {"id": key, "type": "artifacts"} in val.get("drops", [])] + \
                [(emoji(val["emoji"]), val["name"]) for gkey, val in genshin_data["enemy_groups"].items() if {"id": key, "type": "artifacts"} in val.get("drops", [])]
      return discord.Embed(
        title = value["set_name"] + " (Artifact Set)",
        description = "⭐" * value["min_tier"] + " - " + "⭐" * value["max_tier"]
      ).add_field(
        name = "Artifact Names",
        value = "\n".join("- " + name for name in value["names"].values() if name),
        inline = False
      ).add_field(
        name = "Set Bonuses",
        value = "\n".join(f"{i}-piece bonus: {k}" for i, k in enumerate(value["set"]) if k) or "N/A",
        inline = False
      ).add_field(
        name = "Sources",
        value = "\n".join(f"- {emoji} {name}" for emoji, name in sources),
        inline = False
      ).set_thumbnail(url = emoji(key).url), [se for se, _ in sources if se]
  for key, value in genshin_data["regional_specialties"].items():
    if key == name:
      characters = charfilter("specialty", key)
      return discord.Embed(
        title = value["name"],
        description = "Regional Specialty"
      ).add_field(
        name = "Region",
        value = genshin_data["regions"][value["region"]]["name"]
      ).add_field(
        **charfield(characters)
      ).set_thumbnail(url = emoji(key).url), [emoji(value["region"])] + char_reacts(characters)
  for key, value in genshin_data["weapons"].items():
    if key == name:
      embed = discord.Embed(
        title = value["name"],
        description = ""
      ).add_field(
        name = "Type",
        value = genshin_data["weapon_types"][value["type"]] + " " + str(emoji(value["type"]))
      ).add_field(
        name = "Rarity",
        value = "⭐" * value["tier"]
      ).add_field(
        name = "Series",
        value = value["series"]
      ).add_field(
        name = "Sources",
        value = ", ".join(value["sources"]) or "N/A"
      ).add_field(
        name = "Max Level",
        value = "90/90" if value["tier"] >= 3 else "70/70"
      ).add_field(
        name = "Base ATK",
        value = value["base_atk"]
      )
      if value["tier"] >= 3:
        embed = embed.add_field(
          name = value["secondary_type"],
          value = str(value["secondary_stat"]) + ("%" if value["secondary_type"] != "Elemental Mastery" else "")
        ).add_field(
          name = value["passive_name"],
          value = value["passive"],
          inline = False
        )
      embed = embed.add_field(
        name = "Weapon Ascension Materials",
        value = "- " + genshin_data["weapon_ascension"][value["ascension"]]["category_name"] + " (" + emojilist(value["ascension"], 4, "") + ")\n" +
                "- " + genshin_data["general_ascension"][value["material_1"]]["category_name"] + " (" + emojilist(value["material_1"], 3, "") + ")\n" +
                "- " + genshin_data["general_ascension"][value["material_2"]]["category_name"] + " (" + emojilist(value["material_2"], 3, "") + ")" + "\n",
        inline = False
      )
      return embed.set_thumbnail(url = emoji(key).url), [emoji(value["type"]), emoji(value["ascension"] + "3"), emoji(value["material_1"] + "3"), emoji(value["material_2"] + "3")]