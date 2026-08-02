import asyncio
from functions import send_mensage

async def main():
    texto_teste = (
        "🔥 **TESTE DO BOT COM AIOGRAM!**\n\n"
        "O Python está falando com o Telegram de forma assíncrona, "
        "modularizada e super rápida! 🚀"
    )
    await send_mensage(texto_teste)

# Trava de segurança para garantir que o script só roda se for executado diretamente
if __name__ == "__main__":
    asyncio.run(main())