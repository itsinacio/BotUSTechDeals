import asyncio
from main.functions import send_mensage

async def main():
    texto_teste = (
        "🔥 **TESTE DO BOT COM AIOGRAM!**\n\n"
        "O Python está falando com o Telegram de forma assíncrona, "
        "modularizada, junto com uma imagem e super rápida! 🚀"
    )

# Trava de segurança para garantir que o script só roda se for executado diretamente
if __name__ == "__main__":
    asyncio.run(main())