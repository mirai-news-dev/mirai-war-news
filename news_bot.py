import feedparser
import os
from openai import OpenAI
import base64
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

rss_list = [
"https://feeds.bbci.co.uk/news/world/rss.xml",
"http://rss.cnn.com/rss/edition_world.rss"
]

entries = []

for url in rss_list:
    feed = feedparser.parse(url)
    entries.extend(feed.entries)

os.makedirs("articles",exist_ok=True)
os.makedirs("images",exist_ok=True)

cards = ""

count = 0

for entry in entries:

    if count >= 10:
        break

    title = entry.title
    summary = entry.summary

# ------------------
# ミライAI解説
# ------------------

    prompt = f"""
次のニュースを
ミライ（新人ニュースキャスター）が
わかりやすく解説してください。

ニュース
{title}

内容
{summary}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    article = response.output_text

# ------------------
# ソウマ解説
# ------------------

    souma_prompt = f"""
次のニュースを
国際情勢アナリストのソウマが
簡潔に解説してください

{title}
"""

    souma = client.responses.create(
        model="gpt-4.1-mini",
        input=souma_prompt
    ).output_text

# ------------------
# 漫画生成
# ------------------

    img = client.images.generate(
        model="gpt-image-1",
        prompt=f"""
4 panel manga
anime style

Mirai
young japanese news caster
long black hair
blue eyes

Souma
handsome analyst
black suit

topic
{title}
""",
        size="1024x1024"
    )

    img_bytes = base64.b64decode(img.data[0].b64_json)

    img_file = f"images/comic{count}.png"

    with open(img_file,"wb") as f:
        f.write(img_bytes)

# ------------------
# 記事生成
# ------------------

    filename = f"articles/news{count}.html"

    html = f"""
<html>

<head>
<meta charset="UTF-8">
<title>{title}</title>
</head>

<body>

<h1>{title}</h1>

<h2>ミライ解説</h2>

<p>{article}</p>

<img src="../{img_file}" width="100%">

<h3>ソウマ分析</h3>

<p>{souma}</p>

<a href="../index.html">トップへ戻る</a>

</body>

</html>
"""

    with open(filename,"w",encoding="utf-8") as f:
        f.write(html)

# ------------------
# トップカード
# ------------------

    cards += f"""

<div class="card">
<a href="{filename}">
<h3>{title}</h3>
</a>
</div>

"""

    count += 1


# ------------------
# index更新
# ------------------

index_html = f"""

<html>

<head>

<meta charset="UTF-8">

<title>戦争と日本経済ニュース｜ミライ解説</title>

<style>

body{{

background:#0f172a;
color:white;
font-family:Arial;
max-width:900px;
margin:auto;
padding:20px;

}}

.card{{

background:#1e293b;
padding:20px;
margin:20px 0;
border-radius:10px;

}}

a{{

color:#38bdf8;
text-decoration:none;

}}

</style>

</head>

<body>

<h1>戦争と日本経済ニュース</h1>

<p>ミライとソウマが世界ニュースを解説</p>

<h2>最新ニュース</h2>

{cards}

</body>

</html>

"""

with open("index.html","w",encoding="utf-8") as f:
    f.write(index_html)

print("site updated")
