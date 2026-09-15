import re
import unicodedata
from playwright.sync_api import Page


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
                if frame.locator("po-menu, .po-menu-container, po-lookup, .po-lookup-button, .driver-popover").count() > 0:
                    return frame
            except Exception:
                continue

        iframe_element = self.page.locator("iframe").first
        if iframe_element.count() > 0:
            return iframe_element.content_frame
        return self.page

    def fechar_tutorial_se_existir(self, tempo_espera_ms: int = 3000):
        """Fecha o tutorial (driver.js) de forma direta e limpa."""
        self.page.wait_for_timeout(1000)
        seletores_btn = [
            "button.driver-popover-close-btn",
            ".driver-popover-close-btn",
            "#driver-popover-content button"
        ]

        # Busca na página principal e frames
        for f in [self.page] + self.page.frames:
            for s in seletores_btn:
                try:
                    loc = f.locator(s)
                    if loc.count() > 0 and loc.first.is_visible():
                        loc.first.click(force=True)
                        print("  └─ [OK] Tutorial de integração/onboarding fechado.")
                        self.page.wait_for_timeout(1000)
                        return
                except Exception:
                    continue

        # Fallback via remoção direta DOM
        try:
            frame = self._obter_frame_po_ui()
            script = """
            () => {
                const popover = document.querySelector('.driver-popover, #driver-popover-content');
                const overlay = document.querySelector('.driver-overlay');
                if (popover) popover.remove();
                if (overlay) overlay.remove();
                document.body.classList.remove('driver-active', 'driver-fade');
            }
            """
            frame.evaluate(script)
        except Exception:
            pass

    def selecionar_menu_interno(self, nome_item: str):
        """Clica no menu lateral do PO UI e encerra o tutorial caso seja acionado."""
        nome_limpo = sanitizar_texto(nome_item)
        frame = self._obter_frame_po_ui()
        padrao_regex = re.compile(rf"^\s*{re.escape(nome_limpo)}\s*$", re.IGNORECASE)

        candidatos = frame.locator("po-menu-item, .po-menu-item-link, a").filter(has_text=padrao_regex)

        if candidatos.count() == 0:
            candidatos = frame.locator("po-menu-item, .po-menu-item-link, a").filter(has_text=nome_limpo)

        try:
            elem = candidatos.first
            elem.wait_for(state="visible", timeout=10000)
            elem.scroll_into_view_if_needed()
            elem.click(force=True)
            print(f"  └─ Menu '{nome_limpo}' selecionado.")

            self.page.wait_for_timeout(1500)
            self.fechar_tutorial_se_existir()

        except Exception as err:
            raise RuntimeError(f"❌ Item do menu não encontrado: '{nome_limpo}'. Erro: {err}")

    def selecionar_filial_carga(self, codigo_filial: str):
        """Abre o po-lookup de Filial, pesquisa o código informado e confirma."""
        self.fechar_tutorial_se_existir()
        frame = self._obter_frame_po_ui()

        # 1. Clique na Lupa
        btn_lupa = frame.locator(".po-lookup-button[aria-label='Pesquisar']").first
        btn_lupa.wait_for(state="visible", timeout=10000)
        btn_lupa.click(force=True)

        # 2. Busca modal
        campo_busca = frame.locator("input[name='contentSearch']").first
        campo_busca.wait_for(state="visible", timeout=10000)
        campo_busca.fill(codigo_filial)
        campo_busca.press("Enter")

        self.page.wait_for_timeout(1500)

        # 3. Seleção de linha
        linha = frame.locator(".po-row, tr, po-table-row, .po-table-row").filter(has_text=codigo_filial)
        if linha.count() > 0:
            linha.first.click(force=True)
        else:
            frame.locator("input[type='radio'], .po-radio-input").first.click(force=True)

        # 4. Confirmar
        btn_selecionar = frame.locator("po-button, button").filter(
            has_text=re.compile(r"^\s*Selecionar\s*$", re.IGNORECASE)
        )
        btn_selecionar.first.click(force=True)
        print(f"  └─ Filial '{codigo_filial}' selecionada com sucesso.")
        self.page.wait_for_timeout(1000)