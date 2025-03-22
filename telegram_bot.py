import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from fetch_newsletters import fetch_article_text, summarize_text, detect_language

TELEGRAM_BOT_TOKEN = "7985776943:AAED4vPWy2qd6VJdqjMOfpn6IGiCRHrMpIY"


async def start(update: Update, context):
    welcome_message = (
        "👋 *Welcome to SumBuddy Bot\!* 📚\n\n"
        "🔗 Just send me a *link* to any article, and I'll summarize it for you in seconds\.\n\n"
        "*What I Can Do:*\n"
        "✅ *One\-liner* → A quick, punchy summary\n"
        "✅ *Professional* → A well\-structured, concise breakdown\n"
        "✅ *Story Mode* → A more engaging, storytelling\-style summary\n\n"
        "🔍 _Right now, I summarize only in *English*, but future updates will support more languages\. Stay tuned\!_\n\n"
       
        "📩 *Questions or feedback?* Contact me:\n"
        "🔹 [LinkedIn](https://www\.linkedin\.com/in/tatevik-khachatryan\\-/)\n"
        "🔹 Email: tatevik\.s\.khachatryan@gmail\.com\n\n"
        "💬 *Send me a link to get started\!*"
    )

    await update.message.reply_text(welcome_message, parse_mode="MarkdownV2")

async def handle_article_link(update: Update, context):
    user_link = update.message.text.strip()

    if "medium.com" in user_link or "notion.site" in user_link:
        await update.message.reply_text("🙊 Warning: At the moment I can't summarize Medium/Notion articles. Please try something else.")
        return

    if user_link.startswith("http"):  # Validate URL
        # Fetch the article content to check its language
        full_text = await fetch_article_text(user_link)

        if full_text:
            detected_lang = detect_language(full_text)

            if detected_lang != "en":
                await update.message.reply_text("⚠️ I summarize only in English. Multi-language summarization is still in process. Please try a new article in English.")
                return  # Stop further execution and don't show summary options

            context.user_data['article_link'] = user_link
            keyboard = [
                [InlineKeyboardButton("One-liner", callback_data='oneliner')],
                [InlineKeyboardButton("Professional", callback_data='professional')],
                [InlineKeyboardButton("Story Mode", callback_data='storymode')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Choose the summary type:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("⚠️ Failed to fetch article text. Please try another link.")
    else:
        await update.message.reply_text("Please send a valid article link.")


async def show_summary(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Inform the user that the summary is being processed
    await query.message.reply_text("⏳ Processing your summary... Please wait.")

    summary_type = query.data
    article_link = context.user_data.get('article_link')

    if article_link:
        full_text = await fetch_article_text(article_link)

        if full_text:
            summary = await asyncio.to_thread(summarize_text, full_text, summary_type)
            response = f"Summary ({summary_type.capitalize()} mode):\n\n{summary}"
            await query.message.reply_text(response)
        else:
            await query.message.reply_text("⚠️ Failed to fetch article text.")
    else:
        await query.message.reply_text("No article link found. Please send a valid article link.")


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_article_link))
    application.add_handler(CallbackQueryHandler(show_summary, pattern='^(oneliner|professional|storymode)$'))
    application.run_polling()


if __name__ == '__main__':
    main()
