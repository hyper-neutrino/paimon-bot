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
  h, m = divmod(m, 24)
  return str(h) + "h" + str(m).zfill(2)