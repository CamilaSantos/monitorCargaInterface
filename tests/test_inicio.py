
import pytest

# Define qual perfil do .env será utilizado neste teste
PERFIL = "INTEGRACAO"


def test_validar_inicializacao_e_navegacao(
    obter_config_perfil,
    program_page,
    login_page,
    environment_page,
    navigation_page,
    smart_hub_page,
):
  # 1. Carrega o dicionário com as variáveis configuradas para o perfil no .env
  config = obter_config_perfil(PERFIL)

  # PASSO 1: Selecionar o Programa Inicial (Ex: SIGAMDI, SIGAFIS)
  program_page.selecionar_modulo(config["programa"])

  # PASSO 2: Autenticação (Usuário e Senha)
  login_page.realizar_login(config["usuario"], config["senha"])

  # PASSO 3: Configuração do Ambiente (Grupo, Filial, Ambiente e Data-Base)
  environment_page.selecionar_ambiente(
      grupo=config["grupo"],
      filial=config["filial"],
      ambiente=config["ambiente"],
  )

  # PASSO 4: Navegação dinâmica nos N níveis de menu lidos do .env
  navigation_page.navegar(*config["menu"])

  smart_hub_page.selecionar_menu_interno("Carga Inicial")


  # ASSERT / VALIDAÇÃO:
  # Garante que a navegação concluiu sem erros e que a página continua ativa
  assert not navigation_page.page.is_closed(), (
      "A página foi fechada inesperadamente após a navegação."
  )