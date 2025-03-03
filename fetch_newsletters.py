from googleapiclient.discovery import build
import base64
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


def get_gmail_service():
    from gmail_connect import get_gmail_service
    return get_gmail_service()


def extract_text_from_html(html_content, sender):
    """Extracts relevant information from HTML emails based on the sender."""
    soup = BeautifulSoup(html_content, "html.parser")
    articles = set()  # Use a set to avoid duplicates

    if "dataelixir" in sender:
        # Extract ALL <h2> titles and their following <p> summaries
        h2_tags = soup.find_all("h2")
        for h2 in h2_tags:
            title = h2.get_text(strip=True)
            articles.add(f"• {title}")

    elif "datascienceweekly" in sender:
        # Extract ONLY from "Editor's Picks" & "Data Science Articles & Videos"
        sections_of_interest = ["Editor's Picks", "Data Science Articles & Videos"]

        for h2 in soup.find_all("h2"):
            if h2.get_text(strip=True) in sections_of_interest:
                ul = h2.find_next("ul")  # Find the next <ul> under this section
                if ul:
                    for li in ul.find_all("li"):
                        strong_tag = li.find("strong")
                        title = strong_tag.get_text(strip=True) if strong_tag else "Untitled"
                        articles.add(f"• {title}")

    return "\n".join(list(articles)[:10]) if articles else "No relevant content found."


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
            body_text = extract_text_from_html(html_content, sender) if html_content else "No content found."
        else:
            body_text = "No content found."

        emails.append({"subject": subject, "summary": body_text})

    return emails


if __name__ == "__main__":
    newsletters = search_newsletters()
    for news in newsletters:
        print(f"📌 {news['subject']}\n{news['summary']}\n")
