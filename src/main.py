import asyncio, discord, json, re, requests, traceback

with open("../configurations/paimon.json", "r") as f:
    config = json.load(f)

def save():
    with open("../configurations/paimon.json", "w") as f:
        json.dump(config, f, indent = 4)

def safe_eval(regex):
    return eval('"' + regex.replace('"', '\\"') + '"')

class DiscordClient(discord.Client):
    def __init__(self):
        discord.Client.__init__(self, intents = discord.Intents.all())

    async def on_ready(self):
        print("PAIMON has started.")

    async def on_message(self, message):
        if message == "FORCE KILL":
            if message.author.id == self.user.id:
                await message.channel.send("Goodbye, cruel world.")
            exit(0)
        if message.author.id == self.user.id:
            return
        lines = message.content.split("\n")
        if len(lines) == 4 and lines[0] == "WHEN" and lines[2] in ["SEND", "SEND FN MATCH", "SEND FN MSG", "SEND FN BOTH", lines[2] + ".", "DO FN MATCH", "DO FN MSG", "DO FN BOTH"]:
            config["regexes"].append([safe_eval("^" + lines[1] + "$"), lines[3], message.author.id in config["trusted"], ["SEND", "SEND FN MATCH", "SEND FN MSG", "SEND FN BOTH", "", "DO FN MATCH", "DO FN MSG", "DO FN BOTH"].index(lines[2]), message.guild.id])
            save()
            await message.channel.send(f"Added message rule #{len(config['regexes'])}. Enable/disable it with `ENABLE #` / `DISABLE #`." + " Since you are not a trusted user, your rule is currently disabled." * (message.author.id not in config["trusted"]))
        elif message.content == "RULE LIST":
            outputs = []
            for index, (rule, replacement, enabled, type, guild) in enumerate(config["regexes"]):
                outputs.append(f"RULE #{index + 1} ({['dis', 'en'][enabled]}abled):" + "\n" + f"match   : {repr(rule)}" + "\n" + f"replace : {repr(replacement) if type == 0 else replacement}" + "\n" + "type    : " + ["regex substitution", "regex match function", "discord message function", "match + message function", "???", "regex match function (advanced)", "discord message function (advanced)", "match + message function (advanced)"][type] + "\n" + "guild   : " + self.get_guild(guild).name)
            await message.channel.send("```\n" + "\n\n".join(outputs) + "\n```")
        elif re.match(r"(EN|DIS)ABLE \d+", message.content):
            a, b = message.content.split()
            if a == "ENABLE" and message.author.id not in config["trusted"]:
                await message.reply("Only trusted users may enable regex rules.")
            else:
                b = int(b)
                a = a == "ENABLE"
                nr = len(config["regexes"])
                if 0 < b <= nr:
                    config["regexes"][b - 1][2] = a
                    save()
                    await message.channel.send(f"Rule #{b} has been {'en' if a else 'dis'}abled.")
                else:
                    await message.channel.send(f"There is no rule with that ID. There {['are', 'is'][nr == 1]} currently {nr} rule{'s' * (nr != 1)}.")
        for rule, replacement, enabled, type, guild in config["regexes"]:
            if not enabled: continue
            if message.guild.id != guild: continue
            do, type = divmod(type, 4)
            if type == 0:
                r = safe_eval(replacement)
            elif type == 1:
                r = eval(replacement)
            elif type == 2:
                r = lambda match: eval(replacement)(message)
            elif type == 3:
                r = lambda match: eval(replacement)(message, match)
            match = re.match(rule, message.content)
            if match:
                try:
                    if do:
                        await message.channel.send(**r(match))
                    else:
                        await message.channel.send(re.sub(rule, r, message.content))
                except Exception as e:
                    await message.reply(f"Running this command failed: {e}")
                    traceback.print_exc()

client = DiscordClient()

asyncio.get_event_loop().run_until_complete(asyncio.gather(
    client.start(config["discord-token"])
))
