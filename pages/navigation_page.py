import re
from playwright.sync_api import FrameLocator, Page


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  @property
  def protheus_frame(self) -> FrameLocator:
    """Retorna dinamicamente o frame ativo do Protheus via wa-webview."""
    return self.page.locator("wa-webview").last.frame_locator("iframe")

  def navegar(self, *niveis_menu: str):
    """Percorre N níveis de menu passados como argumentos ordenados

    (ex: navegar("Atualizações", "Faturamento", "Pedidos de Venda"))
    """
    for item_nome in niveis_menu:
      # Ignora caso algum item esteja vazio ou nulo
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = item_nome.strip()

      # Expressão regular para garantir a correspondência EXATA do texto do menu
      padrao_exato = re.compile(rf"^{re.escape(nome_limpo)}$")

      # Busca a tag do menu com o texto exato no Shadow DOM/iFrame
      item_locator = self.protheus_frame.locator(
          "cwa-menu-item span.caption", has_text=padrao_exato
      ).first

      # Aguarda o elemento ficar visível no iFrame e executa o clique
      item_locator.wait_for(state="visible", timeout=60000)
      item_locator.click()

      # Pausa técnica necessária para expansão de submenus / carregamento da tela
      self.page.wait_for_timeout(1500)