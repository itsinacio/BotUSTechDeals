import asyncio
from playwright.async_api import async_playwright
from main.functions import send_mensage

async def fluxo_completo_amazon():
    print("🤖 Iniciando o robô explorador com navegação humana...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        # Criamos um contexto com tamanho de tela grande para garantir que os menus apareçam
        context = await browser.new_context(viewport={'width': 1366, 'height': 768})
        page = await context.new_page()
        
        try:
            print("🌐  1. Acessando a Amazon Brasil...")
            await page.goto("https://www.amazon.com.br/events/ofertasmensais?ref_=sxts_snpl_1_0_14f7938a-9291-4655-b3ab-0ee66c377c3d")
            
            print("📂  2. Filtrando pelo Departamento 'Computadores e Informática'...")
            # Espera o menu lateral carregar
            await page.wait_for_timeout(2000)
            await page.get_by_text("Ver mais").nth(1).click()
            # Clica em Computadores e Informática
            await page.locator("label").filter(has_text="Computadores e Informática").click()
            
            print("🎛️  3. Procurando filtro de Desconto...")
            # Espera a página atualizar com os computadores
            await page.wait_for_timeout(2000)
            try:
                filtro_desconto = page.get_by_role("slider", name="Desconto mínimo")
                if await filtro_desconto.is_visible():
                    await filtro_desconto.fill("20")
                else:
                    print("⚠️ Slider de desconto não encontrado como texto, prosseguindo com os resultados atuais...")
            except:
                print("⚠️ Não foi possível aplicar o filtro de 20-80% automaticamente.")

            print("📦  4. Extraindo o PRIMEIRO produto da lista...")
            await page.wait_for_timeout(3000) # Espera as fotos carregarem
            
            # Pega o primeiro "card" de produto na tela de resultados
            primeiro_produto = page.locator('div[data-testid="product-card"]').first
            
            # Se o layout da Amazon mudar, tentamos o seletor padrão de grid deles
            if not await primeiro_produto.is_visible():
                primeiro_produto = page.locator('.a-section.a-spacing-base').first
            # Tentando pegar a imagem
            imagem_tag = primeiro_produto.locator('img').first
            imagem_url = await imagem_tag.get_attribute('src')
            
            # Tentando pegar os preços (com tratamento de erro caso não tenha preço antigo)
            try:
                preco_novoAux = await primeiro_produto.locator('.a-price .a-offscreen').first.inner_text()
                preco_novo = preco_novoAux.replace("Preço da Oferta: ","")
            except:
                preco_novo = "Preço não encontrado"
                
            try:
                # O preço antigo costuma ficar numa classe a-text-price
                preco_antigoAux = await primeiro_produto.locator('.a-text-price .a-offscreen').first.inner_text()
                preco_antigo = preco_antigoAux.replace("De: ","")
            except:
                preco_antigo = "Sem preço antigo"
            
            print("🖱️  5. Clicando no produto e entrando na página dele...")
            await primeiro_produto.click()
            await page.wait_for_selector('#productTitle', timeout=10000)
            print("📦  6. Extraindo dados da página do produto...")
            link_completo = page.url
            nome = await page.locator('#productTitle').inner_text()
            nome = nome.strip()
            print("\n✅ SUCESSO! AQUI ESTÃO OS DADOS:")
            print(f"📌 Nome: {nome}")
            print(f"📉 De: {preco_antigo}")
            print(f"💰 Por: {preco_novo}")
            print(f"📸 Imagem: {imagem_url}")
            print(f"🔗 Link: {link_completo}")

            
            mensagem = (
                f"🔥 **OFERTA ENCONTRADA!**\n\n"
                f"💻 **{nome}**\n"
                f"📉 De: {preco_antigo}\n"
                f"💰 **Por: {preco_novo}**\n\n"
                f"🛒 [Compre aqui]({link_completo})"
            )
            await send_mensage(mensagem,imagem_url)
            print("📩 Mensagem enviada para o Telegram!")
            

        except Exception as e:
            print(f"\n❌ Ocorreu um erro no meio do caminho: {e}")
        
        finally:
            await browser.close()
            print("🛑 Navegador fechado.")

if __name__ == "__main__":
    asyncio.run(fluxo_completo_amazon())