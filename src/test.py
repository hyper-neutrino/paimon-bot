import requests, re

r = requests.get("https://play.google.com/store/apps/details?id=com.miHoYo.GenshinImpact")

stars = re.search("Rated (\\S+) stars out of five stars", r.text).group(1)

ratings = list(map(int, re.findall("mMF0fd.+?(\\d+)%", r.text)[1:]))
s = sum(ratings)
ratings = [r * 100 // s for r in ratings]

print(f"""Genshin Impact: {stars} stars.

5*: {ratings[0]}%
4*: {ratings[1]}%
3*: {ratings[2]}%
2*: {ratings[3]}%
1*: {ratings[4]}%
""")
