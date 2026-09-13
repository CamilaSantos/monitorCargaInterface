from playwright.sync_api import FrameLocator, Page


class EnvironmentPage:

  def __init__(self, page: Page):
    self.page = page

  @property
  def protheus_frame(self) -> FrameLocator:
    """Retorna dinamicamente o frame ativo do Protheus via wa-webview."""
    return self.page.locator("wa-webview").last.frame_locator("iframe")

  # --- SELETORES DOS PARÂMETROS / AMBIENTE ---
  @property
  def input_data_base(self):
    return self.protheus_frame.get_by_role("textbox", name="Data base")

  @property
  def input_grupo(self):
    return self.protheus_frame.get_by_role("textbox", name="Grupo")

  @property
  def input_filial(self):
    return self.protheus_frame.get_by_role("textbox", name="Filial")

  @property
  def input_ambiente(self):
    return self.protheus_frame.get_by_role("textbox", name="Ambiente")

  @property
  def btn_entrar_ambiente(self):
    return self.protheus_frame.get_by_role("button", name="Entrar")

  # --- MÉTODOS DE AÇÃO ---
  def selecionar_ambiente(
      self,
      grupo: str = None,
      filial: str = None,
      ambiente: str = None,
      data_base: str = "hoje",
  ):
    """Passo 3: Configura o ambiente, empresa/filial e data-base no Protheus."""
    self.btn_entrar_ambiente.wait_for(state="visible")

    if data_base and data_base.lower() != "hoje":
      self.input_data_base.wait_for(state="visible")
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
      self.input_ambiente.press("ControlOrMeta+A")
      self.input_ambiente.fill(ambiente)

    self.btn_entrar_ambiente.click()

    # ESPERA CRÍTICA: Aguarda a renderização do menu principal pós-login
    self.protheus_frame.locator("cwa-menu, .tmenu").first.wait_for(
        state="visible", timeout=60000
    )