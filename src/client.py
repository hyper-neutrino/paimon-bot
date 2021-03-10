import discord, shlex, sys

from errors import BotError

class DiscordClient(discord.Client):
  def __init__(self):
    discord.Client.__init__(self, intents = discord.Intents.all())
    self.commands = {}
  
  async def on_error(self, event, *args, **kwargs):
    error_type, error, traceback = sys.exc_info()
    if isinstance(error, BotError):
      print(args, kwargs)
  
  def register(self, category, usage, helptext):
    if category:
      if category not in self.commands:
        self.commands[category] = []
      self.commands[category].append(usage, helptext)
  
  def msg_match(self, match, category = "", usage = "", helptext = ""):
    def inner(process):
      self.register(category, usage, helptext)
      @self.event
      async def on_message(message):
        try:
          m = match(message)
        except:
          return
        await process(m)
    
    return inner
  
  def command(self, syntax = [], category = "", usage = "", helptext = "", please = True):
    def inner(process):
      self.register(category, usage, helptext)
      @self.event
      async def on_message(message):
        try:
          arguments = shlex.split(message)
        except:
          return
        if please:
          syntax = [("please", "pls")] + syntax
        for item in syntax:
          if arguments == []:
            return
          if isinstance(item, str) and arguments[0] != item or isinstance(item, tuple) and arguments[0] not in item:
            return
          arguments.pop(0)
        args = []
        kwargs = {}
        keyword = None
        for arg in arguments:
          if arg.endswith(":") and len(arg) > 1:
            if keyword:
              raise BotError(f"Keyword `{keyword}` was not followed by an argument!")
            keyword = arg[:-1]
          else:
            if keyword:
              if keyword in kwargs:
                raise BotError(f"Keyword `{keyword}` received multiple values!")
              kwargs[keyword] = arg
              keyword = None
            else:
              args.append(arg)
        await process(*args, **kwargs)
      
    return inner