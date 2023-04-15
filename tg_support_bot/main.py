from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update, constants
from loguru import logger
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
WELCOME_MESSAGE = os.environ.get('WELCOME_MESSAGE', 'Welcome to support chat!')
TELEGRAM_SUPPORT_CHAT_ID = os.environ.get('TELEGRAM_SUPPORT_CHAT_ID', '')
REPLY_TO_THIS_MESSAGE = os.environ.get('REPLY_TO_THIS_MESSAGE', 'Reply to this message to send it to support chat.')
WRONG_REPLY = os.environ.get('WRONG_REPLY', 'Wrong reply. Please reply to the message from support chat.')
CONNECTED_TEXT = os.environ.get('CONNECTED_TEXT', '[*{first_name} {last_name}*](https://t.me/{username}) connected \n ID: `{id}`, lang: {language_code}, premium: {premium}')
BOOSTY_GROUP_ID = os.environ.get('BOOSTY_GROUP_ID', '')


@logger.catch
async def is_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    boosty_group_member = await context.bot.getChatMember(
        BOOSTY_GROUP_ID,
        update.effective_message.chat_id,
    )
    return boosty_group_member.status is constants.ChatMemberStatus.MEMBER


@logger.catch
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

    user_info = update.message.from_user.to_dict()
    premium = '✅' if await is_premium(update, context) else '❌'

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
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE, forward_to_chat))
    application.add_handler(MessageHandler(
        filters.Chat(int(TELEGRAM_SUPPORT_CHAT_ID)) & filters.REPLY,
        forward_to_user,
    ))
    application.run_polling()


if __name__ == '__main__':
    logger.info("Starting tg_support_bot...")
    main()
