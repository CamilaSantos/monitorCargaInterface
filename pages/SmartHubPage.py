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
                "po-menu, .po-menu-container, po-menu-item, .driver-popover-close-btn"
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

  def fechar_tutorial_se_existir(self, tempo_espera_ms: int = 5000):
    """Localiza o botão 'X' (button.driver-popover-close-btn) do driver.js e realiza o clique."""
    frame = self._obter_frame_po_ui()

    # Seletor exato extraído do DOM da imagem
    btn_fechar = frame.locator("button.driver-popover-close-btn").first

    try:
      # Aguarda o botão do fechar tutorial surgir na tela
      btn_fechar.wait_for(state="visible", timeout=tempo_espera_ms)

      if btn_fechar.is_visible():
        btn_fechar.click(force=True)
        print("  └─ [OK] Tutorial (driver-popover) fechado com sucesso.")

        # Aguarda a animação de fade do overlay desaparecer
        self.page.wait_for_timeout(1000)
    except PlaywrightTimeoutError:
      # Caso o usuário já tenha acessado e o tutorial não seja exibido
      pass

  def selecionar_menu_interno(self, nome_item: str):
    """Clica no menu lateral do PO UI e encerra o tutorial caso seja acionado."""
    nome_limpo = sanitizar_texto(nome_item)
    print(f"\n[SMART HUB] Navegando no menu interno para: '{nome_limpo}'")

    frame = self._obter_frame_po_ui()
    padrao_regex = re.compile(rf"^\s*{re.escape(nome_limpo)}\s*$", re.IGNORECASE)

    candidatos = frame.locator("po-menu-item, .po-menu-item-link, a").filter(
        has_text=padrao_regex
    )

    if candidatos.count() == 0:
      candidatos = frame.locator("po-menu-item, .po-menu-item-link, a").filter(
          has_text=nome_limpo
      )

    try:
      elem = candidatos.first
      elem.wait_for(state="visible", timeout=10000)
      elem.scroll_into_view_if_needed()
      elem.click(force=True)
      print(f"  └─ [OK] Item '{nome_limpo}' clicado no Smart Hub.")

      # Aguarda 1.5s para renderização do popover do driver.js
      self.page.wait_for_timeout(1500)

      # Trata e fecha a janela de tutorial
      self.fechar_tutorial_se_existir()

    except Exception as err:
      raise RuntimeError(
          f"❌ ITEM DO SMART HUB NÃO ENCONTRADO OU INDISPONÍVEL:"
          f" '{nome_limpo}'. Erro: {err}"
      )