import re
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_contexto_menu(self):
    """Localiza o contexto ativo que possui os menus/submenus renderizados."""
    if self.page.locator("wa-menu-item, cwa-menu-item").count() > 0:
      return self.page

    for frame in self.page.frames:
      try:
        if frame.locator("wa-menu-item, cwa-menu-item").count() > 0:
          return frame
      except Exception:
        continue

    return self.page

  def navegar(self, *niveis_menu: str):
    """Navega dinamicamente por N níveis de menu e submenus expansíveis."""
    print(f"\n[NAVEGAÇÃO] Iniciando sequência de menus: {list(niveis_menu)}")

    # 1. ESPERA CRÍTICA INICIAL: Aguarda os menus raiz carregarem no DOM
    try:
      self.page.wait_for_selector(
          "wa-menu-item, cwa-menu-item", state="attached", timeout=60000
      )
    except PlaywrightTimeoutError:
      raise RuntimeError(
          "❌ FALHA DE CARREGAMENTO: Nenhum menu foi localizado no DOM após o"
          " login."
      )

    self.page.wait_for_timeout(2000)

    # 2. ITERAÇÃO SEQUENCIAL PELOS NÍVEIS
    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = item_nome.strip()
      padrao_flexivel = re.compile(rf"{re.escape(nome_limpo)}", re.IGNORECASE)

      contexto = self._obter_contexto_menu()

      # Busca flexível: atinge <wa-menu-item>, <cwa-menu-item> ou o span interior com o texto do submenu
      item_locator = contexto.locator(
          "wa-menu-item, cwa-menu-item, span.caption"
      ).filter(has_text=padrao_flexivel).first

      # A) Validação de presença no DOM
      try:
        # Aguarda até 10s para o submenu expandir e ser anexado
        item_locator.wait_for(state="attached", timeout=10000)
      except PlaywrightTimeoutError:
        try:
          menus_detectados = [
              txt.strip()
              for txt in contexto.locator(
                  "wa-menu-item, cwa-menu-item, span.caption"
              ).all_inner_texts()
              if txt.strip()
          ]
        except Exception:
          menus_detectados = []

        raise RuntimeError(
            f"❌ MENU NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'.\n"
            f"   - Nome buscado: '{nome_limpo}'\n"
            f"   - Submenus detectados após expansão: {menus_detectados}"
        )

      # B) Clique com rolagem automática
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

      # Pausa essencial pós-clique para permitir a animação de abertura do submenu
      self.page.wait_for_timeout(2000)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")