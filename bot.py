import os
import logging
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

import db

load_dotenv()
API_TOKEN = os.getenv('6820348217:AAFDPmu57ZLh70kGbUq76yi7UaoPOXE6uCY')
ADMIN_ID   = int(os.getenv('7061277619', '0'))
if not API_TOKEN or not ADMIN_ID:
    raise RuntimeError("Установите BOT_TOKEN и ADMIN_ID в окружении")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    tariff          = State()
    release_name    = State()
    subtitle        = State()
    genre           = State()
    upc             = State()
    release_date    = State()
    vocals_info     = State()
    authors         = State()
    pitching        = State()
    files_link      = State()
    contact         = State()
    comments        = State()
    captcha         = State()

@dp.message_handler(commands=['start', 'help'])
async def cmd_start(message: types.Message):
    await db.init_db()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📝 Заполнить заявку", "👤 Личный кабинет")
    if message.from_user.id == ADMIN_ID:
        kb.add("🔧 Админ-панель")
    await message.answer(
        "Привет! Это бот музыкального лейбла.\nВыберите действие:",
        reply_markup=kb
    )

# --- Анкета (с тарифом, датой, капчей и т.д.) ---
@dp.message_handler(lambda m: m.text == "📝 Заполнить заявку")
async def start_form(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("MINI", "PLUS")
    await Form.tariff.set()
    await message.answer("Выберите ваш тариф:", reply_markup=kb)

@dp.message_handler(state=Form.tariff)
async def process_tariff(message: types.Message, state: FSMContext):
    await state.update_data(tariff=message.text)
    await Form.release_name.set()
    await message.answer("Название релиза:")

@dp.message_handler(state=Form.release_name)
async def process_release_name(message: types.Message, state: FSMContext):
    await state.update_data(release_name=message.text)
    await Form.subtitle.set()
    await message.answer("Саб-название (slowed, speed и т.д.):")

@dp.message_handler(state=Form.subtitle)
async def process_subtitle(message: types.Message, state: FSMContext):
    await state.update_data(subtitle=message.text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Pop", "Hip-Hop", "Rock", "Electronic", "Other")
    await Form.genre.set()
    await message.answer("Жанр релиза:", reply_markup=kb)

@dp.message_handler(state=Form.genre)
async def process_genre(message: types.Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await Form.upc.set()
    await message.answer("UPC (при переносе или перезаливе):", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(state=Form.upc)
async def process_upc(message: types.Message, state: FSMContext):
    await state.update_data(upc=message.text)
    await Form.release_date.set()
    await message.answer("Дата релиза (ГГГГ-ММ-ДД, минимум через 7 дней):")

@dp.message_handler(state=Form.release_date)
async def process_release_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return await message.answer("Неверный формат. Ожидаю ГГГГ-ММ-ДД.")
    if dt < datetime.now() + timedelta(days=7):
        return await message.answer("Дата должна быть не раньше, чем через 7 дней.")

    await state.update_data(release_date=text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Есть вокал и текст", "Инструментал (без вокала)")
    await Form.vocals_info.set()
    await message.answer("Информация о вокале:", reply_markup=kb)

@dp.message_handler(state=Form.vocals_info)
async def process_vocals(message: types.Message, state: FSMContext):
    await state.update_data(vocals_info=message.text)
    await Form.authors.set()
    await message.answer("ФИО авторов/битмейкеров инструментала:")

@dp.message_handler(state=Form.authors)
async def process_authors(message: types.Message, state: FSMContext):
    await state.update_data(authors=message.text)
    await Form.pitching.set()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Далее")
    await message.answer(
        "Питчинг (необязательно, ссылка link.cdcult.ru/pitching):",
        reply_markup=kb
    )

@dp.message_handler(state=Form.pitching)
async def process_pitching(message: types.Message, state: FSMContext):
    text = "" if message.text == "Далее" else message.text
    await state.update_data(pitching=text)
    await Form.files_link.set()
    await message.answer(
        "Ссылка на архив + требования:\n"
        "• Audio: .wav/.flac\n"
        "• Cover: .jpg (≧3000×3000)\n"
        "• Видео с дорожками (ОБЯЗАТЕЛЬНО)\n"
        "Вставьте прямую ссылку на архив:"
    )

@dp.message_handler(state=Form.files_link)
async def process_files_link(message: types.Message, state: FSMContext):
    await state.update_data(files_link=message.text)
    await Form.contact.set()
    await message.answer("Как с вами связаться?")

@dp.message_handler(state=Form.contact)
async def process_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await Form.comments.set()
    await message.answer("Дополнительные комментарии (если есть):")

@dp.message_handler(state=Form.comments)
async def process_comments(message: types.Message, state: FSMContext):
    await state.update_data(comments=message.text)
    # капча
    a, b = random.randint(1, 10), random.randint(1, 10)
    await state.update_data(captcha_answer=a + b)
    await Form.captcha.set()
    await message.answer(f"Проверка: {a} + {b} = ?")

@dp.message_handler(state=Form.captcha)
async def process_captcha(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        ans = int(message.text)
    except ValueError:
        return await message.answer("Введите число.")
    if ans != data['captcha_answer']:
        a, b = random.randint(1, 10), random.randint(1, 10)
        await state.update_data(captcha_answer=a + b)
        return await message.answer(f"Неправильно. {a} + {b} = ?")
    # всё верно — собираем и шлём админу
    info = await state.get_data()
    await state.finish()
    text = (
        f"📥 <b>Новая заявка</b>\n"
        f"• Тариф: {info['tariff']}\n"
        f"• Релиз: {info['release_name']}\n"
        f"• Саб: {info['subtitle']}\n"
        f"• Жанр: {info['genre']}\n"
        f"• UPC: {info['upc']}\n"
        f"• Дата: {info['release_date']}\n"
        f"• Вокал: {info['vocals_info']}\n"
        f"• Авторы: {info['authors']}\n"
        f"• Питчинг: {info['pitching'] or '—'}\n"
        f"• Архив: {info['files_link']}\n"
        f"• Контакт: {info['contact']}\n"
        f"• Комментарии: {info['comments'] or '—'}"
    )
    await bot.send_message(ADMIN_ID, text, parse_mode='HTML')
    await message.answer("✅ Заявка отправлена! Спасибо.")

# — Личный кабинет артиста и админ-панель —
@dp.message_handler(lambda m: m.text == "👤 Личный кабинет")
async def show_cabinet(message: types.Message):
    user_id = message.from_user.id
    data = await db.get_artist(user_id)
    if not data:
        await db.upsert_artist(user_id)
        data = (0.0, 'MINI', 0)
    balance, tariff, tracks = data
    await message.answer(
        f"👤 Ваш кабинет:\n"
        f"• Тариф: {tariff}\n"
        f"• Баланс: {balance:.2f}\n"
        f"• Треков: {tracks}"
    )

@dp.message_handler(lambda m: m.text == "🔧 Админ-панель")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "Админ-команды:\n"
        "/view <user_id>\n"
        "/bal <user_id> <amount>\n"
        "/tariff <user_id> <MINI|PLUS>\n"
        "/tracks <user_id> <count>"
    )

@dp.message_handler(lambda m: m.text.startswith("/view "))
async def cmd_view(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts)!=2 or not parts[1].isdigit():
        return await message.answer("Использование: /view <user_id>")
    uid = int(parts[1])
    d = await db.get_artist(uid)
    if not d:
        return await message.answer("Артист не найден.")
    bal, trf, cnt = d
    await message.answer(f"ID {uid} → Тариф: {trf}, Баланс: {bal:.2f}, Треков: {cnt}")

@dp.message_handler(lambda m: m.text.startswith("/bal "))
async def cmd_bal(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    _, uid_s, amt_s = message.text.split(maxsplit=2)
    if not uid_s.isdigit():
        return await message.answer("Первый аргумент — user_id.")
    try: amt = float(amt_s)
    except:
        return await message.answer("Второй аргумент — число (баланс).")
    uid = int(uid_s)
    await db.upsert_artist(uid, balance=amt)
    await message.answer(f"Баланс юзера {uid} = {amt:.2f}")

@dp.message_handler(lambda m: m.text.startswith("/tariff "))
async def cmd_tariff(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    _, uid_s, trf = message.text.split(maxsplit=2)
    if not uid_s.isdigit() or trf not in ("MINI","PLUS"):
        return await message.answer("Использование: /tariff <user_id> <MINI|PLUS>")
    uid = int(uid_s)
    await db.upsert_artist(uid, tariff=trf)
    await message.answer(f"Тариф {uid} = {trf}")

@dp.message_handler(lambda m: m.text.startswith("/tracks "))
async def cmd_tracks(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    _, uid_s, cnt_s = message.text.split(maxsplit=2)
    if not uid_s.isdigit() or not cnt_s.isdigit():
        return await message.answer("Использование: /tracks <user_id> <count>")
    uid, cnt = int(uid_s), int(cnt_s)
    await db.upsert_artist(uid, tracks_count=cnt)
    await message.answer(f"Треков у {uid} = {cnt}")

if name == '__main__':
    executor.start_polling(dp, skip_updates=True)
