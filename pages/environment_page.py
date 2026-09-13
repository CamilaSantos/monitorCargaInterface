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
    self.btn_entrar_ambiente.wait_for(state="visible", timeout=30000)

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

    # Clica no botão 'Entrar' para carregar a área de trabalho
    self.btn_entrar_ambiente.click()

    # ESPERA RESILIENTE: Aguarda até o botão "Entrar" sumir da tela
    # Isso confirma que a tela de parâmetros foi fechada e o processamento de login concluiu.
    try:
      self.btn_entrar_ambiente.wait_for(state="detached", timeout=60000)
    except Exception:
      pass

    # Pausa técnica para permitir o carregamento e renderização total do DOM principal
    self.page.wait_for_timeout(3000)