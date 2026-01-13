import asyncio
import httpx
import os
from dotenv import load_dotenv


async def update_bot_info():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Erro: TELEGRAM_BOT_TOKEN não encontrado no .env")
        return

    base_url = f"https://api.telegram.org/bot{token}"

    updates = [
        ("setMyName", {"name": "MariBico"}),
        ("setMyDescription", {"description": ""}),
        ("setMyShortDescription", {"short_description": ""}),
        ("deleteMyCommands", {}),
    ]

    async with httpx.AsyncClient() as client:
        for method, params in updates:
            try:
                print(f"Executando {method}...")
                response = await client.post(f"{base_url}/{method}", json=params)
                result = response.json()
                if result.get("ok"):
                    print(f"✅ {method} concluído com sucesso.")
                else:
                    print(f"❌ Erro em {method}: {result.get('description')}")
            except Exception as e:
                print(f"💥 Exceção em {method}: {e}")


if __name__ == "__main__":
    asyncio.run(update_bot_info())
