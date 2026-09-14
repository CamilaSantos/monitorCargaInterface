import re
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_contexto_menu(self):
    """Localiza e retorna o contexto (página ou frame) que contém os componentes do menu."""
    # 1. Verifica se os componentes do menu já estão acessíveis na página principal
    if self.page.locator("wa-menu-item").count() > 0:
      return self.page

    # 2. Caso a renderização esteja dentro de um iFrame filho, varre os frames da página
    for frame in self.page.frames:
      try:
        if frame.locator("wa-menu-item").count() > 0:
          return frame
      except Exception:
        continue

    # Retorna o contexto principal por padrão
    return self.page

  def navegar(self, *niveis_menu: str):
    """Atravessa os containers <wa-panel> e clica dinamicamente nos componentes <wa-menu-item>."""
    print(f"\n[NAVEGAÇÃO] Iniciando sequência de menus: {list(niveis_menu)}")

    # 1. ESPERA CRÍTICA: Aguarda que o elemento <wa-menu-item> apareça na árvore DOM
    try:
      self.page.wait_for_selector(
          "wa-menu-item", state="attached", timeout=60000
      )
    except PlaywrightTimeoutError:
      raise RuntimeError(
          "❌ FALHA DE CARREGAMENTO: O componente <wa-menu-item> não foi"
          " localizado no DOM após a seleção do ambiente. Verifique se a página"
          " principal concluiu o carregamento."
      )

    self.page.wait_for_timeout(2000)

    # 2. ITERAÇÃO SOBRE OS NÍVEIS DE MENU
    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = item_nome.strip()

      # Expressão regular flexível para tratar o sufixo numérico injetado pelo Protheus, como (24) ou (10)
      padrao_flexivel = re.compile(rf"{re.escape(nome_limpo)}", re.IGNORECASE)

      contexto = self._obter_contexto_menu()

      # Localiza o wa-menu-item através da árvore de wa-panel sem depender de um seletor pai estático
      item_locator = contexto.locator("wa-menu-item").filter(
          has_text=padrao_flexivel
      ).first

      # A) Validação de presença no DOM
      try:
        item_locator.wait_for(state="attached", timeout=15000)
      except PlaywrightTimeoutError:
        try:
          menus_detectados = [
              txt.strip()
              for txt in contexto.locator("wa-menu-item").all_inner_texts()
              if txt.strip()
          ]
        except Exception:
          menus_detectados = []

        raise RuntimeError(
            f"❌ MENU NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'.\n"
            f"   - Nome buscado no .env: '{nome_limpo}'\n"
            f"   - Itens detectados no contexto atual: {menus_detectados}"
        )

      # B) Interação com o elemento
      try:
        item_locator.scroll_into_view_if_needed()
        item_locator.wait_for(state="visible", timeout=10000)
        print(f"  └─ [OK] Clicando no menu (Nível {nivel_idx}): '{nome_limpo}'")
        item_locator.click()
      except PlaywrightTimeoutError:
        raise RuntimeError(
            f"⚠️ MENU LOCALIZADO MAS NÃO FICOU CLICÁVEL no Nível {nivel_idx}:"
            f" '{nome_limpo}'."
        )

      self.page.wait_for_timeout(1500)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")