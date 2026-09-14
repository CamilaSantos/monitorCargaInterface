import re
import unicodedata
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


def normalizar_texto(texto: str) -> str:
  """Normaliza caracteres HTML especiais como \\xa0 (&nbsp;) para espaços simples."""
  if not texto:
    return ""
  # Substitui espaço inquebrável por espaço comum e limpa espaços extras
  texto_limpo = unicodedata.normalize("NFKC", texto)
  return re.sub(r"\s+", " ", texto_limpo).strip()


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_contexto_menu(self):
    """Localiza o contexto (página ou frame) que contém os menus atualizados."""
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
    """Navega dinamicamente tratando automaticamente &nbsp; (\\xa0), sufixos e refreshes do Protheus."""
    print(f"\n[NAVEGAÇÃO] Iniciando sequência de menus: {list(niveis_menu)}")

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

      nome_limpo = normalizar_texto(item_nome)

      # TRATAMENTO DO \xa0 / &nbsp;: O Regex \s+ aceita tanto espaço comum quanto \xa0 do HTML
      palavras = [re.escape(p) for p in nome_limpo.split(" ")]
      padrao_regex_flexivel = re.compile(r"\s+".join(palavras), re.IGNORECASE)

      item_encontrado = False
      tentativas = 3

      for tentativa in range(1, tentativas + 1):
        contexto = self._obter_contexto_menu()

        # Busca flexível por qualquer tag de menu que contenha a palavra normalizada
        item_locator = contexto.locator(
            "wa-menu-item, cwa-menu-item, span.caption"
        ).filter(has_text=padrao_regex_flexivel).first

        try:
          item_locator.wait_for(state="visible", timeout=8000)
          item_locator.scroll_into_view_if_needed()

          print(
              f"  └─ [OK] Clicando no menu (Nível {nivel_idx}): '{nome_limpo}'"
              f" (Tentativa {tentativa})"
          )
          item_locator.click()

          item_encontrado = True
          break

        except PlaywrightTimeoutError:
          print(
              f"  ├─ [AGUARDANDO REFRESH] Nível {nivel_idx} ('{nome_limpo}'),"
              f" aguardando estabilização... ({tentativa}/{tentativas})"
          )
          self.page.wait_for_timeout(1500)

      if not item_encontrado:
        contexto = self._obter_contexto_menu()
        try:
          # Exibe no log a lista com os textos limpos para facilitar a leitura no console
          menus_detectados = [
              normalizar_texto(txt)
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
            f"   - Menus visíveis normalizados no DOM: {menus_detectados}"
        )

      self.page.wait_for_timeout(2500)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")