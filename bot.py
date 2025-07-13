from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import json
import os
from datetime import datetime

# ========== إعدادات البوت ==========
TOKEN = "7737263844:AAFfogOJz4lfKtsgZLgqNjdhPDspcTjD2yE"
OWNER_ID = 7928004645
TON_WALLET = "UQAvKW2nLoNs3Tj2P_ZB-yZSH8FzrBcPxlDT0UoZJJjj3h8l"

USERNAMES_FILE = "usernames.json"
SALES_LOG_FILE = "sales_log.json"
USER_LANGS_FILE = "user_langs.json"

# ========== بيانات اليوزرات مع الأسعار المعدلة ==========
def load_data():
    if os.path.exists(USERNAMES_FILE):
        with open(USERNAMES_FILE, "r") as f:
            return json.load(f)
    return {
        "@btcfx3": {"sold": False, "price": 30},
        "@btcfx5": {"sold": False, "price": 30},
        "@usdex1": {"sold": False, "price": 30},
        "@ethnx1": {"sold": False, "price": 30},
        "@euros3": {"sold": False, "price": 30},
        "@cpius1": {"sold": False, "price": 30},
        "@purr3": {"sold": False, "price": 30},
        "@Pufi3": {"sold": False, "price": 30},
        "@Moch5": {"sold": False, "price": 30},
        "@Proof": {"sold": False, "price": 300},
        "@Chamb": {"sold": False, "price": 300},
        "@strong": {"sold": False, "price": 300},
        "@claws": {"sold": False, "price": 200},
    }

usernames = load_data()
sales_log = []
user_langs = {}

# ========== حفظ البيانات ==========
def save_usernames():
    with open(USERNAMES_FILE, "w") as f:
        json.dump(usernames, f, indent=2)

def save_sales_log():
    with open(SALES_LOG_FILE, "w") as f:
        json.dump(sales_log, f, indent=2)

def save_user_langs():
    with open(USER_LANGS_FILE, "w") as f:
        json.dump(user_langs, f)

# ========== إعداد البوت ==========
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# ========== اختيار اللغة ==========
@router.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇸🇦 العربية", callback_data="lang_ar")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
    ])
    await message.answer("يرجى اختيار لغتك:\nPlease choose your language:", reply_markup=keyboard)
@router.callback_query(lambda c: c.data.startswith("lang_"))
async def language_chosen(callback: CallbackQuery):
    lang = callback.data.replace("lang_", "")
    user_langs[str(callback.from_user.id)] = lang
    save_user_langs()
    if lang == "ar":
        await callback.message.answer("✅ تم اختيار اللغة! أرسل /menu للمتابعة.")
    else:
        await callback.message.answer("✅ Language selected! Send /menu to continue.")

# ========== القائمة الرئيسية ==========
@router.message(Command("menu"))
async def main_menu(message: types.Message):
    lang = user_langs.get(str(message.from_user.id), "en")
    buttons = [[InlineKeyboardButton(text="🛒 شراء يوزرات" if lang == "ar" else "🛒 Buy Usernames", callback_data="buy")]]
    if message.from_user.id == OWNER_ID:
        buttons.append([InlineKeyboardButton(text="⚙️ إدارة اليوزرات", callback_data="admin")])
    text = "اختر خيارًا:" if lang == "ar" else "Choose an option:"
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# ========== عرض اليوزرات ==========
@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_handler(callback: CallbackQuery):
    username = callback.data.replace("buy_", "")
    data = usernames.get(username)

    if not data or data["sold"]:
        await callback.message.answer("❌ هذا اليوزر تم بيعه بالفعل." if user_langs.get(str(callback.from_user.id), "en") == "ar" else "❌ This username has already been sold.")
        return

    price = data["price"]
    pay_url = f"https://tonkeeper.com/transfer/{TON_WALLET}?amount={price}"

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 الدفع الآن" if user_langs.get(str(callback.from_user.id), "en") == "ar" else "🚀 Pay Now", url=pay_url)],
        [InlineKeyboardButton(text="✅ تم الدفع" if user_langs.get(str(callback.from_user.id), "en") == "ar" else "✅ Paid", callback_data=f"confirm_{username}")],
        [InlineKeyboardButton(text="❌ إلغاء" if user_langs.get(str(callback.from_user.id), "en") == "ar" else "❌ Cancel", callback_data=f"cancel_{username}")]
    ])

    lang = user_langs.get(str(callback.from_user.id), "en")
    if lang == "ar":
        message_text = f"💼 لقد اخترت {username}\n\nاضغط على الزر أدناه للدفع <b>{price} TON</b>.\nبعد الدفع، اضغط \"تم الدفع\" لإبلاغ البائع."
    else:
        message_text = f"💼 You chose {username}\n\nClick the button below to pay <b>{price} TON</b>.\nAfter payment, click \"Paid\" to notify the seller."

    await callback.message.answer(message_text, reply_markup=confirm_keyboard)

# ========== تفاصيل الدفع ==========
@router.callback_query(lambda c: c.data == "buy")
async def show_usernames(callback: CallbackQuery):
    lang = user_langs.get(str(callback.from_user.id), "en")
    buttons = []
    for username, data in usernames.items():
        status = "✅" if not data["sold"] else "❌"
        label = (
            f"{username} - {data['price']} TON {status}"
            if lang == "en"
            else f"{username} - {data['price']} تون {status}"
        )
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"buy_{username}")])

    title = "🧾 Available Usernames:" if lang == "en" else "🧾 اليوزرات المتاحة:"
    await callback.message.answer(title, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
# ========== تأكيد الدفع ==========
@router.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_handler(callback: CallbackQuery):
    username = callback.data.replace("confirm_", "")
    if username not in usernames or usernames[username]["sold"]:
        await callback.message.answer("⚠️ هذا اليوزر تم بيعه.")
        return
    usernames[username]["sold"] = True
    save_usernames()

    buyer = callback.from_user.username or f"ID:{callback.from_user.id}"
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sales_log.append({"username": username, "buyer": buyer, "time": time_now})
    save_sales_log()

    await callback.message.answer("✅ تم التأكيد، سيتم التواصل معك قريبًا.")
    await bot.send_message(OWNER_ID, f"📢 تم تأكيد الدفع لليوزر {username} من {buyer} في {time_now}")

# ========== إلغاء الطلب ==========
@router.callback_query(lambda c: c.data.startswith("cancel_"))
async def cancel_handler(callback: CallbackQuery):
    username = callback.data.replace("cancel_", "")
    await callback.message.answer(f"❌ تم إلغاء الطلب على {username}.")

# ========== إدارة اليوزرات (للمالك فقط) ==========
@router.callback_query(lambda c: c.data == "admin")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        return
    await callback.message.answer("أوامر الإدارة:\n/add @username السعر\n/remove @username\n/price @username السعر")

@router.message(Command("add"))
async def add_username(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    parts = message.text.strip().split()
    if len(parts) != 3 or not parts[1].startswith("@"):
        await message.answer("❗ Usage: /add @username السعر")
        return
    username = parts[1]
    try:
        price = int(parts[2])
    except:
        await message.answer("❗ السعر غير صالح.")
        return
    usernames[username] = {"sold": False, "price": price}
    save_usernames()
    await message.answer(f"✅ تمت إضافة {username} بسعر {price} TON")

@router.message(Command("remove"))
async def remove_username(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].startswith("@"):
        await message.answer("❗ Usage: /remove @username")
        return
    username = parts[1]
    if username in usernames:
        del usernames[username]
        save_usernames()
        await message.answer(f"🗑️ تم حذف {username}")
    else:
        await message.answer("⚠️ اليوزر غير موجود")

@router.message(Command("price"))
async def change_price_handler(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    parts = message.text.strip().split()
    if len(parts) != 3 or not parts[1].startswith("@"):
        await message.answer("❗ Usage: /price @username السعر")
        return
    username = parts[1]
    try:
        new_price = int(parts[2])
    except:
        await message.answer("❗ السعر غير صالح.")
        return
    if username in usernames:
        usernames[username]['price'] = new_price
        save_usernames()
        await message.answer(f"✅ تم تحديث سعر {username} إلى {new_price} TON")
    else:
        await message.answer("⚠️ اليوزر غير موجود")

# ========== تسجيل الراوتر ==========
dp.include_router(router)

# ========== تشغيل البوت ==========
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
