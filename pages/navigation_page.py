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
    """Localiza o frame ou página onde os menus e caixas de diálogo estão renderizados."""
    for frame in self.page.frames:
      try:
        if (
            frame.locator("wa-menu-item, wa-button, button").count() > 0
        ):  # Fontes: Mapeamento de botões e menus
          return frame
      except Exception:
        continue
    return self.page

  def _tratar_dialogo_pos_navegacao(self):
    """Verifica e clica em botões de confirmação (ex: Confirmar, OK) que surgem ao abrir rotinas."""
    # Breve pausa para garantir a renderização de pop-ups ou diálogos de parâmetros
    self.page.wait_for_timeout(1500)

    contexto = self._obter_contexto()

    # Mapeia possíveis seletores de botões de confirmação do SmartClient (wa-button, button, a)
    textos_confirmacao = [
        "Confirmar",
        "OK",
        "Sim",
        "Salvar",
        "Avançar",
    ]  # Fontes: Telas de parâmetro do Protheus

    for texto in textos_confirmacao:
      padrao_botao = re.compile(rf"^\s*{texto}\s*$", re.IGNORECASE)

      # Localiza o botão via Web Components do SmartClient ou HTML padrão
      botoes = contexto.locator("wa-button, button, a, div").filter(
          has_text=padrao_botao
      )

      if botoes.count() > 0:
        for i in range(botoes.count()):
          btn = botoes.nth(i)
          if btn.is_visible():
            btn.scroll_into_view_if_needed()

            # Dispara o clique diretamente na legenda interna (span) ou no botão
            caption_elem = btn.locator(
                "span.caption, .caption, span, label"
            ).first
            if caption_elem.count() > 0 and caption_elem.is_visible():
              caption_elem.click(force=True)
            else:
              btn.click(force=True)

            # Aguarda o processamento do fechamento da caixa de diálogo
            self.page.wait_for_timeout(2000)
            return

  def navegar(self, *niveis_menu: str):
    """Navega pela árvore do menu lateral e confirma diálogos iniciais da rotina."""
    for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
      if not item_nome or not item_nome.strip():
        continue

      nome_limpo = sanitizar_texto(item_nome)
      clicado = False
      tentativas = 5

      for _ in range(1, tentativas + 1):
        contexto = self._obter_contexto()

        item_locator = contexto.locator(
            f"wa-menu-item:has-text('{nome_limpo}')"
        )

        if item_locator.count() > 0:
          for i in range(item_locator.count()):
            elem = item_locator.nth(i)

            caption_elem = elem.locator("span.caption, .caption, span").first
            texto_comparacao = (
                caption_elem.inner_text()
                if caption_elem.count() > 0
                else elem.inner_text()
            )
            texto_comparacao = sanitizar_texto(texto_comparacao)

            texto_sem_contador = re.sub(
                r"\(\d+\)$", "", texto_comparacao
            ).strip()

            if (
                nome_limpo.lower() == texto_sem_contador.lower()
                or nome_limpo.lower() in texto_comparacao.lower()
            ):
              if elem.is_visible():
                elem.scroll_into_view_if_needed()

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

      self.page.wait_for_timeout(2000)

    # Após o último menu clicado, trata automaticamente qualquer tela/pop-up de confirmação
    self._tratar_dialogo_pos_navegacao()