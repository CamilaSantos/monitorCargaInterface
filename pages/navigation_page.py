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

    # 1. ESPERA CRÍTICA: Aguarda a tag <wa-menu> estar anexada no DOM do iFrame
    try:
      self.protheus_frame.locator("wa-menu").first.wait_for(
          state="attached", timeout=60000
      )
    except PlaywrightTimeoutError:
      raise RuntimeError(
          "❌ FALHA DE CARREGAMENTO: O componente <wa-menu> não foi encontrado"
          " no iFrame. O ambiente terminou de carregar?"
      )

    self.page.wait_for_timeout(2000)

    # 2. ITERAÇÃO SOBRE OS MENUS
    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = item_nome.strip()
      padrao_exato = re.compile(rf"^{re.escape(nome_limpo)}$", re.IGNORECASE)

      # Mapeamento com base no Inspetor de Elementos das imagens:
      # Busca por <wa-menu-item> verificando o span interior com title ou texto exato
      item_locator = self.protheus_frame.locator("wa-menu-item").filter(
          has=self.protheus_frame.locator(
              "span.caption", has_text=padrao_exato
          )
      ).first

      # Tentativa alternativa se a busca combinada não encontrar de primeira: busca direta na tag ou atributo title
      if item_locator.count() == 0:
        item_locator = self.protheus_frame.locator(
            "wa-menu-item span.caption", has_text=padrao_exato
        ).first

      try:
        item_locator.wait_for(state="attached", timeout=15000)
      except PlaywrightTimeoutError:
        menus_visiveis = (
            self.protheus_frame.locator("wa-menu-item span.caption")
            .all_inner_texts(timeout=3000)
            if self.protheus_frame.locator("wa-menu-item span.caption")
            .first.is_visible()
            else []
        )

        raise RuntimeError(
            f"❌ MENU NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'.\n"
            f"   - Verifique acentuação e grafia no .env.\n"
            f"   - Menus atualmente visíveis na tela: {menus_visiveis}"
        )

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

      self.page.wait_for_timeout(1500)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")