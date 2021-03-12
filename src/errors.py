class BotError(RuntimeError):
  def __init__(self, content, **kwargs):
    self.content = content
    self.kwargs = kwargs

class PublicBotError(RuntimeError):
  def __init__(self, message):
    self.message = message