import asyncio
import random
from playwright.async_api import async_playwright
from time import sleep
from functions.functionsTelegram import send_mensageAmazon 

endpoints = []
maxNoSourceEndpoint = 0

async def capturarEndpoints(response):
    global maxNoSourceEndpoint
    # Verifica se é o endpoint de produtos e se a requisição deu sucesso (HTTP 200)
    if "/api/v1/products/search" in response.url and response.status == 200:
        try:
            dados_json = await response.json()
            endpoints.append(dados_json)
            print(f"Sucesso! Bloco de produtos interceptado. Total na lista: {len(endpoints)}")
            # Zera o contador de "tentativas falhas" toda vez que acha dados novos
            maxNoSourceEndpoint = 0
        except Exception as e:
            # Ignora erros de parse de JSON silenciosamente
            pass

async def fluxo_completo_amazon():
    global maxNoSourceEndpoint
    produtos_enviados = 0
    
    print("🤖 Iniciando o robô explorador em modo invisível (Headless)...")
    
    async with async_playwright() as p:
        # PROTEÇÃO 1: Headless True e remoção da flag de Automação
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )
        
        # PROTEÇÃO 2: Disfarce de usuário real rodando no Brasil
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            java_script_enabled=True
        )
        
        page = await context.new_page()
        
        # PROTEÇÃO 3: Apagar o rastro de "webdriver" do navegador
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            print("🌐 1. Acessando a Amazon Brasil...")
            await page.goto("https://www.amazon.com.br/deals?ref_=sxts_snpl_1_1_14f7938a-9291-4655-b3ab-0ee66c377c3d")

            print("📂 2. Filtrando pelo Departamento 'Computadores e Informática'...")
            await page.get_by_test_id("discount-asin-grid").get_by_text("Departamento").is_visible()
            await page.get_by_text("Ver mais").nth(1).click()
            await page.locator("label").filter(has_text="Computadores e Informática").click()
            
            print("🎛️ 3. Configurando listener e procurando filtro de Desconto...")
            # Começa a ouvir o tráfego de rede ANTES de dar os scrolls
            await page.get_by_text("Filtrado por").is_visible()
            
            try:
                filtro_desconto = page.get_by_role("slider", name="Desconto mínimo")
                if await filtro_desconto.is_visible():
                    page.on("response", capturarEndpoints)
                    await filtro_desconto.fill("20")
                else:
                    print("⚠️ Slider de desconto não encontrado como texto, prosseguindo...")
            except:
                print("⚠️ Não foi possível aplicar o filtro de desconto automaticamente.")

            # Espera garantir que a vitrine carregou antes de começar o loop
            await page.wait_for_selector('div[data-testid="product-card"]', state="visible")

            print("🕵️‍♂️ 4. Capturando produtos via endpoint e simulando scroll...")
            verMais = page.get_by_text("Ver mais ofertas")
            
            while True:
                # PROTEÇÃO 4: Scroll dinâmico (nunca é a mesma distância exata)
                await page.mouse.wheel(0, random.randint(800, 1200)) 
                
                # PROTEÇÃO 5: Pausa humana antes de verificar as coisas
                await page.wait_for_timeout(random.randint(800, 1500))
                
                maxNoSourceEndpoint += 1
                
                if await verMais.is_visible():
                    await page.wait_for_timeout(random.randint(300, 800)) # Pausa para "olhar" o botão
                    await verMais.click()
                    await page.get_by_test_id("load-more-spinner").wait_for(state="hidden")
                
                # Se após 15 scrolls não interceptar nenhum pacote de produto novo, a página acabou
                if maxNoSourceEndpoint >= 15:
                    print("🛑 Fim da página alcançado ou sem novos produtos.")
                    break
                    
        except Exception as e:
            print(f"\n❌ Ocorreu um erro no meio do caminho: {e}")
        
        finally:
            print(f"\n🎉 Foram capturados {len(endpoints)} pacotes de endpoints.")
            await browser.close()
            print("🛑 Navegador fechado.")
        for json in endpoints:
            listaProdutos = json['products']
            for produto in listaProdutos:
                try:
                    nome = produto['title']
                    precoAntigo = produto['price']['basisPrice']['price']
                    precoNovo = produto['price']['priceToPay']['price']
                    urlImagem = produto['image']['hiRes']['baseUrl'] + ".jpg"
                    urlVenda = "https://www.amazon.com.br/"+ produto['link']
                    desconto = produto["dealBadge"]["label"]["content"]["fragments"][0]["text"]
                    copy = f'<b>​{nome}</b>\n\n❌<s>​De: R${precoAntigo}</s>\n💥​<b>​Por:R${precoNovo}</b>(-{desconto})\n\n🛒<a href="{urlVenda}">Clique para comprar</a>'
                    await send_mensageAmazon(copy,urlImagem)
                    sleep(3)
                except:
                    print("Faltou algo")


if __name__ == "__main__":
    asyncio.run(fluxo_completo_amazon())