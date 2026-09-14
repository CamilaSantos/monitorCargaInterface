import re
import unicodedata
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


def sanitizar_texto(texto: str) -> str:
  """Normaliza \\xa0 e espaços do HTML."""
  if not texto:
    return ""
  texto_limpo = unicodedata.normalize("NFKC", texto)
  return re.sub(r"\s+", " ", texto_limpo).strip()


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_contexto(self):
    """Localiza o frame ou página principal onde os componentes estão anexados."""
    for frame in self.page.frames:
      try:
        if frame.locator("wa-text-view, cwa-panel, wa-menu-item").count() > 0:
          return frame
      except Exception:
        continue
    return self.page

  def navegar(self, *niveis_menu: str):
    """Navega clicando no menu lateral (Nível 1) e prosseguindo pelos wa-text-view do painel central."""
    print(f"\n[NAVEGAÇÃO] Iniciando sequência de menus: {list(niveis_menu)}")

    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = sanitizar_texto(item_nome)
      # Regex que tolera o sufixo numérico como (5) e quebras de linha
      padrao_regex = re.compile(
          rf"^\s*{re.escape(nome_limpo)}(\s*\(\d+\))?\s*$", re.IGNORECASE
      )

      # 1. ESPERA DE REFRESH PÓS-CLIKE ANTERIOR
      # Aguarda a rede estabilizar antes de buscar o próximo elemento
      try:
        self.page.wait_for_load_state("networkidle", timeout=5000)
      except PlaywrightTimeoutError:
        pass

      self.page.wait_for_timeout(1500)  # Garante a renderização do Shadow DOM

      clicado = False
      tentativas = 4

      for tentativa in range(1, tentativas + 1):
        contexto = self._obter_contexto()

        # Seletores combinados: menu lateral (para nível 1) e componentes centrais (wa-text-view, cwa-panel)
        seletores_candidatos = [
            "wa-text-view",
            "cwa-panel",
            "wa-panel",
            "wa-menu-item",
            "a",
            "span",
        ]

        for seletor in seletores_candidatos:
          try:
            # Filtra os elementos pelo texto correspondente
            locators = contexto.locator(seletor).filter(has_text=padrao_regex)

            if locators.count() > 0:
              alvo = locators.first
              if alvo.is_visible():
                alvo.scroll_into_view_if_needed()
                print(
                    f"  └─ [OK] Clicando no Nível {nivel_idx} ('{nome_limpo}')"
                    f" via <{seletor}> (Tentativa {tentativa})"
                )

                # Clique forçado bypassa overlays invisíveis do SmartClient
                alvo.click(force=True)
                clicado = True
                break
          except Exception:
            continue

        if clicado:
          break

        print(
            f"  ├─ [AGUARDANDO REFRESH PÓS-CLIQUE] Nível {nivel_idx}"
            f" ('{nome_limpo}')... ({tentativa}/{tentativas})"
        )
        self.page.wait_for_timeout(1500)

      if not clicado:
        raise RuntimeError(
            f"❌ ITEM NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'.\n"
            f"   Não foi possível interagir com o elemento via wa-text-view ou"
            f" wa-menu-item."
        )

      # Aguarda a animação e requisição ADVPL do clique atual finalizar
      self.page.wait_for_timeout(2000)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")