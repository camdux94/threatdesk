import os
import json
import requests
from datetime import datetime
from anthropic import Anthropic

client = Anthropic()

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")

CATEGORIES = {
    "identity_kyc": {
        "label": "Identity & KYC",
        "emoji": "🔍",
        "query": "identity fraud KYC verification news 2026"
    },
    "payment_fraud": {
        "label": "Payment Fraud",
        "emoji": "💳",
        "query": "payment fraud chargeback card fraud news 2026"
    },
    "business_fraud": {
        "label": "Business Fraud & KYB",
        "emoji": "🏢",
        "query": "business fraud KYB shell company fraud news 2026"
    },
    "account_takeover": {
        "label": "Account Takeover",
        "emoji": "🔐",
        "query": "account takeover credential stuffing SIM swap news 2026"
    },
    "regulatory": {
        "label": "Regulatory & Compliance",
        "emoji": "⚖️",
        "query": "fraud regulation FTC AML compliance enforcement news 2026"
    },
    "trust_safety": {
        "label": "Trust & Safety",
        "emoji": "🌐",
        "query": "trust safety platform abuse bot fraud news 2026"
    }
}

TREND_KEYWORDS = [
    "identity theft",
    "account takeover",
    "synthetic identity",
    "chargeback fraud",
    "deepfake fraud"
]


def search_news(query):
    url = "https://google.serper.dev/news"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5}
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        return data.get("news", [])
    except Exception as e:
        print(f"Search error: {e}")
        return []


def summarize_category(label, articles):
    if not articles:
        return {"summary": "No recent news found for this category.", "severity": "LOW"}

    articles_text = ""
    for i, article in enumerate(articles[:5], 1):
        articles_text += f"{i}. {article.get('title', '')} - {article.get('snippet', '')}\n"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": f"""You are a fraud intelligence analyst. Summarize these {label} news articles into a concise 2-3 sentence brief for a fraud analyst. Focus on key threats, trends, and actionable insights. Be direct and professional.

Articles:
{articles_text}

Then assign a severity level based on the threat landscape: HIGH, MEDIUM, or LOW.

Respond in this exact format:
SUMMARY: [your 2-3 sentence summary]
SEVERITY: [HIGH, MEDIUM, or LOW]"""
        }]
    )

    text = message.content[0].text
    summary = text
    severity = "MEDIUM"

    if "SEVERITY:" in text:
        parts = text.split("SEVERITY:")
        summary = parts[0].replace("SUMMARY:", "").strip()
        severity = parts[1].strip().upper()
        if severity not in ["HIGH", "MEDIUM", "LOW"]:
            severity = "MEDIUM"

    return {"summary": summary, "severity": severity}


def get_trends():
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360)
        results = []
        for keyword in TREND_KEYWORDS:
            try:
                pytrends.build_payload([keyword], timeframe='now 7-d')
                data = pytrends.interest_over_time()
                if not data.empty:
                    avg = int(data[keyword].mean())
                    results.append({"keyword": keyword, "score": avg})
            except:
                results.append({"keyword": keyword, "score": 0})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    except Exception as e:
        print(f"Trends error: {e}")
        return []


def get_top_story(categories_data):
    all_articles = []
    for cat in categories_data:
        for article in cat.get("articles", []):
            article["category"] = cat["label"]
            article["emoji"] = cat["emoji"]
            all_articles.append(article)
    return all_articles[0] if all_articles else None


def run_agent():
    print("ThreatDesk agent starting...")
    output = {
        "generated_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "categories": [],
        "trends": [],
        "top_story": None
    }

    for key, cat in CATEGORIES.items():
        print(f"Fetching {cat['label']}...")
        articles = search_news(cat["query"])
        result = summarize_category(cat["label"], articles)
        output["categories"].append({
            "key": key,
            "label": cat["label"],
            "emoji": cat["emoji"],
            "summary": result["summary"],
            "severity": result["severity"],
            "articles": [
                {
                    "title": a.get("title", ""),
                    "link": a.get("link", ""),
                    "source": a.get("source", ""),
                    "snippet": a.get("snippet", "")
                }
                for a in articles[:5]
            ]
        })

    print("Fetching trends...")
    output["trends"] = get_trends()
    output["top_story"] = get_top_story(output["categories"])

    os.makedirs("data", exist_ok=True)
    with open("data/digest.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Done! Digest saved to data/digest.json")


if __name__ == "__main__":
    run_agent()