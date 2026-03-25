import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN, ADMIN_ID, GROUP_LINK, PAYMENT_AMOUNT, CARD_NUMBER, CARD_OWNER
from keyboards import pay_keyboard, back_keyboard, admin_keyboard
from database import init_db, add_pending_payment, approve_payment

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

WELCOME_TEXT = f"""Тариф: Доступ в Мастерскую Рукоделия 🔥

Стоимость: {PAYMENT_AMOUNT}.00 🇷🇺 RUB
Срок действия: бессрочно

Вы получите доступ к закрытому клубу для мастеров любого направления.

Внутри клуба ты научишься продавать свои изделия стабильно и масштабироваться.

Бонусные уроки + 130 видеомастер-классов в подарок.

Жми кнопку ниже и начинай зарабатывать! 👇"""

PAYMENT_TEXT = f"""Способ оплаты: Переводом на карту!

К оплате: {PAYMENT_AMOUNT}.00 🇷🇺 RUB
Ваш ID: {{user_id}}

Реквизиты для оплаты:
💳 {CARD_NUMBER}
{CARD_OWNER}

После оплаты обязательно пришлите чек (скриншот или фото) в этот чат.

Бот добавит вас в группу сразу после проверки."""

SUCCESS_TEXT = """✅ Оплата успешно подтверждена!

Добро пожаловать в Мастерскую Рукоделия 🎉

Ваша ссылка на закрытый клуб:"""

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=pay_keyboard())

@dp.callback_query(F.data == "pay")
async def pay(callback: CallbackQuery):
    user = callback.from_user
    await add_pending_payment(user.id, user.username or "нет username")
    
    text = PAYMENT_TEXT.format(user_id=user.id)
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=pay_keyboard())

@dp.message(F.photo | F.document)
async def receive_check(message: Message):
    user = message.from_user
    
    # Пересылаем чек админу
    await bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    
    await bot.send_message(
        ADMIN_ID,
        f"🔔 Новый чек от пользователя!\n\n"
        f"ID: <code>{user.id}</code>\n"
        f"Username: @{user.username or 'нет'}",
        reply_markup=admin_keyboard(user.id)
    )
    
    await message.answer("✅ Квитанция отправлена на проверку.\nПожалуйста, ожидайте. Бот сообщит об успешном платеже.")

@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await approve_payment(user_id)
    
    try:
        await bot.send_message(user_id, SUCCESS_TEXT + f"\n\n{GROUP_LINK}")
        await callback.message.edit_text("✅ Платёж одобрен и пользователь уведомлён!")
    except Exception as e:
        await callback.message.edit_text("✅ Платёж одобрен, но сообщение не дошло пользователю.")

@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):
    await callback.message.edit_text("❌ Платёж отклонён.")

async def main():
    await init_db()
    print("✅ Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
