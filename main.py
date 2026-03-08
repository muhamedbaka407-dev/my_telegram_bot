import telebot
from telebot import types
import json, os
from datetime import datetime
import threading, time

# ===== Настройки =====
TOKEN = "8648234693:AAHJ4oP-csQQB56O6JN1xYNDaLbV3bF76GM"  # поставь свой токен
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

MANAGERS = {
    1: {"name": "Менеджер 1", "tg_id": 7160945959},
    2: {"name": "Менеджер 2", "tg_id": 0},
    3: {"name": "Менеджер 3", "tg_id": 0},
    4: {"name": "Менеджер 4", "tg_id": 0},
    5: {"name": "Менеджер 5", "tg_id": 0}
}
ADMINS = [6465381695]

PHOTO_MENU = "https://i.ibb.co/0pHcFtMk/IMG-20260224-082652-868.jpg"
PHOTO_ADMIN = "https://i.ibb.co/G3kpSWjM/Picsart-26-02-28-10-05-12-577.jpg"

ORDERS_FILE = "orders.json"
RATINGS_FILE = "ratings.json"
CHATS_FILE = "chats.json"

AUTO_CLOSE_MINUTES = 15
CHECK_INTERVAL = 60

# ===== Загрузка данных =====
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

ORDERS = load_json(ORDERS_FILE, {})
RATINGS = load_json(RATINGS_FILE, {str(mid): [] for mid in MANAGERS})
CHATS = load_json(CHATS_FILE, {})

def save_data():
    try:
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(ORDERS, f, ensure_ascii=False, indent=4)
        with open(RATINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(RATINGS, f, ensure_ascii=False, indent=4)
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(CHATS, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ Ошибка при сохранении данных: {e}")

# ===== Переменные =====
ACTIVE_CHATS = {}
users_waiting_order = {}
LAST_CLIENT_MESSAGE = {}

# ===== Безопасная отправка сообщений/фото =====
def send_safe_message(chat_id, text, reply_markup=None):
    try:
        if chat_id == bot.get_me().id: return
        user = bot.get_chat(chat_id)
        if user.type == 'private':
            return bot.send_message(chat_id, text, reply_markup=reply_markup)
    except Exception as e:
        print(f"⚠️ Ошибка при отправке сообщения: {e}")

def send_safe_photo(chat_id, photo, caption=None, reply_markup=None):
    try:
        if chat_id == bot.get_me().id: return
        user = bot.get_chat(chat_id)
        if user.type == 'private':
            return bot.send_photo(chat_id, photo, caption=caption, reply_markup=reply_markup)
    except Exception as e:
        print(f"⚠️ Ошибка при отправке фото: {e}")

# ===== Главное меню =====
def main_menu(user_id=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💰 Цены", callback_data="prices"),
        types.InlineKeyboardButton("🚀 Буст БО/КБ", callback_data="boost")
    )
    if user_id in ADMINS:
        markup.add(types.InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel"))
    return markup

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in [v["tg_id"] for v in MANAGERS.values() if v["tg_id"] != 0]:
        manager_panel(user_id)
    else:
        photo_to_send = PHOTO_ADMIN if user_id in ADMINS else PHOTO_MENU
        send_safe_photo(
            user_id,
            photo_to_send,
            caption="👋 <b>Здравствуйте, я бот для покупки софтов для игры Free Fire!</b>\n\nВыберите раздел ниже 👇",
            reply_markup=main_menu(user_id)
        )

# ===== Панель менеджера =====
def manager_panel(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⭐ Мой рейтинг","📊 Статистика заказов","⬅️ Главное меню")
    send_safe_photo(chat_id, PHOTO_MENU, caption="👨‍💼 Панель менеджера", reply_markup=markup)

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    try: bot.delete_message(user_id, call.message.message_id)
    except: pass

    if call.data in ["menu", "back"]:
        start(call)
        return

    if call.data=="prices":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📩 Написать менеджерам", callback_data="write_to_managers"),
            types.InlineKeyboardButton("⬅️ Назад", callback_data="menu")
        )
        send_safe_photo(user_id, PHOTO_MENU, caption="💰 Цены", reply_markup=markup)

    elif call.data=="write_to_managers":
        send_safe_message(user_id, "✍️ Напишите сообщение для менеджеров:")
        bot.register_next_step_handler_by_chat_id(user_id, send_to_all_managers)

    elif call.data=="boost":
        markup=types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="menu"))
        send_safe_photo(user_id, PHOTO_MENU, caption="🚀 Буст БО/КБ", reply_markup=markup)

    elif call.data=="admin_panel" and user_id in ADMINS:
        markup=types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📦 Все заказы", callback_data="admin_orders"),
            types.InlineKeyboardButton("⭐ Рейтинг менеджеров", callback_data="admin_ratings"),
            types.InlineKeyboardButton("🧹 Очистить переписку клиента", callback_data="admin_clear_chat"),
            types.InlineKeyboardButton("⬅️ Главное меню", callback_data="menu")
        )
        send_safe_photo(user_id, PHOTO_ADMIN, caption="👑 Админ-панель", reply_markup=markup)

# ===== Отправка заказа менеджерам =====
def send_to_all_managers(message):
    user_id = message.from_user.id
    if user_id in ACTIVE_CHATS:
        send_safe_message(user_id, "⚠️ Ваш заказ уже принят менеджером.")
        return
    if user_id in LAST_CLIENT_MESSAGE:
        try: bot.delete_message(user_id, LAST_CLIENT_MESSAGE[user_id])
        except: pass

    LAST_CLIENT_MESSAGE[user_id] = message.message_id
    users_waiting_order[user_id] = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    # Создаём заказ
    ORDERS[user_id] = {"manager": 0, "closed": False, "messages": []}
    save_data()

    for mid, data in MANAGERS.items():
        manager_id = data["tg_id"]
        if manager_id == 0: continue
        if manager_id not in [m["tg_id"] for m in MANAGERS.values() if m["tg_id"] != 0]:
            continue
        try:
            user = bot.get_chat(manager_id)
            if user.type == 'private':
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("✅ Принять заказ", callback_data=f"accept_{user_id}"))
                send_safe_message(manager_id, f"📦 Новый заказ от @{message.from_user.username}:\n📝 {message.text}", reply_markup=markup)
        except Exception as e:
            print(f"⚠️ Менеджер {manager_id} недоступен: {e}")

    send_safe_message(user_id, "⚠️ Ваш заказ отправлен менеджерам. Ждите, пока кто-то примет заказ.")

# ===== Приватные чаты =====
@bot.message_handler(content_types=['text'])
def private_chat(message):
    user_id = message.from_user.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if user_id not in ACTIVE_CHATS and user_id not in users_waiting_order and user_id not in [v["tg_id"] for v in MANAGERS.values() if v["tg_id"] != 0]:
        try: bot.delete_message(user_id, message.message_id)
        except: pass
        return

    # Клиент пишет менеджеру
    if user_id in ACTIVE_CHATS:
        manager_id = ACTIVE_CHATS[user_id]
        CHATS.setdefault(str(user_id), []).append({
            "client_id": user_id,
            "manager_id": manager_id,
            "from": "client",
            "text": message.text,
            "date": now
        })
        ORDERS[user_id]["messages"].append(message.text)
        save_data()
        send_safe_message(manager_id, f"👤 Клиент:\n{message.text}")
        return

    # Менеджер пишет клиенту
    for client_id, manager_id in ACTIVE_CHATS.items():
        if manager_id == user_id:
            CHATS.setdefault(str(client_id), []).append({
                "client_id": client_id,
                "manager_id": manager_id,
                "from": "manager",
                "text": message.text,
                "date": now
            })
            ORDERS[client_id]["messages"].append(message.text)
            save_data()
            send_safe_message(client_id, f"👨‍💼 Менеджер:\n{message.text}")
            return

# ===== Принятие заказа =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_order(call):
    client_id = int(call.data.split("_")[1])
    manager_id = call.from_user.id

    # Проверка что только менеджер может принять
    if manager_id not in [m["tg_id"] for m in MANAGERS.values() if m["tg_id"] != 0]:
        send_safe_message(manager_id, "⚠️ Только менеджеры могут принять заказ!")
        return

    if client_id in ACTIVE_CHATS:
        send_safe_message(manager_id, "⚠️ Этот заказ уже принят другим менеджером.")
        return

    ACTIVE_CHATS[client_id] = manager_id
    users_waiting_order.pop(client_id, None)
    LAST_CLIENT_MESSAGE.pop(client_id, None)
    ORDERS[client_id]["manager"] = manager_id
    save_data()

    send_safe_message(client_id, "✅ Ваш заказ принят менеджером, теперь вы можете писать.")
    send_safe_message(manager_id, f"✅ Вы приняли заказ от клиента {client_id}.")

# ===== Оценка менеджера =====
def ask_rating(client_id, manager_id):
    markup = types.InlineKeyboardMarkup(row_width=5)
    for i in range(1, 6):
        markup.add(types.InlineKeyboardButton(f"{i}⭐", callback_data=f"rate_{manager_id}_{client_id}_{i}"))
    send_safe_message(client_id, f"📊 Пожалуйста, оцените работу менеджера {MANAGERS.get(manager_id, {}).get('name','')}:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rate_"))
def rate_manager(call):
    try:
        _, manager_id, client_id, rating = call.data.split("_")
        manager_id = int(manager_id)
        client_id = int(client_id)
        rating = int(rating)

        RATINGS.setdefault(str(manager_id), []).append(rating)
        save_data()
        try: bot.delete_message(client_id, call.message.message_id)
        except: pass
        send_safe_message(client_id, "✅ Спасибо за покупку!")
        send_safe_photo(client_id, PHOTO_MENU, caption="👋 <b>Выберите раздел ниже 👇</b>", reply_markup=main_menu(client_id))
    except Exception as e:
        print(f"⚠️ Ошибка при оценке: {e}")

# ===== Авто-закрытие заказов =====
def auto_close_orders():
    while True:
        now = datetime.now()
        for uid, order in list(ORDERS.items()):
            if order.get("closed"): continue
            chat = CHATS.get(str(uid), [])
            if not chat: continue
            last_time = datetime.strptime(chat[-1]["date"], "%Y-%m-%d %H:%M:%S")
            diff = (now - last_time).total_seconds() / 60
            if diff >= AUTO_CLOSE_MINUTES:
                ORDERS[uid]["closed"] = True
                ACTIVE_CHATS.pop(int(uid), None)
                save_data()
                send_safe_message(int(uid), "⏰ Ваш заказ автоматически закрыт из-за отсутствия переписки.")
                manager_id = order.get("manager", 0)
                if manager_id != 0:
                    send_safe_message(manager_id, f"⏰ Заказ клиента {uid} автоматически закрыт.")
                ask_rating(int(uid), manager_id)
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=auto_close_orders, daemon=True).start()

# ===== Запуск бота =====
bot.polling(non_stop=True, timeout=60)
