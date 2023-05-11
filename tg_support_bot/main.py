from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from loguru import logger
import os
import aiohttp
from tg_support_bot import schemas

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
WELCOME_MESSAGE = os.environ.get('WELCOME_MESSAGE', 'Welcome to support chat!')
TELEGRAM_SUPPORT_CHAT_ID = os.environ.get('TELEGRAM_SUPPORT_CHAT_ID', '')
REPLY_TO_THIS_MESSAGE = os.environ.get('REPLY_TO_THIS_MESSAGE', 'Reply to this message to send it to support chat.')
WRONG_REPLY = os.environ.get('WRONG_REPLY', 'Wrong reply. Please reply to the message from support chat.')
CONNECTED_TEXT = os.environ.get('CONNECTED_TEXT', '[*{first_name} {last_name}*](https://t.me/{username}) connected \n ID: `{id}`, lang: {language_code}, premium: {premium}')

BOOSTY_CHECKER_URL = os.environ.get('BOOSTY_CHECKER_URL', '')
BOOSTY_CHECKER_TOKEN = os.environ.get('BOOSTY_CHECKER_TOKEN', '')


@logger.catch
async def is_premium(ident: str) -> bool:
    auth = aiohttp.BasicAuth('api', BOOSTY_CHECKER_TOKEN)
    async with aiohttp.ClientSession(auth=auth) as session:
        data = schemas.GetPremiumUser(ident=ident)
        async with session.post(f'{BOOSTY_CHECKER_URL}/is_premium', json=data.dict()) as resp:
            return schemas.IsPremium.parse_raw(await resp.text()).is_premium


@logger.catch
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

    user_info = update.message.from_user.to_dict()
    if user_info.get('username') is None:
        user_info['username'] = ''
    if user_info.get('first_name') is None:
        user_info['first_name'] = ''
    if user_info.get('last_name') is None:
        user_info['last_name'] = ''
    if user_info.get('language_code') is None:
        user_info['language_code'] = ''

    premium = '✅' if await is_premium(str(update.message.chat_id)) else '❌'

    await context.bot.send_message(
        chat_id=TELEGRAM_SUPPORT_CHAT_ID,
        text=CONNECTED_TEXT.format(**user_info, premium=premium),
        parse_mode='MarkdownV2',
        disable_web_page_preview=True,
    )


@logger.catch
async def forward_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    forwarded = await update.message.forward(chat_id=TELEGRAM_SUPPORT_CHAT_ID)
    if not forwarded.forward_from:
        await context.bot.send_message(
            chat_id=TELEGRAM_SUPPORT_CHAT_ID,
            reply_to_message_id=forwarded.message_id,
            text=f'{update.message.from_user.id}\n{REPLY_TO_THIS_MESSAGE}'
        )


@logger.catch
async def forward_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = None
    if update.message.reply_to_message.forward_from:
        user_id = update.message.reply_to_message.forward_from.id
    elif REPLY_TO_THIS_MESSAGE in update.message.reply_to_message.text:
        try:
            user_id = int(update.message.reply_to_message.text.split('\n')[0])
        except ValueError:
            user_id = None
    if user_id:
        await context.bot.copy_message(
            message_id=update.message.message_id,
            chat_id=user_id,
            from_chat_id=update.message.chat_id
        )
    else:
        await context.bot.send_message(
            chat_id=TELEGRAM_SUPPORT_CHAT_ID,
            text=WRONG_REPLY
        )


@logger.catch
async def use_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=f'Это не игра, это бот для связи с поддержкой. Пожалуйста, напишите {text}, в игру.'
    )


@logger.catch
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.COMMAND & ~filters.Text(['/start']), use_game))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE, forward_to_chat))
    application.add_handler(MessageHandler(
        filters.Chat(int(TELEGRAM_SUPPORT_CHAT_ID)) & filters.REPLY,
        forward_to_user,
    ))
    application.run_polling()


if __name__ == '__main__':
    logger.info("Starting tg_support_bot...")
    main()
