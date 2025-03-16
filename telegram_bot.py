import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from fetch_newsletters import search_newsletters

TELEGRAM_BOT_TOKEN = "7985776943:AAED4vPWy2qd6VJdqjMOfpn6IGiCRHrMpIY"

async def start(update: Update, context):
    # Ensure we are replying to the correct message depending on the type of update
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
    else:
        return

    keyboard = [
        [InlineKeyboardButton("🟩Data Science Weekly🟩", callback_data='datascienceweekly')],
        [InlineKeyboardButton("🔮Data Elixir🔮", callback_data='dataelixir')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Please choose a newsletter: 📝", reply_markup=reply_markup)

async def show_newsletter(update: Update, context):
    query = update.callback_query
    await query.answer()  # ✅ Acknowledge the callback query **immediately**

    newsletter_type = query.data

    # Store the newsletter name for later use
    if newsletter_type == 'datascienceweekly':
        context.user_data['newsletter_name'] = 'Data Science Weekly'
    elif newsletter_type == 'dataelixir':
        context.user_data['newsletter_name'] = 'Data Elixir'

    # ✅ Run search_newsletters in a separate thread to prevent blocking
    newsletters = await asyncio.to_thread(search_newsletters, newsletter_type)

    if not newsletters:
        await query.message.reply_text("No newsletters found.")
        return

    header = f"{context.user_data['newsletter_name']}'s this week's topics:"
    summaries = []
    context.user_data['articles'] = []

    for news in newsletters:
        for article in news['Articles']:
            title, url, summary = article['title'], article['link'], article['summary']
            if title and url:
                index = len(context.user_data['articles']) + 1
                summaries.append(f"🔹 {index}. {title}")
                context.user_data['articles'].append((title, summary, url))

    if not summaries:
        await query.message.reply_text("No articles found.")
        return

    full_message = f"{header}\n\n" + "\n".join(summaries) + "\n\nReply with a number to read the summary."
    await query.message.reply_text(full_message)
    context.user_data['awaiting_input'] = True


async def handle_user_input(update: Update, context):
    if not context.user_data.get('awaiting_input'):
        return

    user_text = update.message.text.strip()
    if user_text.isdigit():
        idx = int(user_text) - 1
        if 0 <= idx < len(context.user_data['articles']):
            title, summary, url = context.user_data['articles'][idx]
            response = f"🔹Summary:\n{summary}\n\n👉 Check the full article here: {url}"

            # Adding the options to either choose another article or go back home
            keyboard = [
                [InlineKeyboardButton("Home", callback_data='back_home')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"{response}\n\nEnter a new number to choose a new topic from {context.user_data['newsletter_name']} or click Home to start the bot again.", reply_markup=reply_markup)
            context.user_data['awaiting_input'] = True
            return

    keyboard = [
        [InlineKeyboardButton("Try again (numbers only)", callback_data='ask_number')],
        [InlineKeyboardButton("Back to titles", callback_data='back_to_titles')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Invalid input (put numbers only). Select an option:", reply_markup=reply_markup)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()  # ✅ Acknowledge the callback query

    if query.data == 'ask_number':
        await query.message.reply_text("Please enter a valid number.")
    elif query.data == 'back_to_titles':
        await show_newsletter(update, context)
    elif query.data == 'back_home':
        await start(update, context)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_newsletter, pattern='^(datascienceweekly|dataelixir)$'))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    application.run_polling()

if __name__ == '__main__':
    main()
