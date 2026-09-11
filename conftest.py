import os
from dotenv import load_dotenv
import pytest

load_dotenv()


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

@pytest.fixture(autouse=True)
def configurar_timeout_global(page):
  """Aplica um timeout global de 60 segundos para todas as páginas e seletores do projeto."""
  # Define o tempo de espera padrão para interações (click, fill, wait_for, etc.)
  page.set_default_timeout(60000)

  # Define o tempo de espera padrão para navegações de página (goto)
  page.set_default_navigation_timeout(60000)