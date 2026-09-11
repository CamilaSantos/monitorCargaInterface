def test_login_protheus(page, protheus_url, credenciais_protheus):
  page.goto(protheus_url)

  login_page = LoginPage(page)

  # 1. Programa Inicial
  login_page.selecionar_modulo_inicial(credenciais_protheus["programa"])

  # 2. Usuário e Senha
  login_page.realizar_login(
      credenciais_protheus["usuario"], credenciais_protheus["senha"]
  )

  # 3. Parâmetros de Ambiente (Grupo, Filial, Ambiente)
  login_page.selecionar_parametros_ambiente(
      grupo=credenciais_protheus["grupo"],
      filial=credenciais_protheus["filial"],
      ambiente=credenciais_protheus["ambiente"],
  )