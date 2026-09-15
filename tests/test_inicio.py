import pytest

PERFIL = "INTEGRACAO"


@pytest.fixture(scope="module")
def config(obter_config_perfil):
    return obter_config_perfil(PERFIL)


def test_01_selecionar_programa_inicial(config, program_page, tirar_evidencia):
    program_page.selecionar_modulo(config["programa"])
    tirar_evidencia(program_page.page, "01_programa_inicial")


def test_02_autenticar_usuario(config, login_page, tirar_evidencia):
    login_page.realizar_login(config["usuario"], config["senha"])
    tirar_evidencia(login_page.page, "02_autenticacao")


def test_03_autenticar_e_selecionar_ambiente(config, environment_page, tirar_evidencia):
    environment_page.selecionar_ambiente(config["grupo"], config["filial"], config["ambiente"])
    tirar_evidencia(environment_page.page, "03_ambiente_selecionado")


def test_04_navegar_menu(config, navigation_page, tirar_evidencia):
    navigation_page.navegar(*config["menu"])
    tirar_evidencia(navigation_page.page, "04_navegacao_menu")


def test_05_selecionar_smart_hub(smart_hub_page, tirar_evidencia):
    smart_hub_page.selecionar_menu_interno("Carga Inicial")
    tirar_evidencia(smart_hub_page.page, "05_smart_hub_carga_inicial")


def test_06_selecionar_filial_carga(config, smart_hub_page, tirar_evidencia):
    smart_hub_page.selecionar_filial_carga(config["filial"])
    tirar_evidencia(smart_hub_page.page, "06_filial_selecionada")