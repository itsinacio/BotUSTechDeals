import asyncio
from playwright.async_api import async_playwright
from functions.functionsTelegram import send_mensageAmazon

async def fluxo_completo_amazon():
    print("🤖 Iniciando o robô explorador com navegação humana...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(viewport={'width': 1366, 'height': 768})
        page = await context.new_page()
        
        try:
            print("🌐 1. Acessando a Amazon Brasil...")
            await page.goto("https://www.amazon.com.br/deals?ref_=sxts_snpl_1_1_14f7938a-9291-4655-b3ab-0ee66c377c3d")

            print("📂 2. Filtrando pelo Departamento 'Computadores e Informática'...")
            await page.get_by_test_id("discount-asin-grid").get_by_text("Departamento").is_visible()
            await page.get_by_text("Ver mais").nth(1).click()
            await page.locator("label").filter(has_text="Computadores e Informática").click()
            
            print("🎛️ 3. Procurando filtro de Desconto...")
            await page.get_by_text("Filtrado por").is_visible()
            try:
                filtro_desconto = page.get_by_role("slider", name="Desconto mínimo")
                if await filtro_desconto.is_visible():
                    await filtro_desconto.fill("20")
                else:
                    print("⚠️ Slider de desconto não encontrado como texto, prosseguindo com os resultados atuais...")
            except:
                print("⚠️ Não foi possível aplicar o filtro de 20-80% automaticamente.")

            await page.wait_for_selector('div[data-testid="product-card"]', state="visible")

            print("\n🚀 4. Iniciando varredura com Data-Index e Go Back...")
            
            data_index_atual = 0
            produtos_enviados = 0

            while True:
                linha_seletor = f'div[data-index="{data_index_atual}"]'
                linha_atual = page.locator(linha_seletor)

                # Se a linha não estiver visível, da o scroll
                if not await linha_atual.is_visible():
                    print(f"🔄 Linha {data_index_atual} oculta. Dando scroll")
                    await page.mouse.wheel(0, 600) 
                    await page.wait_for_timeout(1000)

                    if not await linha_atual.is_visible():
                        print(f"🛑 Fim da lista alcançado! O data-index {data_index_atual} não carregou.")
                        break

                # Garante que a linha está no meio da tela
                await linha_atual.scroll_into_view_if_needed()

                # Quanto produtos tem no data-index
                produtos_seletor = f'{linha_seletor} div[class*="GridItem-module__container"]'
                qtd_produtos = await page.locator(produtos_seletor).count()
                
                print(f"\n📦 Lendo [Data-Index: {data_index_atual}] - Encontrou {qtd_produtos} produtos.")

                # Itera sobre cada produto da linha atual
                for i in range(qtd_produtos):
                    print(f"  ➡️ Processando produto {i+1} de {qtd_produtos}...")
                    
                    produto_atual = page.locator(produtos_seletor).nth(i)
                    await produto_atual.scroll_into_view_if_needed()
                    
                    try:
                        imagem_tag = produto_atual.locator('img').first
                        imagem_url = await imagem_tag.get_attribute('src')
                    except Exception as e:
                        imagem_url = "Imagem não encontrada"
                    
                    print("🖱️ Clicando e entrando na página do produto...")
                    await produto_atual.click()
                    
                    try:
                        await page.wait_for_selector('#productTitle', timeout=10000)
                        
                        link_completo = page.url
                        nome = await page.locator('#productTitle').inner_text()
                        nome = nome.strip()
                        
                        try:
                            preco_novo = await page.locator('#corePriceDisplay_desktop_feature_div').inner_text()
                        except:
                            preco_novo = "Preço não encontrado"
                            
                        try:
                            preco_antigo = await page.locator(".a-section.a-spacing-small.aok-align-center").first.inner_text()
                            preco_antigo = preco_antigo.replace("De:", "").strip()
                            preco_antigo = " ".join(preco_antigo.split())
                        except:
                            preco_antigo = "Sem preço antigo"

                        print(f"✅ SUCESSO, Produto {data_index_atual} de {i}|{qtd_produtos}")
                        
                        inforProduto = (
                            f"{nome}\n"
                            f"Preço Antigo: {preco_antigo}\n"
                            f"Preço Novo: {preco_novo}\n"
                            f"Link: {link_completo}\n"
                            f"Link imagem:{imagem_url}"
                        )
                        
                        await send_mensageAmazon(inforProduto, imagem_url)
                        print("📩 Mensagem enviada para o Telegram!")
                        produtos_enviados += 1
                        
                        await asyncio.sleep(8)

                    except Exception as e:
                        print(f"❌ Erro ao raspar dados deste produto: {e}")
                    
                    finally:
                        # --- A HORA DO GO BACK ---
                        print("🔙 Retornando à lista de ofertas...")
                        await page.go_back()
                        
                        # Espera a linha que estávamos lendo voltar a ficar visível
                        await page.wait_for_selector(linha_seletor, state="visible", timeout=15000)
                        await page.wait_for_timeout(1000) # Um leve delay para garantir a renderização
                
                data_index_atual += 1

        except Exception as e:
            print(f"\n❌ Ocorreu um erro no meio do caminho: {e}")
        
        finally:
            print(f"\n🎉Foram {produtos_enviados} produtos raspados e enviados.")
            await browser.close()
            print("🛑 Navegador fechado.")

if __name__ == "__main__":
    asyncio.run(fluxo_completo_amazon())