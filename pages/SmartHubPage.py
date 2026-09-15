import re
import unicodedata
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


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
                if frame.locator("po-menu, .po-menu-container, po-lookup, .po-lookup-button").count() > 0:
                    return frame
            except Exception:
                continue

        iframe_element = self.page.locator("iframe").first
        if iframe_element.count() > 0:
            return iframe_element.content_frame
        return self.page

    def fechar_tutorial_se_existir(self, tempo_espera_ms: int = 5000):
        """Varre recursivamente todas as instâncias de frames e shadow DOMs gerenciados pelo Playwright."""
        print("  └─ [INFO] Verificando presença de tutorial onboarding...")

        # Seletor exato do botão de fechar o driver.js
        seletor_btn = "button.driver-popover-close-btn"

        # 1. Tenta encontrar o elemento diretamente via Playwright (ele perfura Shadow DOM automaticamente)
        try:
            btn_global = self.page.locator(seletor_btn).first
            if btn_global.is_visible(timeout=tempo_espera_ms):
                btn_global.click(force=True)
                print("  └─ [OK] Tutorial fechado na página principal/shadow DOM.")
                self.page.wait_for_timeout(1000)
                return
        except Exception:
            pass

        # 2. Caso esteja isolado em contexto de Iframe/Webview do Protheus, percorre a lista de frames ativos
        for frame in self.page.frames:
            try:
                btn_frame = frame.locator(seletor_btn).first
                if btn_frame.is_visible(timeout=1000):
                    btn_frame.click(force=True)
                    print(f"  └─ [OK] Tutorial fechado dentro do frame: {frame.name or frame.url}")
                    self.page.wait_for_timeout(1000)
                    return
            except Exception:
                continue

        # 3. Fallback via tecla 'Escape' (o driver.js por padrão fecha o popover ao pressionar ESC)
        try:
            self.page.keyboard.press("Escape")
            print("  └─ [INFO] Tecla ESC enviada para fechar overlay de tutorial.")
        except Exception:
            pass

    def selecionar_menu_interno(self, nome_item: str):
        """Clica no menu lateral do PO UI e encerra o tutorial caso seja acionado."""
        nome_limpo = sanitizar_texto(nome_item)
        print(f"\n[SMART HUB] Navegando no menu interno para: '{nome_limpo}'")

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
            print(f"  └─ [OK] Item '{nome_limpo}' clicado no Smart Hub.")

            self.page.wait_for_timeout(1500)
            self.fechar_tutorial_se_existir()

        except Exception as err:
            raise RuntimeError(f"❌ ITEM DO SMART HUB NÃO ENCONTRADO OU INDISPONÍVEL: '{nome_limpo}'. Erro: {err}")

    def selecionar_filial_carga(self, codigo_filial: str):
        """Abre o po-lookup de Filial, pesquisa o código informado, valida na tabela e confirma a seleção."""
        print(f"\n[SMART HUB] Selecionando filial no campo de busca: '{codigo_filial}'")

        self.fechar_tutorial_se_existir()
        frame = self._obter_frame_po_ui()

        # 1. Clique na Lupa do po-lookup
        btn_lupa = frame.locator(".po-lookup-button[aria-label='Pesquisar']").first
        btn_lupa.wait_for(state="visible", timeout=10000)
        btn_lupa.click(force=True)

        # 2. Aguarda a modal 'Filiais disponíveis' abrir
        campo_busca_modal = frame.locator("input[name='contentSearch']").first
        campo_busca_modal.wait_for(state="visible", timeout=10000)

        # 3. Preenche o código da Filial e dispara a busca
        campo_busca_modal.fill(codigo_filial)
        campo_busca_modal.press("Enter")

        self.page.wait_for_timeout(1500)

        # 4. Localiza a linha contendo o código e clica para marcar
        linha_resultado = frame.locator(".po-row, tr, po-table-row, .po-table-row").filter(has_text=codigo_filial)

        if linha_resultado.count() > 0:
            linha_resultado.first.click(force=True)
        else:
            frame.locator("input[type='radio'], .po-radio-input, .po-table-checkbox").first.click(force=True)

        # 5. Clica no botão 'Selecionar' da modal
        btn_selecionar = frame.locator("po-button, button").filter(
            has_text=re.compile(r"^\s*Selecionar\s*$", re.IGNORECASE)
        )
        btn_selecionar.first.click(force=True)

        print(f"  └─ [OK] Filial '{codigo_filial}' selecionada com sucesso.")
        self.page.wait_for_timeout(1000)