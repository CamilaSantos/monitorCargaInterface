import re
from playwright.sync_api import FrameLocator, Page, TimeoutError as PlaywrightTimeoutError


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  @property
  def protheus_frame(self) -> FrameLocator:
    """Captura dinamicamente o frame ativo do Protheus no wa-webview."""
    return self.page.locator("wa-webview").last.frame_locator("iframe")

  def navegar(self, *niveis_menu: str):
    """Percorre N níveis de menu e fornece um diagnóstico claro caso ocorra erro.

    Exemplo: navegar("Atualizações", "Faturamento", "Pedidos de Venda")
    """
    print(f"\n[NAVEGAÇÃO] Iniciando sequência de menus: {list(niveis_menu)}")

    # 1. DIAGNÓSTICO DO IFRAME / CARREGAMENTO INICIAL
    try:
      print(
          "[NAVEGAÇÃO] Aguardando o carregamento da estrutura do iFrame do"
          " Protheus..."
      )
      self.protheus_frame.locator("body").wait_for(
          state="attached", timeout=30000
      )
    except PlaywrightTimeoutError:
      raise RuntimeError(
          "❌ FALHA DE CARREGAMENTO: O iFrame do Protheus não carregou a tempo "
          "após confirmar o ambiente. A página ainda está processando o login?"
      )

    # Pausa de estabilização pós-login
    self.page.wait_for_timeout(2000)

    # 2. ITERAÇÃO SOBRE OS NÍVEIS DE MENU
    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = item_nome.strip()
      padrao_exato = re.compile(rf"^{re.escape(nome_limpo)}$")

      # Localizador para o texto exato do menu
      item_locator = self.protheus_frame.locator(
          "cwa-menu-item span.caption, .tmenu-item-text", has_text=padrao_exato
      ).first

      # A) Verificar se o elemento existe no DOM (Mesmo que invisível)
      try:
        item_locator.wait_for(state="attached", timeout=15000)
      except PlaywrightTimeoutError:
        # Pega os menus que estão visíveis na tela para nos ajudar no diagnóstico
        menus_visiveis = (
            self.protheus_frame.locator(
                "cwa-menu-item span.caption, .tmenu-item-text"
            )
            .all_inner_texts(timeout=3000)
            if self.protheus_frame.locator(
                "cwa-menu-item span.caption, .tmenu-item-text"
            )
            .first.is_visible()
            else []
        )

        raise RuntimeError(
            f"❌ MENU NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'.\n"
            f"   - O texto no .env está exatamente igual ao menu do Protheus (acentos, maiúsculas)?\n"
            f"   - Menus atualmente visíveis na tela: {menus_visiveis}"
        )

      # B) Verificar se o elemento está Visível e Clicável
      try:
        item_locator.scroll_into_view_if_needed()
        item_locator.wait_for(state="visible", timeout=10000)
        print(f"  └─ [OK] Clicando no menu (Nível {nivel_idx}): '{nome_limpo}'")
        item_locator.click()
      except PlaywrightTimeoutError:
        raise RuntimeError(
            f"⚠️ MENU LOCALIZADO MAS NÃO FICOU VISÍVEL/CLICÁVEL no Nível"
            f" {nivel_idx}: '{nome_limpo}'.\n"
            "   - É muito provável que a página ainda esteja carregando a animação ou"
            " exista um modal/overlay na frente."
        )

      # Pausa necessária para a animação de abertura do submenu
      self.page.wait_for_timeout(1500)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")