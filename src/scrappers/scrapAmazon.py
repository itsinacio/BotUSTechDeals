import asyncio
import random
import os
from playwright.async_api import async_playwright
from .functions.functionsTelegram import send_mensageAmazon 
from dotenv import load_dotenv
from .database.database import *
import re

endpoints = []
load_dotenv()
TAG_AFILIADO = os.getenv("TAG_AFILIADO_AMAZON")

async def executar_scroll_pagina(page, lista_endpoints, limite_tentativas=15):
    verMais = page.get_by_text("Ver mais ofertas")
    scrolls_sem_dados_novos = 0
    total_pacotes_anterior = len(lista_endpoints)
    
    while True:
        # PROTEÇÃO: Scroll dinâmico com pausa humana
        await page.mouse.wheel(0, random.randint(800, 1200)) 
        await page.wait_for_timeout(random.randint(800, 1500))
        
        # Clica no botão "Ver Mais" se ele aparecer na tela
        if await verMais.is_visible():
            await page.wait_for_timeout(random.randint(300, 800))
            await verMais.click()
        # VERIFICAÇÃO DINÂMICA: Chegaram pacotes novos no vetor?
        total_pacotes_atual = len(lista_endpoints)
        
        if total_pacotes_atual > total_pacotes_anterior:
            # Encontrou produtos novos! Reseta o contador e atualiza a referência
            scrolls_sem_dados_novos = 0
            total_pacotes_anterior = total_pacotes_atual
        else:
            # Nenhum pacote novo interceptado neste scroll
            scrolls_sem_dados_novos += 1
            
        # Se rolar X vezes sem capturar nada novo, encerra esta categoria
        if scrolls_sem_dados_novos >= limite_tentativas:
            break

def extrairASIN(link: str) -> str | None:
    match = re.search(r'/(?:dp|gp/product)/([A-Za-z0-9]{10})', link)
    return match.group(1).upper() if match else None

async def capturarEndpoints(response):
    if "/api/v1/products/search" in response.url and response.status == 200:
        try:
            dados_json = await response.json()
            endpoints.append(dados_json)
        except Exception:
            pass

async def fluxo_completo_amazon():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=["--disable-blink-features=AutomationControlled", "--disable-infobars"]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            java_script_enabled=True
        )
        
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            filtro4Extrelas = page.get_by_test_id("filter-reviewRating-4")
            filtroComputadoresEInfor = page.get_by_test_id("filter-departments-16339927011")
            filtroEletronicosETecno = page.get_by_test_id("filter-departments-16209063011")
            
            await page.goto("https://www.amazon.com.br/")
            await page.get_by_role("link", name="Ofertas do Dia").click()
            await page.get_by_test_id("discount-asin-grid").get_by_text("Departamento").wait_for(state="visible")
            await page.get_by_text("Ver mais").nth(1).click()
            
            # --- CATEGORIA 1: Computadores e Informática ---
            await filtroComputadoresEInfor.click()
            
            # Liga o escutador de rede
            page.on("response", capturarEndpoints)
            
            await filtro4Extrelas.click()
            await page.wait_for_selector('div[data-testid="product-card"]', state="visible")
            
            # Roda o scroll dinâmico passando a lista de endpoints
            await executar_scroll_pagina(page, endpoints)
            
            # Desliga a escuta antes de trocar de aba
            page.remove_listener("response", capturarEndpoints)
            
            # --- CATEGORIA 2: Eletrônicos e Tecnologia ---
            await filtroComputadoresEInfor.click() # Desmarca a anterior se necessário
            
            # Religa a escuta e clica no novo filtro
            page.on("response", capturarEndpoints)
            await filtroEletronicosETecno.click()
            await page.wait_for_timeout(2000)
            
            # Roda o scroll dinâmico novamente
            await executar_scroll_pagina(page, endpoints)
            page.remove_listener("response", capturarEndpoints)

        except Exception as e:
            print(f"\n❌ Ocorreu um erro no meio do caminho: {e}")
        
        finally:
            await browser.close()
    conn = obter_conexao()
    # --- PROCESSAMENTO DOS PRODUTOS E ENVIOS ---
    for json_data in endpoints:
        listaProdutos = json_data.get('products', [])
        for produto in listaProdutos:
            try:
                nome = produto['title']
                
                # Leitura segura usando .get() para evitar KeyErrors silenciosos
                price_dict = produto.get('price', {})
                precoNovo = float(price_dict.get('priceToPay', {}).get('price', 0))
                precoAntigo = float(price_dict.get('basisPrice', {}).get('price', precoNovo))
                
                # Se o preço for 0, pula o item
                if precoNovo == 0:
                    continue
                    
                urlImagem = produto['image']['hiRes']['baseUrl'] + ".jpg"
                link_relativo = produto['link']
                separador = "&" if "?" in link_relativo else "?"
                urlVenda = f"https://www.amazon.com.br{link_relativo}{separador}tag={TAG_AFILIADO}"
                
                desconto_real = round(((precoAntigo - precoNovo) / precoAntigo) * 100) if precoAntigo > 0 else 0
                
                asin = extrairASIN(link_relativo)
                
                # Joga a chamada do banco para uma thread paralela para não congelar o async
                if asin and desconto_real > 0:
                    aprovado = await asyncio.to_thread(
                        validar_oferta,conn, asin, precoNovo, desconto_real, 'amazon'
                    )
                    
                    if aprovado :
                        copy = f'<b>{nome}</b>\n\n❌<s>De: R${precoAntigo:.2f}</s>\n💥<b>Por: R${precoNovo:.2f}</b> (-{desconto_real}%)\n\n🛒<a href="{urlVenda}">Clique para comprar</a>'
                        enviado = await send_mensageAmazon(copy, urlImagem)
                        if enviado:
                            await asyncio.to_thread(
                            salvar_oferta,conn, asin, nome, precoNovo, desconto_real, 'amazon'
                            )
                        await asyncio.sleep(3)
            except Exception as e:
                print(f"⚠️ Erro ao processar '{produto.get('title', 'Desconhecido')[:20]}': {e}")
                continue
    conn.close()

if __name__ == "__main__":
    asyncio.run(fluxo_completo_amazon())