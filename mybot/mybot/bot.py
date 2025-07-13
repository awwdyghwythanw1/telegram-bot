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
TOKEN = "YOUR_BOT_TOKEN_HERE"  # ← حط التوكن الحقيقي هنا
OWNER_ID = 7928004645  # ← عدّل ID حسب حسابك
TON_WALLET = "UQAvKW2nLoNs3Tj2P_ZB-yZSH8FzrBcPxlDT0UoZJJjj3h8l"

# ========== ملفات البيانات ==========
USERNAMES_FILE = "usernames.json"
SALES_LOG_FILE = "sales_log.json"

default_usernames = {
    "@btcfx3": False,
    "@btcfx5": False,
    "@usdex1": False,
    "@ethnx1": False,
    "@euros3": False,
    "@cpius1": False,
    "@purr3": False,
    "@Pufi3": False,
    "@Moch5": False,
}

# تحميل اليوزرات من ملف أو استخدام الافتراضي
if os.path.exists(USERNAMES_FILE):
    with open(USERNAMES_FILE, "r") as f:
        usernames = json.load(f)
else:
    usernames = default_usernames.copy()

# تحميل سجل المبيعات
if os.path.exists(SALES_LOG_FILE):
    with open(SALES_LOG_FILE, "r") as f:
        sales_log = json.load(f)
else:
    sales_log = []

# حفظ اليوزرات
def save_usernames():
    with open(USERNAMES_FILE, "w") as f:
        json.dump(usernames, f)

# حفظ السجل
def save_sales_log():
    with open(SALES_LOG_FILE, "w") as f:
        json.dump(sales_log, f, indent=2)

# ========== إعداد البوت ==========
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# أمر /start
@router.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Buy Usernames", callback_data="buy_usernames")],
        [InlineKeyboardButton(text="📊 Check Commission", callback_data="commission")]
    ])
    await message.answer("👋 Welcome! You can purchase available usernames from the seller using this bot.", reply_markup=keyboard)

# عرض العمولة
@router.callback_query(lambda c: c.data == "commission")
async def commission_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("💰 The seller's price is: <b>30 TON</b> per username.\nPlease make sure to pay before confirming.")

# عرض اليوزرات المتوفرة
@router.callback_query(lambda c: c.data == "buy_usernames")
async def show_usernames(callback: CallbackQuery):
    await callback.answer()
    buttons = []
    for username, sold in usernames.items():
        label = f"{username} (SOLD)" if sold else username
        status = "❌" if sold else "✅"
        buttons.append([InlineKeyboardButton(text=f"{label} {status}", callback_data=f"buy_{username}")])
    await callback.message.answer("🧾 Available usernames:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# عند اختيار يوزر
@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_handler(callback: CallbackQuery):
    await callback.answer()
    username = callback.data.replace("buy_", "")
    if usernames.get(username):
        await callback.message.answer("❌ Sorry, this username has already been sold.")
        return

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ I have paid", callback_data=f"confirm_{username}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data=f"cancel_{username}")]
    ])

    text = (
        f"💼 You selected <b>{username}</b>\n\n"
        f"Please send <b>30 TON</b> to the seller's wallet:\n"
        f"<code>{TON_WALLET}</code>\n\n"
        "After sending the payment, click <b>'I have paid'</b> to notify the seller."
    )
    await callback.message.answer(text, reply_markup=confirm_keyboard)

# عند الضغط "تم الدفع"
@router.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_payment(callback: CallbackQuery):
    await callback.answer()
    username = callback.data.replace("confirm_", "")

    if usernames.get(username):
        await callback.message.answer("⚠️ This username was already marked as sold.")
        return

    usernames[username] = True
    save_usernames()

    buyer = callback.from_user.username or f"ID:{callback.from_user.id}"
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sales_log.append({
        "username": username,
        "buyer": buyer,
        "time": time_now
    })
    save_sales_log()

    await callback.message.answer("✅ Payment confirmed. The seller has been notified.")
    await bot.send_message(OWNER_ID, f"📢 Buyer @{buyer} confirmed payment for {username} at {time_now}.")

# عند الضغط "إلغاء الطلب"
@router.callback_query(lambda c: c.data.startswith("cancel_"))
async def cancel_handler(callback: CallbackQuery):
    await callback.answer()
    username = callback.data.replace("cancel_", "")
    await callback.message.answer(f"❌ You have canceled the request for {username}.")

# أمر /add لإضافة يوزر
@router.message(Command("add"))
async def add_username_handler(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].startswith("@"):
        await message.answer("❗ Usage: /add @username")
        return

    new_username = parts[1]
    if new_username in usernames:
        await message.answer("⚠️ Username already exists.")
    else:
        usernames[new_username] = False
        save_usernames()
        await message.answer(f"✅ Username {new_username} added.")

# أمر /remove لحذف يوزر
@router.message(Command("remove"))
async def remove_username_handler(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].startswith("@"):
        await message.answer("❗ Usage: /remove @username")
        return

    target_username = parts[1]
    if target_username in usernames:
        del usernames[target_username]
        save_usernames()
        await message.answer(f"🗑️ Username {target_username} removed.")
    else:
        await message.answer("⚠️ Username not found.")

# تشغيل الراوتر
dp.include_router(router)

# بدء البوت
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
