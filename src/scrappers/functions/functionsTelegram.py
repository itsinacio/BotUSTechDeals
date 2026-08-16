import os
import re
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TAG_AFILIADO = os.getenv("TAG_AFILIADO", "sua_tag-20")  


async def send_mensageAmazon(Mensage: str, Image: str):
    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=Image,
            caption=Mensage,
            parse_mode="HTML",
        )
        print("✅ OK - Mensagem enviada com link formatado!")

    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")

    finally:
        await bot.session.close()