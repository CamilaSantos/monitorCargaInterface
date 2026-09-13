from playwright.sync_api import Page


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_frame_ativo(self):
    """Captura o iFrame ativo onde o SmartClient HTML roda."""
    return self.page.locator("wa-webview").last.frame_locator("iframe")

  def navegar_por_caminho_menu(self, *niveis_menu: str):
    """Percorre cada item enviado nos parâmetros e clica na sequência do menu."""
    frame = self._obter_frame_ativo()

    for item_nome in niveis_menu:
      # Ignora caso alguma variável do .env esteja vazia/Nula
      if not item_nome:
        continue

      # Busca a tag do menu com o texto exato no Shadow DOM
      item_locator = frame.locator(
          "cwa-menu-item span.caption", has_text=item_nome
      ).first

      # Aguarda ficar visível no iFrame e executa o clique
      item_locator.wait_for(state="visible", timeout=60000)
      item_locator.click()

      # Pausa técnica para permitir a expansão do submenu
      self.page.wait_for_timeout(1500)

  def navegar_ate_rotina_completa(self, dados_menu: dict):
    """Método orquestrador único.

    Recebe o dicionário da fixture do conftest.py e executa toda a sequência de
    menus.
    """
    self.navegar_por_caminho_menu(
        dados_menu.get("menu_principal"),
        dados_menu.get("submenu"),
        dados_menu.get("rotina_destino"),
    )