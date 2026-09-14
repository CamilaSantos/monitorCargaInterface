import re
import unicodedata
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


def sanitizar_texto(texto: str) -> str:
  if not texto:
    return ""
  texto_limpo = unicodedata.normalize("NFKC", texto)
  return re.sub(r"\s+", " ", texto_limpo).strip()


class SmartHubPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_frame_po_ui(self):
    """Localiza o iframe interno onde o app Angular com PO UI está rodando."""
    for frame in self.page.frames:
      try:
        if (
            frame.locator("po-menu, .po-menu-container, po-menu-item").count()
            > 0
        ):
          return frame
      except Exception:
        continue

    # Fallback: tenta obter o iframe pelo seletor diretamente
    iframe_element = self.page.locator("iframe").first
    if iframe_element.count() > 0:
      return iframe_element.content_frame
    return self.page

  def selecionar_menu_interno(self, nome_item: str):
    """Clica nos itens do menu lateral do PO UI (ex: 'Carga Inicial', 'Assistente')."""
    nome_limpo = sanitizar_texto(nome_item)
    print(f"\n[SMART HUB] Navegando no menu interno para: '{nome_limpo}'")

    # Aguarda o carregamento do iframe e dos componentes Angular
    self.page.wait_for_timeout(2000)
    frame = self._obter_frame_po_ui()

    padrao_regex = re.compile(rf"^\s*{re.escape(nome_limpo)}\s*$", re.IGNORECASE)

    # Localiza o po-menu-item pelo texto ou label interna
    candidatos = frame.locator("po-menu-item, .po-menu-item-link, a").filter(
        has_text=padrao_regex
    )

    if candidatos.count() == 0:
      # Tenta busca flexível por aproximação
      candidatos = frame.locator("po-menu-item, .po-menu-item-link, a").filter(
          has_text=nome_limpo
      )

    if candidatos.count() > 0:
      for i in range(candidatos.count()):
        elem = candidatos.nth(i)
        if elem.is_visible():
          elem.scroll_into_view_if_needed()
          elem.click(force=True)
          print(f"  └─ [OK] Item '{nome_limpo}' clicado no Smart Hub.")

          # Aguarda o processamento da navegação interna do Angular
          try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
          except PlaywrightTimeoutError:
            pass
          self.page.wait_for_timeout(1500)
          return

    raise RuntimeError(
        f"❌ ITEM DO SMART HUB NÃO ENCONTRADO: '{nome_limpo}' dentro do"
        " iframe PO UI."
    )