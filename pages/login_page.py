from datetime import datetime
from playwright.sync_api import FrameLocator, Page


class LoginPage:

  def __init__(self, page: Page):
    self.page = page

    # 1. SMARTCLIENT HTML (MODAL INICIAL)
    self.input_programa_inicial = page.locator(
        "wa-combobox#selectStartProg input"
    )
    self.input_ambiente_servidor = page.locator("wa-combobox#selectEnv input")
    self.btn_ok_modulo = page.locator("wa-dialog button:has-text('OK')")

    # 2. FRAME DO PROTHEUS (WEBVIEW / IFRAME)
    self.protheus_frame: FrameLocator = page.frame_locator("wa-webview iframe")

    # 3. TELA DE LOGIN (PO-UI LOGIN)
    self.input_usuario = self.protheus_frame.get_by_role(
        "textbox", name="Insira seu usuário"
    )
    self.input_senha = self.protheus_frame.get_by_role(
        "textbox", name="Insira sua senha"
    )
    self.btn_entrar = self.protheus_frame.get_by_role("button", name="Entrar")

    # 4. TELA DE PARÂMETROS / AMBIENTE (PÓS-LOGIN)
    self.input_data_base = self.protheus_frame.locator(
        "po-datepicker[name='database'] input, input[name='database']"
    )
    self.input_grupo = self.protheus_frame.locator(
        "po-lookup[name='group'] input, input[name='group']"
    )
    self.input_filial = self.protheus_frame.locator(
        "po-lookup[name='branch'] input, input[name='branch']"
    )
    self.input_ambiente = self.protheus_frame.locator(
        "po-lookup[name='environment'] input, po-lookup[name='module'] input,"
        " input[name='environment']"
    )
    self.input_papel_trabalho = self.protheus_frame.locator(
        "po-lookup[name='role'] input, input[name='role']"
    )

    self.btn_entrar_ambiente = self.protheus_frame.locator(
        "button:has-text('Entrar'), button:has-text('Confirmar')"
    )
    self.btn_voltar_ambiente = self.protheus_frame.locator(
        "button:has-text('Voltar')"
    )

  # =============================================================================
  # MÉTODOS DE AÇÃO
  # =============================================================================

  def selecionar_modulo_inicial(self, programa: str = "SIGAMDI"):
    """Ação da 1ª Tela (SmartClient HTML)."""
    self.input_programa_inicial.wait_for(state="visible")
    self.input_programa_inicial.fill(programa)
    self.page.keyboard.press("Enter")
    self.btn_ok_modulo.click()
    self.page.wait_for_selector("wa-webview iframe", state="attached")

  def realizar_login(self, usuario: str, senha: str):
      """Ação com digitação simulada caractere por caractere."""
      self.input_usuario.wait_for(state="visible")

      # Clica para dar foco e digita como um usuário real
      self.input_usuario.click()
      self.input_usuario.press_sequentially(usuario, delay=50)

      self.input_senha.click()
      self.input_senha.press_sequentially(senha, delay=50)

      self.btn_entrar.click()

  def selecionar_parametros_ambiente(
      self,
      grupo: str = None,
      filial: str = None,
      ambiente: str = None,
      data_base: str = "hoje",
  ):
    """Ação da 3ª Tela (Data Base, Grupo, Filial e Ambiente pós-login)."""
    self.btn_entrar_ambiente.wait_for(state="visible")

    if data_base:
      data_para_preencher = (
          datetime.now().strftime("%d/%m/%Y")
          if data_base.lower() == "hoje"
          else data_base
      )
      self.input_data_base.wait_for(state="visible")
      self.input_data_base.fill(data_para_preencher)
      self.page.keyboard.press("Tab")

    if grupo:
      self.input_grupo.wait_for(state="visible")
      self.input_grupo.fill(grupo)
      self.page.keyboard.press("Tab")

    if filial:
      self.input_filial.wait_for(state="visible")
      self.input_filial.fill(filial)
      self.page.keyboard.press("Tab")

    if ambiente:
      self.input_ambiente.wait_for(state="visible")
      self.input_ambiente.fill(ambiente)
      self.page.keyboard.press("Tab")

    self.btn_entrar_ambiente.click()

  def fazer_login_completo(
      self,
      programa: str,
      usuario: str,
      senha: str,
      grupo: str = None,
      filial: str = None,
      ambiente: str = None,
      data_base: str = "hoje",
  ):
    """Orquestrador único para executar a sequência de login de ponta a ponta."""
    self.selecionar_modulo_inicial(programa)
    self.realizar_login(usuario, senha)
    self.selecionar_parametros_ambiente(grupo, filial, ambiente, data_base)