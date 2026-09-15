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

    def fechar_tutorial_se_existir(self, tempo_espera_ms: int = 4000):
        """
        Mapeia a página principal e todos os frames em busca dos elementos do tutorial (driver.js),
        registrando detalhadamente no console se o elemento foi localizado ou não.
        """
        print("\n[DIAGNÓSTICO TUTORIAL] Mapeando estrutura para fechar o tutorial...")
        
        # Pausa para garantir que a animação de fade do driver.js conclua
        self.page.wait_for_timeout(1000)

        # Seletores mapeados a partir dos prints do DOM
        seletores_btn = [
            "button.driver-popover-close-btn",
            ".driver-popover-close-btn",
            "button[aria-label='Close']",
            "#driver-popover-content button"
        ]

        # 1. Tentar localizar o botão diretamente no contexto da página principal
        for seletor in seletores_btn:
            loc = self.page.locator(seletor)
            qtd = loc.count()
            if qtd > 0:
                print(f"  ├─ [Mapeamento Main Page] Encontrado {qtd} elemento(s) com seletor: '{seletor}'")
                try:
                    if loc.first.is_visible():
                        loc.first.click(force=True)
                        print("  └─ [SUCESSO] Tutorial fechado na Página Principal!")
                        self.page.wait_for_timeout(1000)
                        return True
                except Exception as e:
                    print(f"  ├─ [Aviso] Falha ao clicar no elemento da Main Page: {e}")

        # 2. Mapeamento recursivo em todos os frames/iframes
        todos_frames = self.page.frames
        print(f"  ├─ [Mapeamento Frames] Total de frames ativos detectados: {len(todos_frames)}")

        for index, frame in enumerate(todos_frames):
            nome_frame = frame.name or frame.url or f"Frame {index}"
            print(f"  ├─ Analisando {nome_frame}...")

            # Testa os seletores dentro deste frame específico
            for seletor in seletores_btn:
                try:
                    loc = frame.locator(seletor)
                    qtd = loc.count()
                    if qtd > 0:
                        print(f"  │   ├─ [ENCONTRADO] {qtd} elemento(s) com '{seletor}' dentro do {nome_frame}")
                        
                        # Tenta clicar no botão
                        loc.first.click(force=True)
                        print(f"  │   └─ [SUCESSO] Tutorial fechado com sucesso dentro do {nome_frame}!")
                        self.page.wait_for_timeout(1000)
                        return True
                except Exception as err:
                    print(f"  │   ├─ [Aviso] Erro ao interagir com seletor '{seletor}' no {nome_frame}: {err}")

            # 3. Tentativa de remoção/fechamento via JS dentro do Frame (Fallback)
            try:
                script_fechar = """
                () => {
                    const btn = document.querySelector('button.driver-popover-close-btn, .driver-popover-close-btn');
                    if (btn) {
                        btn.click();
                        return 'clicado';
                    }
                    const popover = document.querySelector('.driver-popover, #driver-popover-content');
                    const overlay = document.querySelector('.driver-overlay');
                    if (popover || overlay) {
                        if (popover) popover.remove();
                        if (overlay) overlay.remove();
                        document.body.classList.remove('driver-active', 'driver-fade');
                        return 'removido_dom';
                    }
                    return null;
                }
                """
                res = frame.evaluate(script_fechar)
                if res:
                    print(f"  │   └─ [SUCESSO JS] Ação executada via script no {nome_frame}: resultado = '{res}'")
                    self.page.wait_for_timeout(1000)
                    return True
            except Exception:
                pass

        # 4. Caso não encontre em nenhum lugar, gera evidência para depuração
        print("  └─ [ALERTA] Nenhum botão ou popover de tutorial foi localizado nos elementos do DOM.")
        try:
            self.page.screenshot(path="debug_tutorial.png")
            print("  └─ [DEBUG] Print da tela salvo em 'debug_tutorial.png' para análise.")
        except Exception:
            pass
            
        return False

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

            # Mapeia e fecha o tutorial
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