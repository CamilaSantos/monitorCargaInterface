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
        """Localiza a página ou frame onde a árvore de menus está anexada."""
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
            # Regex que tolera o sufixo numérico (ex: "Smart Hub" casa com "Smart Hub (5)")
            padrao_regex = re.compile(rf"^\s*{re.escape(nome_limpo)}(\s*\(\d+\))?\s*$", re.IGNORECASE)

            # Espera obrigatória para garantir que o SmartClient terminou o re-render após o clique anterior
            self.page.wait_for_timeout(1500)

            clicado = False
            tentativas = 5

            for tentativa in range(1, tentativas + 1):
                contexto = self._obter_contexto()

                # Busca os itens de menu lateral renovando o nó do DOM a cada tentativa
                elementos = contexto.locator("wa-menu-item").all()

                for elem in elementos:
                    try:
                        texto_bruto = elem.inner_text()
                        texto_limpo = sanitizar_texto(texto_bruto)

                        # Verifica se o texto do elemento bate com o nome desejado
                        if padrao_regex.search(texto_limpo) or nome_limpo.lower() in texto_limpo.lower():
                            if elem.is_visible():
                                elem.scroll_into_view_if_needed()
                                
                                # Tenta clicar no span interno ou força o clique no elemento
                                span_caption = elem.locator("span.caption, span").first
                                if span_caption.count() > 0 and span_caption.is_visible():
                                    span_caption.click(force=True)
                                else:
                                    elem.click(force=True)

                                print(f"  └─ [OK] Clicado no menu lateral (Nível {nivel_idx}): '{nome_limpo}' (Tentativa {tentativa})")
                                clicado = True
                                break
                    except Exception:
                        # Se o nó do DOM mudou no meio da iteração, ignora e tenta na próxima
                        continue

                if clicado:
                    break

                print(f"  ├─ [AGUARDANDO DOM] Nível {nivel_idx} ('{nome_limpo}')... ({tentativa}/{tentativas})")
                self.page.wait_for_timeout(1500)

            if not clicado:
                raise RuntimeError(
                    f"❌ MENU LATERAL NÃO ENCONTRADO no Nível {nivel_idx}: '{nome_limpo}'.\n"
                    f"   Verifique se o nome bate com os submenus visíveis na barra lateral."
                )

            # Aguarda a resposta ADVPL e a expansão dos filhos antes de ir para o próximo nível
            self.page.wait_for_timeout(2000)

        print("[NAVEGAÇÃO] Navegação pelo menu lateral concluída com sucesso!\n")