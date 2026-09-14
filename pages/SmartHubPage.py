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
  """Clica nos itens do menu lateral do PO UI e trata pop-ups de tutorial de forma rápida e dinâmica."""
  nome_limpo = sanitizar_texto(nome_item)
  print(f"\n[SMART HUB] Navegando no menu interno para: '{nome_limpo}'")

  frame = self._obter_frame_po_ui()
  padrao_regex = re.compile(rf"^\s*{re.escape(nome_limpo)}\s*$", re.IGNORECASE)

  # Busca pelo seletor do menu no PO UI
  candidatos = frame.locator("po-menu-item, .po-menu-item-link, a").filter(
      has_text=padrao_regex
  )

  # Fallback de busca parcial caso não encontre pelo padrão exato
  if candidatos.count() == 0:
    candidatos = frame.locator("po-menu-item, .po-menu-item-link, a").filter(
        has_text=nome_limpo
    )

  try:
    # Aguarda o elemento do menu ficar visível na tela (com limite de 10s), clicando assim que estiver pronto
    elem = candidatos.first
    elem.wait_for(state="visible", timeout=10000)
    elem.scroll_into_view_if_needed()
    elem.click(force=True)
    print(f"  └─ [OK] Item '{nome_limpo}' clicado no Smart Hub.")

    # Tenta fechar o tutorial de onboarding imediatamente após o clique
    self.fechar_tutorial_se_existir()

  except Exception as err:
    raise RuntimeError(
        f"❌ ITEM DO SMART HUB NÃO ENCONTRADO OU INDISPONÍVEL:"
        f" '{nome_limpo}'. Erro: {err}"
    )