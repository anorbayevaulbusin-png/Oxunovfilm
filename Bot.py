import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

FILM_BOT_TOKEN = "8650700833:AAGDTLvsaKxKN6OW8qBXwdYJdIsPRAVe7-I"
film_bot = Bot(token=FILM_BOT_TOKEN)

dp = Dispatcher()
router = Router()

CHANNEL_USERNAME = "@oxunovfilm"


def init_db():
  conn = sqlite3.connect("movies.db")
  cursor = conn.cursor()
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            file_id TEXT,
            caption TEXT
        )
    """
  )
  conn.commit()
  conn.close()


init_db()


async def check_subscription(user_id: int):
  try:
    member = await film_bot.get_chat_member(
        chat_id=CHANNEL_USERNAME, user_id=user_id
    )
    if member.status in ["member", "administrator", "creator"]:
      return True
  except Exception:
    pass
  return False


def main_menu():
  return ReplyKeyboardMarkup(
      keyboard=[
          [
              KeyboardButton(text="🎬 Kinolar qidirish"),
              KeyboardButton(text="📢 Kanalimiz"),
          ],
          [
              KeyboardButton(text="📸 Instagram"),
              KeyboardButton(text="✍️ Adminga murojaat"),
          ],
      ],
      resize_keyboard=True,
  )


def sub_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📢 Kanalga obuna bo'lish", url="https://t.me/oxunovfilm"
              )
          ],
          [
              InlineKeyboardButton(
                  text="✅ Obunani tekshirish", callback_data="check_sub"
              )
          ],
      ]
  )


@router.message(Command("start"))
async def film_start(message: Message):
  user_id = message.from_user.id
  if not await check_subscription(user_id):
    await message.answer(
        "⚠️ Botdan foydalanish uchun avval rasmiy kanalimizga obuna bo'ling!",
        reply_markup=sub_keyboard(),
    )
    return

  await message.answer(
      "🎥 **Oxunov Film** rasmiy botiga xush kelibsiz!\n\n"
      "Kino kodini yuboring (masalan: 101, 105):",
      reply_markup=main_menu(),
      parse_mode="Markdown",
  )


@router.callback_query(F.data == "check_sub")
async def verify_subscription(callback: CallbackQuery):
  if await check_subscription(callback.from_user.id):
    await callback.message.delete()
    await callback.message.answer(
        "Rahmat! Obuna tasdiqlandi. Kino kodini yuborishingiz mumkin:",
        reply_markup=main_menu(),
    )
  else:
    await callback.answer(
        "Siz hali kanalga obuna bo'lmadingiz!", show_alert=True
    )


@router.message(F.video)
async def save_movie(message: Message):
  if message.from_user.username != "oxunov18":
    return

  if not message.caption or "|" not in message.caption:
    await message.answer(
        "⚠️ Kino kodi va nomini to'g'ri yozing!\nNamuna: `105|Kino nomi`",
        parse_mode="Markdown",
    )
    return

  code, title = message.caption.split("|", 1)
  code = code.strip()
  file_id = message.video.file_id

  conn = sqlite3.connect("movies.db")
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR REPLACE INTO movies (code, file_id, caption) VALUES (?, ?,"
      " ?)",
      (code, file_id, title.strip()),
  )
  conn.commit()
  conn.close()

  await message.answer(
      f"✅ **{code}**-kodli kino bazaga muvaffaqiyatli saqlandi!"
  )


@router.message(
    F.text
    & ~F.text.in_(
        [
            "🎬 Kinolar qidirish",
            "📢 Kanalimiz",
            "📸 Instagram",
            "✍️ Adminga murojaat",
        ]
    )
)
async def get_movie_by_code(message: Message):
  if not await check_subscription(message.from_user.id):
    await message.answer(
        "⚠️ Avval kanalga obuna bo'ling!", reply_markup=sub_keyboard()
    )
    return

  code = message.text.strip()

  conn = sqlite3.connect("movies.db")
  cursor = conn.cursor()
  cursor.execute("SELECT file_id, caption FROM movies WHERE code = ?", (code,))
  movie = cursor.fetchone()
  conn.close()

  if movie:
    file_id, caption = movie
    await message.answer_video(
        video=file_id,
        caption=f"🎬 {caption}\n🔗 Kanal: @oxunovfilm",
        reply_markup=main_menu(),
    )
  else:
    await message.answer(
        "❌ Kino kodi xato yoki bunday kino mavjud emas!",
        reply_markup=main_menu(),
    )


@router.message(F.text == "🎬 Kinolar qidirish")
async def search_prompt(message: Message):
  await message.answer(
      "🔍 Kino kodini yuboring (masalan: 101, 105):", reply_markup=main_menu()
  )


@router.message(F.text == "📢 Kanalimiz")
async def channel_link(message: Message):
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔗 Telegram kanal", url="https://t.me/oxunovfilm"
              )
          ]
      ]
  )
  await message.answer(
      "📢 Bizning Telegram kanalimiz:", reply_markup=keyboard
  )


@router.message(F.text == "📸 Instagram")
async def instagram_link(message: Message):
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📸 Instagram sahifamiz",
                  url="https://instagram.com/oxunovfilm",
              )
          ]
      ]
  )
  await message.answer("📱 Bizning Instagram sahifamiz:", reply_markup=keyboard)


@router.message(F.text == "✍️ Adminga murojaat")
async def contact_admin(message: Message):
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="💬 Adminga yozish", url="https://t.me/oxunov18"
              )
          ]
      ]
  )
  await message.answer(
      "🛠 Savol va takliflar uchun admin bilan bog'laning:",
      reply_markup=keyboard,
  )


async def main():
  dp.include_router(router)
  print("Oxunov Film boti ishga tushdi...")
  await film_bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(film_bot)


if __name__ == "__main__":
  asyncio.run(main())
