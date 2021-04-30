import asyncio, httpx, img2pdf, os, re, requests

from client import *
from db import *
from errors import *

from io import BytesIO
from PIL import Image
from PyPDF3 import PdfFileMerger

async def get_async(url):
  async with httpx.AsyncClient() as client:
    return await client.get(url)

def nhentai(nhid, force = False):
  entry = doujins.query.filter_by(nhid = nhid).first()
  if force and entry:
    doujins.remove(entry)
    doujin_urls.query.filter_by(nhid = nhid).delete()
    commit()
    entry = None
  if entry:
    return entry, [du.url for du in doujin_urls.query.filter_by(nhid = nhid).order_by(doujin_urls.index.asc()).all()]
  else:
    response = requests.get(f"https://nhentai.net/g/{nhid}")
    if response.status_code == 404:
      raise BotError("404 Not Found!")
    elif response.status_code == 200:
      t = response.text
      urls = {x.replace("t.", "i.", 1).replace("t.", ".") for x in re.findall("https://t\\.nhentai\\.net/galleries/\\d+/\\d+t\\.\\w+", t)}
      urls = sorted(urls, key = lambda s: [int(x) for x in re.findall("\\d+", s)])
      title = re.findall("<span class=\"pretty\">\\s*(.+?)\\s*</span>", t)[0]
      subtitle = re.findall("<span class=\"after\">\\s*(.+?)\\s*</span>", t)[0]
      sauce = int(re.findall("\\d+", urls[0])[0])
      doujin = doujins.add(nhid = nhid, title = title, subtitle = subtitle, sauce = sauce)
      for index, url in enumerate(urls):
        doujin_urls.add(nhid = nhid, index = index, url = url, __no_commit = True)
      commit()
      return doujin, urls
    else:
      raise BotError(f"Unknown error: {response.status_code}")

@client.reaction_handler
async def handle(reaction, user):
  if user == client.user: return
  nh_embed = nhentai_embeds.query.filter_by(message_id = reaction.message.id).first()
  if not nh_embed: return
  doujin, urls = nhentai(nh_embed.nhid)
  pages = len(urls)
  if reaction.emoji == "⬅️":
    page = nh_embed.page - 1
    if page == -1: page = pages - 1
  elif reaction.emoji == "➡️":
    page = nh_embed.page + 1
    if page == pages: page = 0
  else:
    return
  nh_embed.page = page
  commit()
  embed = reaction.message.embeds[0]
  embed.set_image(url = urls[page])
  embed.description = f"Page {page + 1} / {pages}"
  await reaction.message.edit(embed = embed)

@slash.slash(name = "nhentai", description = "Create an embed for an nhentai doujin", guild_ids = guilds, options = [
  create_option(
    name = "nhid",
    description = "The ID / sauce of the doujin",
    option_type = 4,
    required = True
  ),
  create_option(
    name = "force",
    description = "Force reload in case of source edit",
    option_type = 3,
    required = False,
    choices = [
      create_choice(name = "force", value = "force")
    ]
  )])
async def nhentai_embed(ctx, nhid, force = None):
  doujin, urls = nhentai(nhid, force == "force")
  reply = await send_embed(ctx, discord.Embed(
    title = doujin.title + " " + doujin.subtitle,
    url = f"https://nhentai.net/g/{nhid}",
    description = f"Page 1 / {len(urls)}"
  ).set_image(
    url = urls[0]
  ), True)
  await reply.add_reaction("⬅️")
  await reply.add_reaction("➡️")
  nhentai_embeds.add(nhid = nhid, message_id = reply.id, page = 0)

@slash.slash(name = "nhdownload", description = "Download a doujin from nhentai", guild_ids = guilds, options = [
  create_option(
    name = "nhid",
    description = "The ID / sauce of the doujin",
    option_type = 4,
    required = True
  )])
async def nhdownload(ctx, nhid):
  ch = ctx.channel
  await ctx.send("Fetching your doujin! This may take a minute or two.", hidden = True)
  async with ch.typing():
    doujin, urls = nhentai(nhid, True)
    try:
      os.mkdir(f"/tmp/nhentai/{nhid}")
    except:
      pass
    merger = PdfFileMerger()
    responses = await asyncio.gather(*map(get_async, urls))
    for page, r in enumerate(responses):
      pdf_path = f"/tmp/nhentai/{nhid}/{page}.pdf"
      pdf_bytes = img2pdf.convert(r.content)
      with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
      merger.append(pdf_path)
    final_path = f"/tmp/nhentai/{nhid}/final.pdf"
    merger.write(final_path)
    merger.close()
    try:
      with open(final_path, "rb") as f:
        await ch.send(file = discord.File(fp = f, filename = f"[{nhid}] {doujin.title}.pdf"))
    except:
      await send_embed_channel(ch, discord.Embed(
        title = f"[{nhid}] {doujin.title} {doujin.subtitle}",
        url = f"https://nhentai.net/g/{nhid}",
        description = f"The file is too large to upload; you can access it [here](https://dev.hyper-neutrino.xyz/nh/{nhid})"
      ), ctx.author)