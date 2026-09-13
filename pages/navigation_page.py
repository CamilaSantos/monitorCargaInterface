import re
from playwright.sync_api import (
    FrameLocator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  @property
  def protheus_frame(self) -> FrameLocator:
    """Captura dinamicamente o frame ativo do Protheus no wa-webview."""
    return self.page.locator("wa-webview").last.frame_locator("iframe")

  def navegar(self, *niveis_menu: str):
    """Navega dinamicamente pelos Web Components <wa-menu-item> do Protheus SmartClient HTML."""
    print(f"\n[NAVEGAÇÃO] Iniciando sequência de menus: {list(niveis_menu)}")

    # 1. ESPERA CRÍTICA: Aguarda a presença de qualquer item de menu (<wa-menu-item>) no iFrame
    try:
      self.protheus_frame.locator("wa-menu-item").first.wait_for(
          state="attached", timeout=60000
      )
    except PlaywrightTimeoutError:
      raise RuntimeError(
          "❌ FALHA DE CARREGAMENTO: Nenhum componente <wa-menu-item> foi"
          " encontrado no iFrame após 60 segundos."
      )

    # Pausa técnica para estabilidade da renderização visual
    self.page.wait_for_timeout(2000)

    # 2. ITERAÇÃO SOBRE OS NÍVEIS DE MENU
    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = item_nome.strip()
      padrao_exato = re.compile(rf"^{re.escape(nome_limpo)}$", re.IGNORECASE)

      # Busca pelo <wa-menu-item> que possui o span.caption com o texto correspondente
      item_locator = self.protheus_frame.locator("wa-menu-item").filter(
          has=self.protheus_frame.locator(
              "span.caption", has_text=padrao_exato
          )
      ).first

      # Fallback: Se o filter por span falhar, busca direto no elemento que contém o texto
      if item_locator.count() == 0:
        item_locator = self.protheus_frame.locator(
            "wa-menu-item", has_text=padrao_exato
        ).first

      # A) Verificar se o elemento foi anexado ao DOM
      try:
        item_locator.wait_for(state="attached", timeout=15000)
      except PlaywrightTimeoutError:
        menus_visiveis = (
            self.protheus_frame.locator("wa-menu-item")
            .all_inner_texts(timeout=3000)
            if self.protheus_frame.locator("wa-menu-item").first.is_visible()
            else []
        )

        raise RuntimeError(
            f"❌ MENU NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'.\n"
            f"   - Verifique se a grafia no .env está idêntica à do Protheus.\n"
            f"   - Itens visíveis detectados: {menus_visiveis}"
        )

      # B) Exibir e clicar no item do menu
      try:
        item_locator.scroll_into_view_if_needed()
        item_locator.wait_for(state="visible", timeout=10000)
        print(f"  └─ [OK] Clicando no menu (Nível {nivel_idx}): '{nome_limpo}'")
        item_locator.click()
      except PlaywrightTimeoutError:
        raise RuntimeError(
            f"⚠️ MENU LOCALIZADO MAS NÃO FICOU VISÍVEL/CLICÁVEL no Nível"
            f" {nivel_idx}: '{nome_limpo}'."
        )

      # Pausa necessária para animação de abertura do submenu
      self.page.wait_for_timeout(1500)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")