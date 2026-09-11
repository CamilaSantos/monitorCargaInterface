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
    self.input_usuario = self.protheus_frame.locator("input[name='login']")
    self.input_senha = self.protheus_frame.locator("input[type='password']")
    self.btn_entrar = self.protheus_frame.locator(
        "button.po-button:has-text('Entrar'), button[type='submit']"
    )

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
    """Ação da 2ª Tela (Login e Senha)."""
    self.input_usuario.wait_for(state="visible")
    self.input_usuario.fill(usuario)
    self.input_senha.fill(senha)
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

    # Tratamento da Data Base
    if data_base:
      data_para_preencher = (
          datetime.now().strftime("%d/%m/%Y")
          if data_base.lower() == "hoje"
          else data_base
      )
      self.input_data_base.wait_for(state="visible")
      self.input_data_base.fill(data_para_preencher)
      self.page.keyboard.press("Tab")

    # Grupo
    if grupo:
      self.input_grupo.wait_for(state="visible")
      self.input_grupo.fill(grupo)
      self.page.keyboard.press("Tab")

    # Filial
    if filial:
      self.input_filial.wait_for(state="visible")
      self.input_filial.fill(filial)
      self.page.keyboard.press("Tab")

    # Ambiente
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