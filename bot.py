import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Вставь свой токен и канал сюда
BOT_TOKEN = "7571256577:AAFGCDLSMXqo-6-akUISJlDM4_8wWmwYhVo"  # <-- сюда токен бота
CHANNEL_USERNAME = "@asdfzxcvasf"  # <-- сюда username канала (с @)


# 👇 Асинхронная функция обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    try:
        # Запрашиваем статус пользователя в канале
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME, user_id=user_id
        )
        status = member.status
        await update.message.reply_text(member)

        if status in ("member", "administrator", "creator"):
            await update.message.reply_text(
                f"Привет, {user.first_name}! 👋 Спасибо за подписку на наш канал."
            )
        else:
            await update.message.reply_text(
                "😕 Похоже, ты ещё не подписан на наш канал.\n"
                f"Пожалуйста, подпишись: {CHANNEL_USERNAME}"
            )

    except Exception as e:
        # Обрабатываем случай, если бот не админ в канале или канал не существует
        await update.message.reply_text(
            "⚠️ Не удалось проверить подписку. "
            "Убедись, что бот добавлен в канал как администратор."
        )
        print(f"Ошибка проверки подписки: {e}")


# 👇 Точка входа

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("🤖 Бот запущен...")
    app.run_polling()
