import os
from dotenv import load_dotenv
import pytest
from pages.program_page import ProgramPage
from pages.login_page import LoginPage
from pages.environment_page import EnvironmentPage
from pages.navigation_page import NavigationPage

load_dotenv()

# Timeout padrão lido do .env (padrão 60s)
TIMEOUT_PADRAO = int(os.getenv("PROTHEUS_TIMEOUT", "60000"))


@pytest.fixture(scope="session")
def protheus_url():
  return os.getenv("PROTHEUS_URL")


@pytest.fixture(scope="session")
def obter_config_perfil():
  """Lê do .env as configurações de um perfil específico usando o prefixo.

  Exemplo de uso no teste: config = obter_config_perfil("COMERCIAL")
  """

  def _carregar_perfil(perfil: str) -> dict:
    prefixo = f"PROTHEUS_{perfil.upper()}_"

    # Trata os N níveis de menu do .env
    menu_bruto = os.getenv(f"{prefixo}MENU", "")
    caminho_menu = [
        item.strip() for item in menu_bruto.split(",") if item.strip()
    ]

    return {
        "programa": os.getenv(f"{prefixo}PROGRAMA"),
        "usuario": os.getenv(f"{prefixo}USUARIO"),
        "senha": os.getenv(f"{prefixo}SENHA"),
        "grupo": os.getenv(f"{prefixo}GRUPO"),
        "filial": os.getenv(f"{prefixo}FILIAL"),
        "ambiente": os.getenv(f"{prefixo}AMBIENTE"),
        "menu": caminho_menu,
    }

  return _carregar_perfil


@pytest.fixture(scope="session")
def pagina_protheus(browser, protheus_url):
  """FIXTURE DE SESSÃO: Prepara a aba do navegador, navega até a URL base do Protheus

  e configura os timeouts globais.
  """
  context = browser.new_context()
  page = context.new_page()

  page.set_default_timeout(TIMEOUT_PADRAO)
  page.set_default_navigation_timeout(TIMEOUT_PADRAO)

  page.goto(protheus_url)

  yield page

  context.close()


# --- FIXTURES DOS PAGE OBJECTS DE INICIALIZAÇÃO ---


@pytest.fixture(scope="session")
def program_page(pagina_protheus):
  """Instancia a ProgramPage (Passo 1)."""
  return ProgramPage(pagina_protheus)


@pytest.fixture(scope="session")
def login_page(pagina_protheus):
  """Instancia a LoginPage (Passo 2)."""
  return LoginPage(pagina_protheus)


@pytest.fixture(scope="session")
def environment_page(pagina_protheus):
  """Instancia a EnvironmentPage (Passo 3)."""
  return EnvironmentPage(pagina_protheus)


@pytest.fixture(scope="session")
def navigation_page(pagina_protheus):
  """Instancia a NavigationPage (Passo 4)."""
  return NavigationPage(pagina_protheus)