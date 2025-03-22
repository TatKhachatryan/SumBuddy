# SumBuddy: Your AI-Powered Telegram Assistant for Smarter Reading
Ever stumbled upon an interesting article but didn’t have the time to read it? We’ve all been there. That’s exactly why I built SumBuddy, a Telegram bot that summarizes articles for you in seconds.

Instead of skimming through long texts or bookmarking articles you’ll never return to, just send the link to SumBuddy, and it will generate a summary tailored to your needs. Whether you want a quick one-liner, a structured breakdown, or an engaging story-style summary, SumBuddy has you covered.

### How It Works
Using AI-powered natural language processing (NLP), SumBuddy extracts key points from any article and condenses them into **3 different styles**:

* A **one-liner** for a quick takeaway.

* A **professional** summary for structured insights.

* A **story mode** version that reads like a short engaging narrative.

The bot is powered by **Google’s FLAN-T5 model**, which helps generate human-like summaries while preserving context and meaning.

### Building the Bot
Developing SumBuddy wasn’t just about connecting a summarization model to Telegram—it involved handling real-world challenges like text extraction, unsupported websites, and multi-language detection. The bot automatically warns users when an article isn’t supported (like Medium links) and informs them when non-English content is detected.

For deployment, I initially hosted the bot on Railway, but after facing issues with disappearing environments, I moved it to Render, ensuring stable **24/7 availability**. Security was also a key priority, so the bot token is managed through environment variables to prevent accidental exposure.

### What’s Next?
I’m constantly improving SumBuddy, with **multi-language summarization and PDF support** being next on the roadmap. The goal is to make it even more useful for people who want quick and insightful summaries without the hassle of reading entire articles.

### Want to Try It?
SumBuddy is live and ready to help! You can chat with the bot here and test out its summarization capabilities.

If you're interested in AI-powered automation, feel free to connect with me:
📧 Email: tatevik.s.khachatryan@gmail.com
💼 LinkedIn: https://www.linkedin.com/in/tatevik-khachatryan-/
