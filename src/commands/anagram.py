import math, random

from asyncio.exceptions import TimeoutError
from client import *
from db import anagram_puzzle, commit
from display import *
from errors import BotError
from leaderboard import *

with open("config/words.txt", "r") as f:
  words = f.read().strip().splitlines()

def save():
  with open("config/words.txt", "w") as f:
    f.write("\n".join(words))

def get_puzzle(channel):
  return anagram_puzzle.query.filter_by(channel = channel.id).first()

def set_puzzle(channel, ans, clue, hint):
  puzzle = get_puzzle(channel)
  if puzzle:
    anagram_puzzle.remove(puzzle)
  return anagram_puzzle.add(channel = channel.id, ans = ans, clue = clue, hint = hint)

def new_puzzle(channel):
  choice = random.choice(words)
  charlist = list(choice)
  random.shuffle(charlist)
  clue = "".join(charlist)
  return set_puzzle(channel, choice, clue, 0)

def display_clue(puzzle):
  if puzzle.hint == 0:
    return "_" + puzzle.clue + "_"
  else:
    prefix = puzzle.ans[:puzzle.hint]
    suffix = puzzle.ans[-puzzle.hint:]
    letters = []
    remove = list(prefix + suffix)
    for letter in puzzle.clue:
      if letter in remove:
        remove.remove(letter)
      else:
        letters.append(letter)
    return "_**" + puzzle.ans[:puzzle.hint] + "**" + "".join(letters) + "**" + puzzle.ans[-puzzle.hint:] + "**_"

def get_answers(anagram):
  return set(word for word in words if sorted(word) == sorted(anagram))

def display_answers(puzzle):
  answers = get_answers(puzzle.ans)
  if len(answers) == 1:
    return f"the correct answer was {list(answers)[0]}"
  else:
    return f"the correct answers were {english_list(sorted(answers))}"

@slash.subcommand(base = "anagram", name = "current", description = "Check this channel's anagram puzzle", guild_ids = guilds)
async def anagram(ctx):
  puzzle = get_puzzle(ctx.channel)
  if puzzle:
    await send_embed(ctx, discord.Embed(
      description = f"Current anagram puzzle: solve for {display_clue(puzzle)}"
    ), True)
  else:
    await send_embed(ctx, discord.Embed(
      description = f"There is no anagram puzzle in this channel right now!"
    ), True)

@slash.subcommand(base = "anagram", name = "help", description = "Get info about anagram puzzles", guild_ids = guilds)
async def anagram_help(ctx):
  await send_embed(ctx, discord.Embed(
    title = "Anagram Puzzles",
    description = "by Alexander Liao"
  ).add_field(
    name = "Rules",
    value = "Anagrams are words that have the same characters as each other. For example, \"tops\" and \"spot\" are anagrams. When a puzzle is in a channel, you are to find an English word that is an anagram of the clue (there may be multiple right answers). You can guess by just typing your answer in plaintext.",
    inline = False
  ).add_field(
    name = "Commands",
    value = "- `/anagram current` - check this channel's anagram puzzle\n- `/anagram help` - show this message\n- `/anagram start` - start an anagram puzzle, if one is not present\n- `/anagram stop` - stop this channel's anagrma puzzle, if one is present\n- `/anagram restart` - stop this channel's anagram puzzle, if one is present, then start a new one\n- `/anagram reorder` - reorder the clue\n- `/anagram hint` - reveal one letter from the start and end of the word\n- `/anagram leaderboard` - display the leaderboard (guild-specific)",
    inline = False
  ), True)

@slash.subcommand(base = "anagram", name = "start", description = "Start a new anagram puzzle", guild_ids = guilds)
async def anagram_start(ctx):
  puzzle = get_puzzle(ctx.channel)
  if puzzle:
    await send_embed(ctx, discord.Embed(
      description = f"An anagram puzzle is already active in this channel! Solve for {display_clue(puzzle)}"
    ), True)
  else:
    npuzzle = new_puzzle(ctx.channel)
    await send_embed(ctx, discord.Embed(
      description = f"New anagram puzzle! Solve for {display_clue(npuzzle)}"
    ), True)

@slash.subcommand(base = "anagram", name = "stop", description = "Stop the current anagram puzzle", guild_ids = guilds)
async def anagram_stop(ctx):
  print(ctx)
  puzzle = get_puzzle(ctx.channel)
  if puzzle:
    anagram_puzzle.remove(puzzle)
    await send_embed(ctx, discord.Embed(
      description = f"Stopped the active anagram puzzle ({display_answers(puzzle)})!"
    ), True)
  else:
    await send_embed(ctx, discord.Embed(
      description = f"There is no active anagram puzzle in this channel!"
    ), True)

@slash.subcommand(base = "anagram", name = "restart", description = "Stop the current anagram puzzle (if one exists) and start a new one", guild_ids = guilds)
async def anagram_restart(ctx):
  puzzle = get_puzzle(ctx.channel)
  if puzzle:
    anagram_puzzle.remove(puzzle)
    npuzzle = new_puzzle(ctx.channel)
    await send_embed(ctx, discord.Embed(
      description = f"Stopped the current anagram puzzle ({display_answers(puzzle)})! New puzzle: solve for {display_clue(npuzzle)}"
    ), True)
  else:
    npuzzle = new_puzzle(ctx.channel)
    await send_embed(ctx, discord.Embed(
      description = f"New anagram puzzle! Solve for {display_clue(npuzzle)}"
    ), True)

@slash.subcommand(base = "anagram", name = "reorder", description = "Reorder the clue", guild_ids = guilds)
async def anagram_reorder(ctx):
  puzzle = get_puzzle(ctx.channel)
  if puzzle:
    charlist = list(puzzle.clue)
    random.shuffle(charlist)
    clue = "".join(charlist)
    puzzle = set_puzzle(ctx.channel, puzzle.ans, clue, puzzle.hint)
    await send_embed(ctx, discord.Embed(
      description = f"Reordered: solve for {display_clue(puzzle)}."
    ), True)
  else:
    await send_embed(ctx, discord.Embed(
      description = f"There is no active anagram puzzle in this channel!"
    ), True)

@slash.subcommand(base = "anagram", name = "hint", description = "Reveal one letter from the start and end of the word", guild_ids = guilds)
async def anagram_hint(ctx):
  puzzle = get_puzzle(ctx.channel)
  if puzzle:
    if len(puzzle.ans) - 2 * (puzzle.hint + 1) <= 1:
      await send_embed(ctx, discord.Embed(
        description = f"Too many hints; the answer has been revealed: {display_answers(puzzle)}."
      ))
      anagram_puzzle.remove(puzzle)
    else:
      puzzle = set_puzzle(ctx.channel, puzzle.ans, puzzle.clue, puzzle.hint + 1)
      await send_embed(ctx, discord.Embed(
        description = f"Hint: solve for {display_clue(puzzle)}."
      ))
  else:
    await send_embed(ctx, discord.Embed(
      description = f"There is no active anagram puzzle in this channel!"
    ), True)

@client.message_handler
async def on_message(message):
  puzzle = get_puzzle(message.channel)
  if not puzzle:
    return
  if message.content in words and sorted(message.content) == sorted(puzzle.ans):
    other_answers = get_answers(puzzle.ans) - {message.content}
    x = len(puzzle.ans) - 2 * puzzle.hint
    points = int(round(math.e ** x / 10000 + x ** 2 / 50 - x / 5 + 3))
    add_score(message.author, "anagram", points)
    anagram_puzzle.remove(puzzle)
    npuzzle = new_puzzle(message.channel)
    await message.channel.send(embed = discord.Embed(
      description = f"Congratulations to {message.author.mention} for solving the anagram puzzle (+{points}){' (other answers: ' + ', '.join(sorted(other_answers)) + ')' if other_answers else ''}! New puzzle: solve for {display_clue(npuzzle)}"
    ))
    def check(m):
      return m.channel == message.channel and m.content in words and sorted(message.content) == sorted(puzzle.ans)
    try:
      m = await client.wait_for("message", check = check, timeout = 1)
      await m.reply("L", mention_author = False)
    except TimeoutError:
      pass