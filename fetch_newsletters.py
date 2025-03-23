import asyncio
import re
from bs4 import BeautifulSoup
from newspaper import Article
from requests_html import AsyncHTMLSession
from langdetect import detect
from transformers import T5Tokenizer, T5ForConditionalGeneration

# Load the summarization model and tokenizer once
tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-base", legacy=False)
model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-base")
device = "cpu"  # Or "cuda" if you later upgrade to a GPU instance
model.to(device)

async def fetch_article_text(url, semaphore=None):
    """
    Asynchronously fetches article text. Uses AsyncHTMLSession to render JavaScript,
    handles Substack redirect links, and processes Medium articles properly.
    """
    if semaphore is None:
        semaphore = asyncio.Semaphore(5)  # limit concurrency

    async with semaphore:
        try:
            session = AsyncHTMLSession()
            response = await session.get(url)
            await response.html.arender(timeout=20, sleep=2)

            # Handle Substack redirects by following the first absolute link
            if "substack.com/redirect" in response.url:
                links = list(response.html.absolute_links)
                if links:
                    real_url = links[0]
                    return await fetch_article_text(real_url, semaphore)

            # Use newspaper3k in a thread for general article extraction
            def parse_article(url):
                art = Article(url)
                art.download()
                art.parse()
                return art.text.strip()

            article_text = await asyncio.to_thread(parse_article, response.url)

            # Return valid extracted content
            if article_text and len(article_text) > 200:
                return article_text

            # Fallback: Use rendered page text if other methods fail
            fallback_text = response.html.text.strip()
            return fallback_text if fallback_text and len(fallback_text) > 200 else None

        except Exception as e:
            print(f"⚠️ Failed to fetch article ({url}): {e}. Are you sure it's a valid article link? 👀")
            return None


def detect_language(text):
    """
    Detects the language of the given text.
    """
    try:
        return detect(text)
    except Exception:
        return "unknown"  # In case detection fails


def summarize_text(text, summary_type="casual"):
    """
    Summarizes text using the FLAN-T5 model with different styles and length constraints.
    """
    if summary_type == "professional":
        input_text = f"Summarize this professionally with at least 150 characters: {text}"
        max_length = 200
    elif summary_type == "oneliner":
        input_text = f"Summarize in one concise sentence: {text}"
        max_length = 50
    elif summary_type == "storymode":
        input_text = f"Summarize this as an engaging story and ensure it ends with a complete sentence: {text}"
        max_length = 300
    else:
        input_text = f"Summarize: {text}"
        max_length = 200

    inputs = tokenizer(input_text, return_tensors="pt", max_length=256, truncation=True)
    summary_ids = model.generate(
        inputs.input_ids,
        max_length=max_length,
        min_length=max_length - 50,  # Enforce minimum character count
        num_beams=5,  # Increase diversity
        length_penalty=1.5,  # Encourage longer summaries
        early_stopping=True,
        no_repeat_ngram_size=3  # Prevent repetitive phrases
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    # Ensure the summary ends with a full sentence
    if not summary.endswith(('.', '!', '?')):
        summary = summary.rsplit('.', 1)[0] + '.'  # Trim to the last full sentence

    return summary
