from googleapiclient.discovery import build
import base64
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from newspaper import Article


def get_gmail_service():
    from gmail_connect import get_gmail_service
    return get_gmail_service()


def extract_titles_and_links(html_content, sender):
    """Extracts article titles and links from HTML emails."""
    soup = BeautifulSoup(html_content, "html.parser")
    articles = []

    if "dataelixir" in sender:
        for h2 in soup.find_all("h2"):
            title = h2.get_text(strip=True)
            a_tag = h2.find("a")  # Get the link inside <h2>
            link = a_tag["href"] if a_tag else None
            articles.append({"title": title, "link": link})

    elif "datascienceweekly" in sender:
        sections_of_interest = ["Editor's Picks", "Data Science Articles & Videos"]
        for h2 in soup.find_all("h2"):
            if h2.get_text(strip=True) in sections_of_interest:
                ul = h2.find_next("ul")
                if ul:
                    for li in ul.find_all("li"):
                        strong_tag = li.find("strong")
                        a_tag = li.find("a")  # Extract URL
                        title = strong_tag.get_text(strip=True) if strong_tag else "Untitled"
                        link = a_tag["href"] if a_tag else None
                        articles.append({"title": title, "link": link})

    return articles


def fetch_article_text(url):
    """Fetches the main content from an article URL."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text[:1000]  # Limit to 1000 characters to keep summaries short
    except Exception as e:
        print(f"Failed to extract article: {e}")
        return None


def save_article(newsletter_type, title, url, summary):
    """Stores article data in SQLite to prevent redundant scraping."""
    conn = sqlite3.connect("newsletters.db")
    cursor = conn.cursor()


    cursor.execute("INSERT OR REPLACE INTO articles (newsletter_type, title, url, summary) VALUES (?, ?, ?)",
                   (newsletter_type, title, url, summary))

    conn.commit()
    conn.close()


def get_cached_summary(url):
    """Checks if an article summary is already stored in SQLite."""
    conn = sqlite3.connect("newsletters.db")
    cursor = conn.cursor()
    cursor.execute("SELECT summary FROM articles WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def search_newsletters(newsletter_type=None):
    service = get_gmail_service()

    # Calculate the start of the week (7 days ago)
    last_week_date = (datetime.now() - timedelta(weeks=1)).strftime('%Y/%m/%d')

    query = ''
    if newsletter_type == 'datascienceweekly':
        query = f'from:(datascienceweekly@substack.com) after:{last_week_date}'
    elif newsletter_type == 'dataelixir':
        query = f'from:(lon@dataelixir.com) after:{last_week_date}'
    else:
        query = f'(from:(datascienceweekly@substack.com) OR from:(lon@dataelixir.com)) after:{last_week_date}'

    results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No newsletters found.")
        return []

    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = msg_data['payload']

        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "").lower()

        # Extract email content
        if "data" in payload.get("body", {}):
            body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        elif "parts" in payload:
            html_content = next((base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8")
                                 for p in payload["parts"] if p.get("mimeType") == "text/html"), "")
            articles = extract_titles_and_links(html_content, sender) if html_content else []
        else:
            articles = []

        # Fetch & Store article summaries
        for article in articles:
            title, url = article["title"], article["link"]
            if url:
                cached_summary = get_cached_summary(url)
                if not cached_summary:
                    summary = fetch_article_text(url)
                    if summary:
                        save_article(newsletter_type, title, url, summary)
                    else:
                        summary = "Could not fetch summary. Going to work on this right now. Sorry 🥲\n\n ⚠️ Please consider that if the article leads to an online course or a YouTube video, then I can't summarize it. ⚠️"
                else:
                    summary = cached_summary
            else:
                summary = "No link available."


            article["summary"] = summary

        emails.append({"Newsletter": subject,
                       "Articles": articles})

    return emails


if __name__ == "__main__":
    newsletters = search_newsletters()
    for news in newsletters:
        print(f"📌 {news['Newsletter']}")
        for article in news["Articles"]:
            print(f"• {article['title']}\n  🔗 {article['link']}\n  📝 {article['summary']}\n")
