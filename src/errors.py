class BotError(RuntimeError):
  def __init__(self, content, **kwargs):
    self.content = content
    self.kwargs = kwargs