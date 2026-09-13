import pytest
from pages.login_page import LoginPage
from pages.navigation_page import NavigationPage


def test_login_e_navegacao_protheus(
    page, protheus_url, credenciais_protheus, dados_navegacao_protheus
):
  # 1. Acesso à URL inicial
  page.goto(protheus_url)

  # 2. Instância e Execução do Login Completo
  login_page = LoginPage(page)
  login_page.fazer_login_completo(
      programa=credenciais_protheus["programa"],
      usuario=credenciais_protheus["usuario"],
      senha=credenciais_protheus["senha"],
      grupo=credenciais_protheus["grupo"],
      filial=credenciais_protheus["filial"],
      ambiente=credenciais_protheus["ambiente"],
  )

  # 3. Instância e Execução da Navegação no Menu
  navigation_page = NavigationPage(page)
  navigation_page.navegar_ate_rotina_completa(dados_navegacao_protheus)