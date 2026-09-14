import re
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_contexto_menu(self):
    """Retorna o contexto (página ou frame) que contém os menus atualizados."""
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
    """Navega dinamicamente lidando com o refresh do painel central entre cada clique."""
    print(f"\n[NAVEGAÇÃO] Iniciando sequência de menus: {list(niveis_menu)}")

    # ESPERA CRÍTICA INICIAL
    try:
      self.page.wait_for_selector(
          "wa-menu-item, cwa-menu-item", state="attached", timeout=60000
      )
    except PlaywrightTimeoutError:
      raise RuntimeError(
          "❌ FALHA DE CARREGAMENTO: Os menus não carregaram a tempo após o"
          " login."
      )

    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = item_nome.strip()
      padrao_flexivel = re.compile(rf"{re.escape(nome_limpo)}", re.IGNORECASE)

      # -------------------------------------------------------------------
      # TRATAMENTO DO REFRESH: Tentativas com reconexão ao DOM recarregado
      # -------------------------------------------------------------------
      item_encontrado = False
      tentativas = 3

      for tentativa in range(1, tentativas + 1):
        contexto = self._obter_contexto_menu()

        # Localiza o elemento atualizado pós-refresh
        item_locator = contexto.locator(
            "wa-menu-item, cwa-menu-item, span.caption"
        ).filter(has_text=padrao_flexivel).first

        try:
          # Aguarda o elemento existir e ficar visível na tela pós-refresh
          item_locator.wait_for(state="visible", timeout=8000)

          # Rola e executa o clique
          item_locator.scroll_into_view_if_needed()
          print(
              f"  └─ [OK] Clicando no menu (Nível {nivel_idx}): '{nome_limpo}'"
              f" (Tentativa {tentativa})"
          )
          item_locator.click()

          item_encontrado = True
          break  # Clique realizado com sucesso!

        except PlaywrightTimeoutError:
          # Se falhar pela transição do refresh, aguarda 1.5s antes da próxima tentativa
          print(
              f"  ├─ [AGUARDANDO REFRESH] Nível {nivel_idx} ('{nome_limpo}'),"
              f" aguardando estabilização do painel... ({tentativa}/{tentativas})"
          )
          self.page.wait_for_timeout(1500)

      # Se após todas as tentativas o menu não foi clicado, lança exceção detalhada
      if not item_encontrado:
        contexto = self._obter_contexto_menu()
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
            f"❌ MENU NÃO ENCONTRADO PÓS-REFRESH no Nível {nivel_idx}:"
            f" '{nome_limpo}'.\n"
            f"   - Nome buscado no .env: '{nome_limpo}'\n"
            f"   - Menus visíveis no DOM atual: {menus_detectados}"
        )

      # PAUSA PÓS-CLIQUE: Aguarda o término da animação/refresh do painel central
      self.page.wait_for_timeout(2500)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")