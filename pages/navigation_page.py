from playwright.sync_api import Page


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_frame_ativo(self):
    """Captura o iFrame ativo onde o SmartClient HTML roda."""
    return self.page.locator("wa-webview").last.frame_locator("iframe")

  def navegar_por_caminho_menu(self, *niveis_menu: str):
    """
    Recebe um ou múltiplos nomes de menu/submenu e clica na sequência.
    Exemplo de uso: navegar_por_caminho_menu("Atualizações", "Consultas", "Extração")
    """
    frame = self._obter_frame_ativo()

    # O loop percorre cada texto passado no parâmetro
    for item_nome in niveis_menu:
      # O Playwright busca no DOM a tag <cwa-menu-item> que contenha o <span class="caption"> com o texto exato
      item_locator = frame.locator(
          "cwa-menu-item span.caption", has_text=item_nome
      ).first

      # Aguarda ficar visível no iFrame/Shadow DOM e clica
      item_locator.wait_for(state="visible", timeout=60000)
      item_locator.click()

      # Pausa técnica para permitir a expansão do próximo nível no menu
      self.page.wait_for_timeout(1000)