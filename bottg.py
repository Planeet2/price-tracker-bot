import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart


TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_price_from_db():
    try:
        conn = psycopg2.connect(
            dbname='dns_monitor',
            user='postgres',
            password=os.getenv("DB_PASSWORD"),
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()

       
        query = """
            SELECT DISTINCT ON (p.id) p.name, ph.price
            FROM products p 
            JOIN price_history ph ON p.id = ph.product_id
            ORDER BY p.id, ph.created_at DESC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e: 
        return f"Ошибка БД: {e}"
        
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    data = get_price_from_db()

    if isinstance(data, str):
        await message.answer(data)
    else:
        text = "📢 *Актуальные цены из базы:*\n\n"
        for name, price in data:
            short_name = (name[:50] + '...') if len(name) > 50 else name
            
            text += f"🔹 {short_name}\n💰 *{price} руб.*\n\n"
        
        await message.answer(text, parse_mode="Markdown")
async def main():
    print("🚀 Бот запущен! Напиши /start в Telegram.")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
