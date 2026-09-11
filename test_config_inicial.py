from playwright.sync_api import Page, expect

def test_validar_titulo(page: Page):
    page.goto("https://automationexercise.com")
    
    # 1. Estratégia por texto (Mais resiliente no Playwright)
    titulo_locator = page.locator("h1:has-text('Automation')").first
    
    # 2. Garante que o elemento está visível antes de tentar ler
    titulo_locator.wait_for(state="visible", timeout=10000)
    
    # 3. Validação do texto unificado ("Automation" + "Exercise")
    expect(titulo_locator).to_contain_text("Automation")
    
    # Exibe no terminal o texto capturado
    print(f"Texto capturado: {titulo_locator.inner_text()}")