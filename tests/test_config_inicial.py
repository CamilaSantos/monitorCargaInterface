import pytest
from pages.login_page import LoginPage  # <-- Esta linha é obrigatória!


def test_login_protheus(page, protheus_url, credenciais_protheus):
  page.goto(protheus_url)

  # Agora o Python reconhecerá a classe sem erros
  login_page = LoginPage(page)

  login_page.selecionar_modulo_inicial(credenciais_protheus["programa"])
  login_page.realizar_login(
      credenciais_protheus["usuario"], credenciais_protheus["senha"]
  )
  login_page.selecionar_parametros_ambiente(
      grupo=credenciais_protheus["grupo"],
      filial=credenciais_protheus["filial"],
      ambiente=credenciais_protheus["ambiente"],
  )