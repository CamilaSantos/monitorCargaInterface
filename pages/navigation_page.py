import re
import unicodedata
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


def sanitizar_texto(texto: str) -> str:
  """Normaliza \\xa0 e limpa espaços extras."""
  if not texto:
    return ""
  texto_limpo = unicodedata.normalize("NFKC", texto)
  return re.sub(r"\s+", " ", texto_limpo).strip()


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_contexto_ativo(self):
    """Retorna a página ou iFrame que possui os elementos renderizados."""
    # Se houver frames ativos com conteúdo, varre os frames
    for frame in self.page.frames:
      try:
        if frame.locator(
            "wa-menu-item, a, .caption, div, span"
        ).filter(has_text=re.compile(r"Smart Hub", re.IGNORECASE)).count() > 0:
          return frame
      except Exception:
        continue
    return self.page

  def _clicar_elemento_flexivel(self, contexto, nome_buscado: str) -> bool:
    """Busca o elemento tanto no menu lateral quanto no painel central de opções."""
    nome_limpo = sanitizar_texto(nome_buscado)
    padrao_regex = re.compile(
        rf"^\s*{re.escape(nome_limpo)}(\s*\(\d+\))?\s*$", re.IGNORECASE
    )

    # 1. Tentativa via seletores de menu ou links do painel central
    seletores = [
        # Submenus ou itens de menu lateral
        f"wa-menu-item:has-text('{nome_limpo}')",
        # Links, títulos de blocos ou botões no painel central
        f"a:has-text('{nome_limpo}')",
        f"span:has-text('{nome_limpo}')",
        f"div:has-text('{nome_limpo}')",
    ]

    for seletor in seletores:
      try:
        elementos = contexto.locator(seletor).all()
        for elem in elementos:
          texto_elem = sanitizar_texto(elem.inner_text())

          # Valida se o texto bate exatamente com o nome buscado (ignorando contadores como (5))
          texto_sem_contador = re.sub(r"\(\d+\)$", "", texto_elem).strip()

          if (
              texto_sem_contador.lower() == nome_limpo.lower()
              or nome_limpo.lower() in texto_elem.lower()
          ):
            if elem.is_visible():
              elem.scroll_into_view_if_needed()
              elem.click(force=True)
              return True
      except Exception:
        continue

    # 2. Tentativa fallback com locator via text regex direto no Playwright
    try:
      elem_text = contexto.get_by_text(padrao_regex).first
      if elem_text.is_visible():
        elem_text.click(force=True)
        return True
    except Exception:
      pass

    return False

  def navegar(self, *niveis_menu: str):
    """Navega dinamicamente alternando entre menus laterais e links do painel central."""
    print(f"\n[NAVEGAÇÃO] Iniciando sequência de menus: {list(niveis_menu)}")

    # Aguarda o carregamento inicial da interface
    self.page.wait_for_timeout(3000)

    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = sanitizar_texto(item_nome)
      clicado = False
      tentativas = 5

      for tentativa in range(1, tentativas + 1):
        contexto = self._obter_contexto_ativo()

        if self._clicar_elemento_flexivel(contexto, nome_limpo):
          print(
              f"  └─ [OK] Clicando no item (Nível {nivel_idx}): '{nome_limpo}'"
              f" (Tentativa {tentativa})"
          )
          clicado = True
          break

        print(
            f"  ├─ [AGUARDANDO RENDERIZAÇÃO] Nível {nivel_idx} ('{nome_limpo}'),"
            f" aguardando painel/menu... ({tentativa}/{tentativas})"
        )
        self.page.wait_for_timeout(2000)

      if not clicado:
        raise RuntimeError(
            f"❌ ITEM NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'.\n"
            f"   Verifique se o nome no .env corresponde exatamente ao exibido"
            f" na tela/painel."
        )

      # Tempo de espera para o painel central recarregar as opções do próximo nível
      self.page.wait_for_timeout(2500)

    print("[NAVEGAÇÃO] Sequência de menus concluída com sucesso!\n")