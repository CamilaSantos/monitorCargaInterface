from playwright.sync_api import Page


class ProgramPage:

  def __init__(self, page: Page):
    self.page = page

    # SmartClient HTML - Modal Inicial
    self.input_programa_inicial = page.get_by_role(
        "group", name="Programa Inicial"
    ).get_by_role("textbox")
    self.btn_ok_modulo = page.get_by_role("button", name="Ok")

  def selecionar_modulo(self, programa: str):
    """Passo 1: Preenche o programa inicial (SIGAMDI, SIGAFIS, etc.) e confirma."""
    self.input_programa_inicial.wait_for(state="visible")
    self.input_programa_inicial.click()
    self.input_programa_inicial.press("ControlOrMeta+A")
    self.input_programa_inicial.fill(programa)
    self.btn_ok_modulo.click()

    # Aguarda o frame do Protheus ser anexado para o próximo passo
    self.page.wait_for_selector("iframe", state="attached", timeout=30000)