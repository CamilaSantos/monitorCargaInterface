from datetime import datetime
from playwright.sync_api import FrameLocator, Page


class LoginPage:

  def __init__(self, page: Page):
    self.page = page

    # 1. SMARTCLIENT HTML (MODAL INICIAL)
    self.input_programa_inicial = page.get_by_role(
        "group", name="Programa Inicial"
    ).get_by_role("textbox")
    self.btn_ok_modulo = page.get_by_role("button", name="Ok")

    # 2. FRAME DO PROTHEUS (WEBVIEW / IFRAME)
    self.protheus_frame: FrameLocator = page.frame_locator("iframe")

    # 3. TELA DE LOGIN (PO-UI LOGIN)
    self.input_usuario = self.protheus_frame.get_by_role(
        "textbox", name="Insira seu usuário"
    )
    self.input_senha = self.protheus_frame.get_by_role(
        "textbox", name="Insira sua senha"
    )
    self.btn_entrar = self.protheus_frame.get_by_role("button", name="Entrar")

    # 4. TELA DE PARÂMETROS / AMBIENTE (PÓS-LOGIN)
    self.input_data_base = self.protheus_frame.get_by_role(
        "textbox", name="Data base"
    )
    self.input_grupo = self.protheus_frame.get_by_role(
        "textbox", name="Grupo"
    )
    self.input_filial = self.protheus_frame.get_by_role(
        "textbox", name="Filial"
    )
    self.input_ambiente = self.protheus_frame.get_by_role(
        "textbox", name="Ambiente"
    )

    self.btn_entrar_ambiente = self.protheus_frame.get_by_role(
        "button", name="Entrar"
    )

  # =============================================================================
  # MÉTODOS DE AÇÃO
  # =============================================================================

  def selecionar_modulo_inicial(self, programa: str = "SIGAMDI"):
    """Ação da 1ª Tela (SmartClient HTML)."""
    self.input_programa_inicial.wait_for(state="visible")
    self.input_programa_inicial.click()
    self.input_programa_inicial.press("ControlOrMeta+A")
    self.input_programa_inicial.fill(programa)
    self.btn_ok_modulo.click()

    # Aguarda o carregamento do iframe do Protheus
    self.page.wait_for_selector("iframe", state="attached",timeout=30000)

  def realizar_login(self, usuario: str, senha: str):
    # 1. Pega o iframe do wa-webview ativo
    frame_login = self.page.locator("wa-webview").last.frame_locator("iframe")

    # 2. Mapeia o input do usuário
    input_usuario = frame_login.locator("po-login[name='login'] input")

    # 3. ESPERA EXPLÍCITA: Aguarda o frame sair do branco e renderizar o input (timeout de 60s)
    input_usuario.wait_for(state="visible", timeout=60000)

    # 4. Ações de preenchimento (executadas no segundo exato em que o campo surge)
    input_usuario.fill(usuario)

    input_senha = frame_login.locator("po-password[name='password'] input")
    input_senha.fill(senha)

    btn_entrar = frame_login.locator("po-button button")
    btn_entrar.click()

  def selecionar_parametros_ambiente(
      self,
      grupo: str = None,
      filial: str = None,
      ambiente: str = None,
      data_base: str = "hoje",
  ):
    """Ação da 3ª Tela (Data Base, Grupo, Filial e Ambiente pós-login)."""
    self.btn_entrar_ambiente.wait_for(state="visible")

    if data_base and data_base.lower() != "hoje":
      if self.input_data_base.is_visible():
        self.input_data_base.click()
        self.input_data_base.press("ControlOrMeta+A")
        self.input_data_base.fill(data_base)

    if grupo:
      self.input_grupo.wait_for(state="visible")
      self.input_grupo.click()
      self.input_grupo.press("ControlOrMeta+A")
      self.input_grupo.fill(grupo)

    if filial:
      self.input_filial.wait_for(state="visible")
      self.input_filial.click()
      self.input_filial.press("ControlOrMeta+A")
      self.input_filial.fill(filial)

    if ambiente:
      self.input_ambiente.wait_for(state="visible")
      self.input_ambiente.click()
      self.input_ambiente.fill(ambiente)

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