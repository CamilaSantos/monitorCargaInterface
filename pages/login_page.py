from playwright.sync_api import FrameLocator, Page


class LoginPage:

  def __init__(self, page: Page):
    self.page = page

  @property
  def protheus_frame(self) -> FrameLocator:
    """Retorna dinamicamente o frame ativo do Protheus via wa-webview."""
    return self.page.locator("wa-webview").last.frame_locator("iframe")

  # --- SELETORES DO PO-UI LOGIN ---
  @property
  def input_usuario(self):
    return self.protheus_frame.locator("po-login[name='login'] input")

  @property
  def input_senha(self):
    return self.protheus_frame.locator("po-password[name='password'] input")

  @property
  def btn_entrar(self):
    return self.protheus_frame.locator("po-button button")

  # --- MÉTODOS DE AÇÃO ---
  def realizar_login(self, usuario: str, senha: str):
    """Passo 2: Preenche as credenciais de acesso e clica em Entrar."""
    self.input_usuario.wait_for(state="visible", timeout=60000)
    self.input_usuario.fill(usuario)
    self.input_senha.fill(senha)
    self.btn_entrar.click()