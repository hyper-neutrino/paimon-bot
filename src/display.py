def english_list(items):
  items = list(map(str, items))
  if len(items) == 1:
    return items[0]
  elif len(items) == 2:
    return " and ".join(items)
  else:
    return ", ".join(items[:-1]) + ", and " + items[-1]

def time_hm(s):
  s = int(s)
  m, s = divmod(s, 60)
  h, m = divmod(m, 60)
  return str(h) + "h" + str(m).zfill(2)

def cap(string, limit):
  if len(string) > limit:
    return string[:limit - 3] + "..."
  else:
    return string

def to_text(message, refer = False, refer_limit = 200, limit = 2000):
  if message is None:
    return "[something went wrong; message is missing]"
  return cap(("".join("> " + line + "\n" for line in cap(to_text(message.reference.resolved), refer_limit).splitlines()) if refer and message.reference and message.reference.resolved else "") + f"[**{message.author.name}**] {message.content} {''.join('[attached: ' + attachment.url + ']' for attachment in message.attachments)}", limit)