import pytest
from pages.login_page import LoginPage


def test_00_autenticacao_protheus(page, protheus_url, credenciais_protheus):
  """
  Teste dedicado exclusivamente a validar a tela de login e acesso ao ambiente.
  """
  page.goto(protheus_url)

  login_page = LoginPage(page)
  login_page.fazer_login_completo(
      programa=credenciais_protheus["programa"],
      usuario=credenciais_protheus["usuario"],
      senha=credenciais_protheus["senha"],
      grupo=credenciais_protheus["grupo"],
      filial=credenciais_protheus["filial"],
      ambiente=credenciais_protheus["ambiente"],
  )