import pytest

PERFIL = "INTEGRACAO"

@pytest.fixture(scope="module")
def config(obter_config_perfil):
    return obter_config_perfil(PERFIL)


def test_01_selecionar_programa_inicial(config, program_page):
    program_page.selecionar_modulo(config["programa"])


def test_02_autenticar_usuario(config, login_page):
    login_page.realizar_login(config["usuario"], config["senha"])


def test_03_configurar_ambiente(config, environment_page):
    environment_page.selecionar_ambiente(
        grupo=config["grupo"],
        filial=config["filial"],
        ambiente=config["ambiente"],
    )


def test_04_navegar_menu(config, navigation_page):
    navigation_page.navegar(*config["menu"])


def test_05_selecionar_smart_hub(smart_hub_page):
    smart_hub_page.selecionar_menu_interno("Carga Inicial")


def test_06_selecionar_filial_carga(config, smart_hub_page):
    smart_hub_page.selecionar_filial_carga(config["filial"])