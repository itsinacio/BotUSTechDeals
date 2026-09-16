import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


async def send_mensageAmazon(Mensage: str, Image: str) -> bool:
    bot = Bot(token=BOT_TOKEN)    
    try:
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=Image,
            caption=Mensage,
            parse_mode="HTML",
        )
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return False

    finally:
        await bot.session.close()