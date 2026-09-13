import pytest
from pages.navigation_page import NavigationPage


def test_navegacao_rotina_principal(
    pagina_logada, dados_navegacao_protheus
):
  """Navega até a rotina configurada no .env aproveitando o login feito na sessão."""
  navigation_page = NavigationPage(pagina_logada)
  navigation_page.navegar_ate_rotina_completa(dados_navegacao_protheus)