import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def send_mensage(Mensage: str):
    # Função para enviar mensagem para o canal simples
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(chat_id=CHAT_ID, text=Mensage, parse_mode="Markdown")
        print("✅  OK")
        
    except Exception as e:
        print(f"❌  {e}")
        
    finally:
        await bot.session.close()