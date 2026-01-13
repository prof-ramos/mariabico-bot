from telethon import TelegramClient, events, types
import os
from dotenv import load_dotenv
import asyncio

# Configurações do Telethon fornecidas pelo usuário
API_ID = 29602137
API_HASH = "497eb4906e57de5fc6a992eeb6740489"

load_dotenv()
BOT_USERNAME = "@MariaBicoBot"  # Ou use o link do bot se preferir


async def main():
    client = TelegramClient("mariabico_test", API_ID, API_HASH)
    await client.start()

    print("✅ Conectado ao Telegram como usuário!")

    # Busca o bot
    bot = await client.get_input_entity(BOT_USERNAME)

    print(f"🤖 Enviando /start para {BOT_USERNAME}...")
    await client.send_message(bot, "/start")

    # Aguarda a resposta (timeout de 10s)
    print("⏳ Aguardando resposta do bot no privado...")

    response_msg = None
    for i in range(10):
        await asyncio.sleep(1)
        async for message in client.iter_messages(bot, limit=5):
            if message.sender_id == (await client.get_me()).id:
                continue
            if "MariaBicoBot" in message.text or "Escolha uma opção" in message.text:
                response_msg = message
                break
        if response_msg:
            break

    if not response_msg:
        print("❌ Bot não respondeu ao /start no tempo esperado.")
        return

    print(f"📩 Resposta recebida do bot:\n{response_msg.text}")

    if response_msg.reply_markup:
        print("🔘 O bot enviou botões (teclado inline).")
        # Encontra o botão de curadoria
        button_to_click = None
        if hasattr(response_msg.reply_markup, "rows"):
            for row in response_msg.reply_markup.rows:
                for button in row.buttons:
                    if hasattr(button, "data") and button.data == b"curate_now":
                        button_to_click = button
                        break

        if button_to_click:
            print("👉 Clicando no botão 'Curadoria Agora'...")
            await response_msg.click(data=button_to_click.data)

            print("⏳ Aguardando processamento da curadoria (até 60s)...")
            final_text = ""
            for _ in range(12):  # 12 * 5s = 60s
                await asyncio.sleep(5)
                edited_msg = await client.get_messages(bot, ids=response_msg.id)
                final_text = edited_msg.text
                if "Executando" not in final_text:
                    break
                print("... ainda processando ...")

            print(f"🆕 Estado final da mensagem:\n{final_text}")

            # Teste de conversão de link
            print("\n🔗 Testando conversão de link...")
            await client.send_message(bot, "https://shopee.com.br/product/123/456")
            print("⏳ Aguardando conversão (10s)...")
            await asyncio.sleep(10)
            async for msg in client.iter_messages(bot, limit=1):
                print(f"📩 Resposta da conversão:\n{msg.text}")
        else:
            print("❌ Botão 'Curadoria Agora' não encontrado.")

    # Teste no grupo
    target_group_id = os.getenv("TARGET_GROUP_ID")
    if target_group_id:
        try:
            # Garante prefixo -100 para supergroups
            if not target_group_id.startswith("-100") and target_group_id.startswith(
                "-"
            ):
                group_id_str = "-100" + target_group_id[1:]
            else:
                group_id_str = target_group_id

            group_id = int(group_id_str)
            print(f"🏠 Verificando grupo {group_id}...")

            # Tenta pegar a entidade do grupo
            group = await client.get_entity(group_id)
            print(f"✅ Grupo '{group.title}' encontrado.")

            # Verifica se o bot está no grupo
            participants = await client.get_participants(group)
            bot_in_group = any(
                p.username
                and p.username.lower() == BOT_USERNAME.replace("@", "").lower()
                for p in participants
            )

            if bot_in_group:
                print(f"✅ Bot {BOT_USERNAME} ESTÁ no grupo.")
            else:
                print(f"❌ Bot {BOT_USERNAME} NÃO FOI ENCONTRADO no grupo!")
                print("👉 Por favor, adicione o bot ao grupo manualmente.")

            print("🕒 Últimas mensagens no grupo:")
            async for msg in client.iter_messages(group, limit=5):
                sender = await msg.get_sender()
                sender_name = getattr(sender, "first_name", "Unknown")
                print(
                    f"[{msg.date}] {sender_name}: {msg.text[:50] if msg.text else '[Mídia/Outro]'}"
                )
        except Exception as e:
            print(f"❌ Erro ao verificar grupo: {e}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
