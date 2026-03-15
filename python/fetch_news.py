import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser

"""
fetch_news_step6.py

目的:
- RSSからニュース候補を集める
- あとでAI要約しやすい形のJSONにする
- 初心者でも修正しやすいようにコメント多め

今の段階では:
- RSSを取得する
- タイトル / リンク / 要約 / 公開日 を保存する
- 日本への影響カテゴリを手動で付けやすい形にする

あとで追加する機能:
- AIで本文要約
- 会話形式の記事生成
- HTML自動生成と連携
"""

# ========================================
# 1) 基本設定
# ========================================

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "rss_articles_raw.json"

# 取得したいRSS
# まずは世界ニュース系を少数から始めるのがおすすめ
RSS_FEEDS = [
    {
        "name": "BBC World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "world"
    },
    {
        "name": "BBC Business",
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "category": "economy"
    },
    {
        "name": "Reuters World News",
        "url": "https://feeds.reuters.com/Reuters/worldNews",
        "category": "world"
    }
]

# 1つのRSSから何件取るか
MAX_ITEMS_PER_FEED = 5


# ========================================
# 2) 便利関数
# ========================================

def now_jst_str() -> str:
    """保存日時を文字列で返す"""
    jst = timezone.utc
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S UTC")


def clean_text(text: str) -> str:
    """改行や余分な空白を整理する"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)  # HTMLタグ削除
    text = re.sub(r"\s+", " ", text).strip()
    return text


def guess_japan_impact_tags(title: str, summary: str) -> list[str]:
    """
    タイトルと要約から、日本への影響タグの候補をざっくり付ける
    完璧ではないので、あとで手動修正前提
    """
    text = f"{title} {summary}".lower()
    tags = []

    keyword_map = {
        "エネルギー価格": ["oil", "gas", "energy", "crude", "lng", "opec"],
        "輸入物価": ["inflation", "prices", "food", "wheat", "grain", "shipping"],
        "為替": ["yen", "dollar", "currency", "fx", "exchange"],
        "半導体": ["semiconductor", "chip", "taiwan", "tsmc"],
        "物流": ["shipping", "port", "red sea", "supply chain"],
        "防衛": ["war", "military", "missile", "defense", "security"],
        "災害": ["earthquake", "flood", "wildfire", "storm", "hurricane", "disaster"],
    }

    for tag, words in keyword_map.items():
        for word in words:
            if word in text:
                tags.append(tag)
                break

    if not tags:
        tags.append("日本への影響を確認")
    return tags


def entry_to_article(feed_name: str, feed_category: str, entry) -> dict:
    """RSSの1件をJSON用の辞書に変換"""
    title = clean_text(getattr(entry, "title", ""))
    link = getattr(entry, "link", "")
    summary = clean_text(getattr(entry, "summary", "")) or clean_text(getattr(entry, "description", ""))
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")

    source_domain = urlparse(link).netloc if link else ""

    return {
        "title": title,
        "link": link,
        "summary": summary,
        "published": published,
        "source_name": feed_name,
        "source_domain": source_domain,
        "topic_category": feed_category,
        "japan_impact_tags": guess_japan_impact_tags(title, summary),
        # ここは後で手動 or AIで埋める想定
        "japan_impact_memo": "",
        "status": "candidate"
    }


# ========================================
# 3) RSS取得
# ========================================

def fetch_feed(feed_info: dict) -> list[dict]:
    """1つのRSSから記事候補を取得"""
    name = feed_info["name"]
    url = feed_info["url"]
    category = feed_info["category"]

    print(f"取得中: {name}")
    parsed = feedparser.parse(url)

    if getattr(parsed, "bozo", 0):
        print(f"  注意: RSSの読み込みで警告がありました -> {url}")

    articles = []
    for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
        article = entry_to_article(name, category, entry)
        if article["title"] and article["link"]:
            articles.append(article)

    print(f"  取得件数: {len(articles)}")
    return articles


# ========================================
# 4) 保存
# ========================================

def save_articles(articles: list[dict], output_file: Path) -> None:
    """JSONとして保存"""
    data = {
        "site_theme": "世界の戦争・経済・災害ニュースが日本に与える影響をやさしく解説する",
        "fetched_at": now_jst_str(),
        "count": len(articles),
        "articles": articles
    }

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n保存完了: {output_file}")
    print(f"記事数: {len(articles)}")


# ========================================
# 5) 実行
# ========================================

def main():
    all_articles = []

    for feed in RSS_FEEDS:
        try:
            articles = fetch_feed(feed)
            all_articles.extend(articles)
        except Exception as e:
            print(f"エラー: {feed['name']} の取得に失敗しました -> {e}")

    # 同じリンクを除外
    unique_articles = []
    seen_links = set()

    for article in all_articles:
        if article["link"] not in seen_links:
            unique_articles.append(article)
            seen_links.add(article["link"])

    save_articles(unique_articles, OUTPUT_FILE)

    print("\n次の作業:")
    print("1. data/rss_articles_raw.json を開く")
    print("2. japan_impact_memo を手動で少し埋める")
    print("3. 次の段階で AI 要約スクリプトにつなぐ")


if __name__ == "__main__":
    main()
