import pytest

# Define qual perfil do .env será utilizado neste teste
PERFIL = "INTEGRACAO"


def etapa(titulo: str):
    """Exibe um cabeçalho formatado para destacar as etapas/baterias do teste no terminal."""
    largura = 70
    print("\n" + "=" * largura)
    print(f"  ETAPA: {titulo.upper()}".center(largura))
    print("=" * largura)


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

    etapa(f"1. SELECIONANDO PROGRAMA INICIAL ({config['programa']})")
    program_page.selecionar_modulo(config["programa"])

    etapa(f"2. AUTENTICAÇÃO COM USUÁRIO: {config['usuario']}")
    login_page.realizar_login(config["usuario"], config["senha"])

    etapa(f"3. CONFIGURAÇÃO DE AMBIENTE E FILIAL ({config['grupo']} / {config['filial']})")
    environment_page.selecionar_ambiente(
        grupo=config["grupo"],
        filial=config["filial"],
        ambiente=config["ambiente"],
    )

    etapa(f"4. NAVEGAÇÃO NO MENU DO PROTHEUS ({' > '.join(config['menu'])})")
    navigation_page.navegar(*config["menu"])

    etapa("5. SELEÇÃO DE MENU INTERNO NO SMART HUB")
    smart_hub_page.selecionar_menu_interno("Carga Inicial")

    etapa(f"6. SELEÇÃO DA FILIAL DE CARGA ({config['filial']})")
    smart_hub_page.selecionar_filial_carga(config["filial"])

    etapa("7. VALIDAÇÃO E ASSERÇÃO FINAL DO TESTE")
    # ASSERT / VALIDAÇÃO:
    # Garante que a navegação concluiu sem erros e que a página continua ativa
    assert not navigation_page.page.is_closed(), (
        "A página foi fechada inesperadamente após a navegação."
    )
    print("  └─ [OK] Teste e navegação concluídos com sucesso!")