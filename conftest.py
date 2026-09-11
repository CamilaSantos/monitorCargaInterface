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