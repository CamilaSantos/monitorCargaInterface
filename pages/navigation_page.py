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

    def obter_informacoes_ambiente(self) -> str:
    """Busca diretamente o texto do cabeçalho da aplicação."""
    try:
        # Script JS simples para pegar a legenda do cabeçalho (caption) independente do Shadow DOM
        script = """
        () => {
            const el = document.querySelector('wa-panel, wa-button, [class*="dict-tbutton"]');
            if (el) {
                return el.getAttribute('caption') || el.innerText || '';
            }
            return document.body.innerText;
        }
        """
        texto = self.page.evaluate(script)
        if texto:
            # Procura por padrões como TOTVS, Serviços, ORACLE, P12, etc., ou pega a primeira linha limpa
            linhas = [l.strip() for l in texto.split('\n') if l.strip()]
            for linha in linhas:
                if any(k in linha for k in ["Serviços", "ORACLE", "Psh", "TOTVS", "COMP"]):
                    return linha
            if linhas:
                return linhas[0]
        return "Informação de ambiente capturada"
    except Exception as e:
        return f"Erro na captura: {str(e)}"

    def obter_banco_dados(self) -> str:
        """Alias mantido para compatibilidade."""
        return self.obter_informacoes_ambiente()

    def _obter_contexto(self):
        """Localiza o frame ou página onde os menus e caixas de diálogo estão renderizados."""
        for frame in self.page.frames:
            try:
                if frame.locator("wa-menu-item, wa-dialog, wa-button").count() > 0:
                    return frame
            except Exception:
                continue
        return self.page

    def _tratar_dialogos_sequenciais(
        self, tempo_limite_total: int = 30, intervalo_checagem: float = 1.5
    ):
        """Trata janelas e pop-ups encadeados (ex: Parâmetros -> Aviso 'Atenção' -> Moedas)."""
        tempo_decorrido = 0.0

        while tempo_decorrido < tempo_limite_total:
            contexto = self._obter_contexto()
            dialogo_tratado = False

            # 1. CASO 1: Pop-up de Aviso/Atenção
            dialogo_atencao = contexto.locator("wa-dialog").filter(
                has_text=re.compile(r"Atenção", re.IGNORECASE)
            )

            if dialogo_atencao.count() > 0 and dialogo_atencao.first.is_visible():
                btn_fechar = dialogo_atencao.first.locator(
                    "div.close, .close-button, button.close, [title='Fechar'], div[class*='close']"
                ).first
                if btn_fechar.count() > 0 and btn_fechar.is_visible():
                    btn_fechar.click(force=True)
                    dialogo_tratado = True
                else:
                    dialogo_atencao.first.locator("div, span").last.click(force=True)
                    dialogo_tratado = True

            # 2. CASO 2: Telas de Confirmação Padrão
            if not dialogo_tratado:
                textos_confirmacao = ["Confirmar", "OK", "Sim", "Salvar", "Avançar"]

                for texto in textos_confirmacao:
                    padrao_botao = re.compile(rf"^\s*{texto}\s*$", re.IGNORECASE)
                    botoes = contexto.locator("wa-button, button, a, div").filter(
                        has_text=padrao_botao
                    )

                    if botoes.count() > 0:
                        for i in range(botoes.count()):
                            btn = botoes.nth(i)
                            if btn.is_visible():
                                caption_elem = btn.locator(
                                    "span.caption, .caption, span, label"
                                ).first
                                if caption_elem.count() > 0 and caption_elem.is_visible():
                                    caption_elem.click(force=True)
                                else:
                                    btn.click(force=True)

                                dialogo_tratado = True
                                break

                    if dialogo_tratado:
                        break

            if dialogo_tratado:
                tempo_decorrido = 0.0
                try:
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                except PlaywrightTimeoutError:
                    pass
                self.page.wait_for_timeout(3000)
            else:
                self.page.wait_for_timeout(int(intervalo_checagem * 1000))
                tempo_decorrido += intervalo_checagem

    def navegar(self, *niveis_menu: str):
        """Navega pela árvore do menu lateral e trata a sequência completa de janelas."""
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

        self._tratar_dialogos_sequenciais(tempo_limite_total=25)