import os
from dotenv import load_dotenv
import pytest

load_dotenv()

# Tempo máximo de tolerância para ações e transições (obtido do .env ou padrão 60s)
TIMEOUT_PADRAO = int(os.getenv("PROTHEUS_TIMEOUT", "60000"))


@pytest.fixture(scope="session")
def protheus_url():
  return os.getenv("PROTHEUS_URL")


@pytest.fixture(scope="session")
def credenciais_protheus():
  return {
      "programa": os.getenv("PROTHEUS_PROGRAMA"),
      "usuario": os.getenv("PROTHEUS_USUARIO"),
      "senha": os.getenv("PROTHEUS_SENHA"),
      "grupo": os.getenv("PROTHEUS_GRUPO"),
      "filial": os.getenv("PROTHEUS_FILIAL"),
      "ambiente": os.getenv("PROTHEUS_AMBIENTE"),
      "data_base": "hoje",
  }


@pytest.fixture(scope="session")
def dados_navegacao_protheus():
  return {
      "menu_principal": os.getenv("PROTHEUS_MENU_ATUALIZACAO"),
      "submenu": os.getenv("PROTHEUS_SUBMENU_SH"),
      "rotina_destino": os.getenv("PROTHEUS_SUBMENU_ROTINA_SHT"),
  }


@pytest.fixture(autouse=True)
def configurar_timeout_global(page):
  """Aplica tolerância global para elementos e chamadas de navegação."""
  page.set_default_timeout(TIMEOUT_PADRAO)
  page.set_default_navigation_timeout(TIMEOUT_PADRAO)


@pytest.fixture
def aguardar_estabilizacao_iframe(page):
  """
  Helper exclusivo para sincronizar trocas de telas/iFrames.
  Garante que o iFrame ativo e o body do SmartClient/PO-UI estejam visíveis.
  """

  def _sincronizar():
    # 1. Aguarda o container do webview/iframe ser anexado ao DOM
    page.wait_for_selector(
        "wa-webview iframe, iframe", state="attached", timeout=TIMEOUT_PADRAO
    )

    # 2. Captura o frame ativo e aguarda o body renderizar
    frame = page.locator("wa-webview").last.frame_locator("iframe")
    frame.locator("body").wait_for(state="visible", timeout=TIMEOUT_PADRAO)

    # 3. Micro-pausa de 1.5s apenas para estabilização de Web Components (Shadow DOM)
    page.wait_for_timeout(3500)

  return _sincronizar