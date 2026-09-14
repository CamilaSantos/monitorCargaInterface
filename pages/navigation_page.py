import re
import unicodedata
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


def sanitizar_texto(texto: str) -> str:
  """Normaliza \\xa0 (&nbsp;) para espaços simples e remove espaços duplicados."""
  if not texto:
    return ""
  texto_limpo = unicodedata.normalize("NFKC", texto)
  return re.sub(r"\s+", " ", texto_limpo).strip()


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_contexto_menu(self):
    """Localiza o contexto ativo que possui os menus renderizados."""
    if self.page.locator("wa-menu-item").count() > 0:
      return self.page

    for frame in self.page.frames:
      try:
        if frame.locator("wa-menu-item").count() > 0:
          return frame
      except Exception:
        continue

    return self.page

  def _localizar_elemento_menu(self, contexto, nome_buscado: str):
    """Varre os elementos wa-menu-item normalizando o texto (resolvendo \\xa0 e contadores como (5))."""
    elementos = contexto.locator("wa-menu-item").all()
    nome_alvo = sanitizar_texto(nome_buscado).lower()

    for elem in elementos:
      texto_bruto = elem.inner_text()
      texto_normalizado = sanitizar_texto(texto_bruto).lower()

      # Remove sufixos como (5), (24) do texto normalizado do elemento para comparação
      texto_sem_contador = re.sub(r"\(\d+\)$", "", texto_normalizado).strip()

      if (
          nome_alvo == texto_sem_contador
          or nome_alvo in texto_normalizado
          or nome_alvo in texto_bruto.lower()
      ):
        return elem

    return None

  def navegar(self, *niveis_menu: str):
    """Navega dinamicamente lidando com \\xa0, contadores e refreshes do Protheus."""
    print(f"\n[NAVEGAÇÃO] Iniciando sequência de menus: {list(niveis_menu)}")

    try:
      self.page.wait_for_selector(
          "wa-menu-item", state="attached", timeout=60000
      )
    except PlaywrightTimeoutError:
      raise RuntimeError(
          "❌ FALHA DE CARREGAMENTO: Os menus não carregaram no DOM a tempo."
      )

    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = sanitizar_texto(item_nome)
      item_encontrado = False
      tentativas = 4

      for tentativa in range(1, tentativas + 1):
        contexto = self._obter_contexto_menu()
        elem_locator = self._localizar_elemento_menu(contexto, nome_limpo)

        if elem_locator and elem_locator.is_visible():
          try:
            elem_locator.scroll_into_view_if_needed()
            print(
                f"  └─ [OK] Clicando no menu (Nível {nivel_idx}): '{nome_limpo}'"
                f" (Tentativa {tentativa})"
            )
            elem_locator.click()
            item_encontrado = True
            break
          except Exception:
            pass

        print(
            f"  ├─ [AGUARDANDO REFRESH] Nível {nivel_idx} ('{nome_limpo}'),"
            f" aguardando estabilização... ({tentativa}/{tentativas})"
        )
        self.page.wait_for_timeout(1500)

      if not item_encontrado:
        contexto = self._obter_contexto_menu()
        try:
          menus_detectados = [
              sanitizar_texto(elem.inner_text())
              for elem in contexto.locator("wa-menu-item").all()
              if elem.is_visible()
          ]
        except Exception:
          menus_detectados = []

        raise RuntimeError(
            f"❌ MENU NÃO ENCONTRADO PÓS-REFRESH no Nível {nivel_idx}:"
            f" '{nome_limpo}'.\n"
            f"   - Nome buscado no .env: '{nome_limpo}'\n"
            f"   - Menus visíveis normalizados: {menus_detectados}"
        )

      # Pausa para permitir a abertura do submenu pós-clique
      self.page.wait_for_timeout(2000)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")