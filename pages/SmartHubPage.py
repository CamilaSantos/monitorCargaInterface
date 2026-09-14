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
            frame.locator(
                "po-menu, .po-menu-container, po-menu-item, #driver-popover-item"
            ).count()
            > 0
        ):
          return frame
      except Exception:
        continue

    iframe_element = self.page.locator("iframe").first
    if iframe_element.count() > 0:
      return iframe_element.content_frame
    return self.page

  def fechar_tutorial_se_existir(self, tempo_espera_ms: int = 3000):
    """Identifica o pop-up de tutorial/onboarding (driver.js) e clica no botão 'X' (fechar)."""
    frame = self._obter_frame_po_ui()

    # Seletor do popover do driver.js
    popover = frame.locator(
        "#driver-popover-item, div[id*='driver-popover'], .driver-popover"
    )

    try:
      # Aguarda uma breve Janela para ver se o onboarding aparece na tela
      popover.first.wait_for(state="visible", timeout=tempo_espera_ms)

      # Mapeamento dos seletores do botão fechar ('X')
      btn_fechar = popover.locator(
          ".driver-close-btn, button.driver-close-btn, [aria-label='Close'],"
          " .driver-popover-close-btn"
      ).first

      if btn_fechar.count() > 0 and btn_fechar.is_visible():
        btn_fechar.click(force=True)
        print("  └─ [OK] Tutorial/Onboarding fechado com sucesso.")

        # Aguarda o elemento sumir e a tela reestabilizar
        self.page.wait_for_timeout(1000)
    except PlaywrightTimeoutError:
      # Caso o usuário já tenha acessado anteriormente e o tutorial não apareça
      pass

  def selecionar_menu_interno(self, nome_item: str):
    """Clica nos itens do menu lateral do PO UI e trata pop-ups de tutorial."""
    nome_limpo = sanitizar_texto(nome_item)
    print(f"\n[SMART HUB] Navegando no menu interno para: '{nome_limpo}'")

    self.page.wait_for_timeout(2000)
    frame = self._obter_frame_po_ui()

    padrao_regex = re.compile(rf"^\s*{re.escape(nome_limpo)}\s*$", re.IGNORECASE)

    candidatos = frame.locator("po-menu-item, .po-menu-item-link, a").filter(
        has_text=padrao_regex
    )

    if candidatos.count() == 0:
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

          try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
          except PlaywrightTimeoutError:
            pass

          # Após selecionar o menu, tenta fechar o tutorial caso ele seja disparado
          self.fechar_tutorial_se_existir()
          return

    raise RuntimeError(
        f"❌ ITEM DO SMART HUB NÃO ENCONTRADO: '{nome_limpo}' dentro do"
        " iframe PO UI."
    )