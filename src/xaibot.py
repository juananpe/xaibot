#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import os
import logging
from dotenv import load_dotenv

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from functools import wraps

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# Load environment variables
load_dotenv()

# Enable logging
loglevel = os.getenv("LOGLEVEL", "INFO")
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=loglevel
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

HELP = """
/start - Start the bot\n
/help - Show this help message\n
/getid - Get user and chat id\n
"""

ALLOWED_USERS = [2614189, 2181298]
ALLOWED_GROUPS = [1002015877792]

def restricted(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        if user_id not in ALLOWED_USERS and chat_id not in ALLOWED_GROUPS:
            print(f"Unauthorized access denied for user {user_id} or group {chat_id}.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(HELP)

@restricted
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply using Mistral AI"""
    username = update.effective_user.username
    message = update.message.text
    logger.info("Chat message received from user %s : %s", username, message)
    #logging.info("Chat message received from user %s : %s", username, message)

    mistralai_api_key = os.getenv("MISTRALAI_API_KEY")
    model = "mistral-medium"
    system_prompt = "You are xaibot, a Telegram bot that uses Mistral AI to generate text. Please, be short and concise (30 words maximum)."
    client = MistralClient(api_key=mistralai_api_key)

    chat_response = client.chat (
        model = model,
        messages=[
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=message)],
    )
    
    answer = chat_response.choices[0].message.content
    await update.message.reply_text(answer)

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get user and chat id"""
    user = update.effective_user.id
    chat = update.effective_chat.id
    await update.message.reply_text("User ID: " + str(user) + "\nChat ID: " + str(chat) + "\n")

def main() -> None:
    logger.info("Starting bot...")

    # Get Telegram Bot Token from envar
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    # Get MistralAI API Token from envar
    mistralai_api_key = os.getenv("MISTRALAI_API_KEY")

    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(telegram_bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("getid", getid))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
