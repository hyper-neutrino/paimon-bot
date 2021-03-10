from main import client

@client.command(["test"])
async def test(a, *b):
  print(a, b)