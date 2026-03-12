import feedparser
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

rss = "https://feeds.bbci.co.uk/news/world/rss.xml"

feed = feedparser.parse(rss)

news = feed.entries[0]

title = news.title
summary = news.summary

prompt = f"""
次のニュースを日本語でわかりやすく説明してください。

タイトル
{title}

内容
{summary}
"""

response = client.responses.create(
model="gpt-4.1-mini",
input=prompt
)

text = response.output_text

html = f"""
<html>

<head>
<meta charset="UTF-8">
<title>{title}</title>
</head>

<body>

<h1>{title}</h1>

<p>{text}</p>

<a href="../index.html">トップへ戻る</a>

</body>

</html>
"""

os.makedirs("articles",exist_ok=True)

with open("articles/news1.html","w",encoding="utf-8") as f:
    f.write(html)

print("news generated")
