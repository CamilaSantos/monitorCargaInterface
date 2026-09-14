import re
import unicodedata
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


def sanitizar_texto(texto: str) -> str:
  if not texto:
    return ""
  texto_limpo = unicodedata.normalize("NFKC", texto)
  return re.sub(r"\s+", " ", texto_limpo).strip()


class NavigationPage:

  def __init__(self, page: Page):
    self.page = page

  def _obter_contexto(self):
    """Localiza o frame ou página onde os menus estão renderizados."""
    for frame in self.page.frames:
      try:
        if frame.locator("wa-menu-item").count() > 0:
          return frame
      except Exception:
        continue
    return self.page

  def navegar(self, *niveis_menu: str):
    """Navega exclusivamente pela árvore do menu lateral."""
    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = sanitizar_texto(item_nome)
      clicado = False
      tentativas = 5

      for _ in range(1, tentativas + 1):
        contexto = self._obter_contexto()

        # Busca o menu pelo texto visível exato do elemento
        item_locator = contexto.locator(
            f"wa-menu-item:has-text('{nome_limpo}')"
        )

        if item_locator.count() > 0:
          for i in range(item_locator.count()):
            elem = item_locator.nth(i)

            # Captura a legenda interna do item de menu
            caption_elem = elem.locator("span.caption, .caption, span").first
            texto_comparacao = (
                caption_elem.inner_text()
                if caption_elem.count() > 0
                else elem.inner_text()
            )
            texto_comparacao = sanitizar_texto(texto_comparacao)

            # Remove contadores do tipo (24), (5) para comparar
            texto_sem_contador = re.sub(
                r"\(\d+\)$", "", texto_comparacao
            ).strip()

            if (
                nome_limpo.lower() == texto_sem_contador.lower()
                or nome_limpo.lower() in texto_comparacao.lower()
            ):
              if elem.is_visible():
                elem.scroll_into_view_if_needed()

                # Dispara o clique no span interno
                if caption_elem.count() > 0 and caption_elem.is_visible():
                  caption_elem.click(force=True)
                else:
                  elem.click(force=True)

                clicado = True
                break

        if clicado:
          break

        self.page.wait_for_timeout(1500)

      if not clicado:
        raise RuntimeError(
            f"❌ MENU LATERAL NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'."
        )

      # Aguarda a resposta do Protheus antes de prosseguir
      self.page.wait_for_timeout(2000)