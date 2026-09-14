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
        print(f"\n[NAVEGAÇÃO] Sequência no menu lateral: {list(niveis_menu)}")

        for nivel_idx, item_nome in enumerate(niveis_menu, start=1):
            if not item_nome or not item_nome.strip():
                continue

            nome_limpo = sanitizar_texto(item_nome)
            clicado = False
            tentativas = 5

            for tentativa in range(1, tentativas + 1):
                contexto = self._obter_contexto()

                # Busca o menu pelo texto visível exato do elemento
                # O locator do Playwright isola o elemento correto sem concatenar os textos dos filhos
                item_locator = contexto.locator(f"wa-menu-item:has-text('{nome_limpo}')")

                if item_locator.count() > 0:
                    # Percorre os candidatos para encontrar a correspondência exata do nível atual
                    for i in range(item_locator.count()):
                        elem = item_locator.nth(i)
                        
                        # Captura apenas o texto da legenda interna ou primeira linha para evitar os filhos
                        caption_elem = elem.locator("span.caption, .caption, span").first
                        texto_comparacao = caption_elem.inner_text() if caption_elem.count() > 0 else elem.inner_text()
                        texto_comparacao = sanitizar_texto(texto_comparacao)

                        # Valida se o nome buscado está contido no texto do item (ignorando contadores)
                        texto_sem_contador = re.sub(r"\(\d+\)$", "", texto_comparacao).strip()

                        if nome_limpo.lower() == texto_sem_contador.lower() or nome_limpo.lower() in texto_comparacao.lower():
                            if elem.is_visible():
                                elem.scroll_into_view_if_needed()
                                
                                # Dispara o clique no span interno para garantir a execução do evento ADVPL
                                if caption_elem.count() > 0 and caption_elem.is_visible():
                                    caption_elem.click(force=True)
                                else:
                                    elem.click(force=True)

                                print(f"  └─ [OK] Clicado no menu lateral (Nível {nivel_idx}): '{nome_limpo}' (Tentativa {tentativa})")
                                clicado = True
                                break

                if clicado:
                    break

                print(f"  ├─ [AGUARDANDO REFRESH/DOM] Nível {nivel_idx} ('{nome_limpo}')... ({tentativa}/{tentativas})")
                self.page.wait_for_timeout(1500)

            if not clicado:
                raise RuntimeError(
                    f"❌ MENU LATERAL NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'.\n"
                    f"   Verifique se o nome bate com os itens visíveis na barra lateral."
                )

            # Aguarda a resposta da requisição do Protheus pós-clique
            self.page.wait_for_timeout(2000)

        print("[NAVEGAÇÃO] Navegação pelo menu lateral concluída com sucesso!\n")