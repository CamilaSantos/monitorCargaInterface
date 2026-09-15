import os
from dotenv import load_dotenv
import pytest

from pages.program_page import ProgramPage
from pages.login_page import LoginPage
from pages.environment_page import EnvironmentPage
from pages.navigation_page import NavigationPage
from pages.smart_hub_page import SmartHubPage

load_dotenv()


# Timeout padrão lido do .env (padrão 60s)
TIMEOUT_PADRAO = int(os.getenv("PROTHEUS_TIMEOUT", "60000"))


# ==============================================================================
# CONFIGURAÇÃO DE RELATÓRIO DINÂMICO E EVIDÊNCIAS (PYTEST-HTML)
# ==============================================================================

def pytest_configure(config):
    """Gera o relatório HTML automaticamente com o mesmo nome do arquivo do teste."""
    os.makedirs("relatorios", exist_ok=True)
    os.makedirs("evidencias", exist_ok=True)

    args = config.args
    nome_base = "relatorio_execucao"

    for arg in args:
        if "test_" in arg:
            nome_limpo = os.path.basename(arg).split("::")[0].replace(".py", "")
            nome_base = f"{nome_limpo}"
            break

    caminho_html = os.path.join("relatorios", f"{nome_base}.html")
    config.option.htmlpath = caminho_html
    config.option.self_contained_html = True


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook que anexa as evidências (imagens) capturadas no relatório HTML final."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        extras = getattr(report, "extras", [])
        
        # Anexa todas as fotos registradas no teste/etapa
        evidencias = getattr(item, "_evidencias", [])
        for caminho_foto, nome_passo in evidencias:
            try:
                import pytest_html
                html_embed = (
                    f'<div><p style="font-weight:bold; margin-top:10px;">Evidência: {nome_passo}</p>'
                    f'<img src="../{caminho_foto}" alt="{nome_passo}" '
                    f'style="width:600px; height:auto; border:1px solid #ccc; border-radius:4px;" '
                    f'onclick="window.open(this.src)"/></div>'
                )
                extras.append(pytest_html.extras.html(html_embed))
            except Exception:
                pass

        report.extras = extras


@pytest.fixture
def tirar_evidencia(request):
    """Fixture para tirar print da página e incluir no relatório HTML sem erro de fixture extra."""
    
    def _capturar(page, nome_passo: str):
        if not page or page.is_closed():
            return

        nome_teste = request.node.name
        nome_arquivo_foto = f"{nome_teste}_{nome_passo}.png"
        caminho_foto = os.path.join("evidencias", nome_arquivo_foto)

        # Captura screenshot no Playwright
        page.screenshot(path=caminho_foto)

        # Registra a evidência no item do Pytest para o hook salvar no relatório
        if not hasattr(request.node, "_evidencias"):
            request.node._evidencias = []
        request.node._evidencias.append((caminho_foto, nome_passo))

    return _capturar


# ==============================================================================
# FIXTURES EXISTENTES
# ==============================================================================

@pytest.fixture(scope="session")
def protheus_url():
    return os.getenv("PROTHEUS_URL")


@pytest.fixture(scope="session")
def obter_config_perfil():
    """Lê do .env as configurações de um perfil específico usando o prefixo.

    Exemplo de uso no teste: config = obter_config_perfil("COMERCIAL")
    """

    def _carregar_perfil(perfil: str) -> dict:
        prefixo = f"PROTHEUS_{perfil.upper()}_"

        # Trata os N níveis de menu do .env
        menu_bruto = os.getenv(f"{prefixo}MENU", "")
        caminho_menu = [
            item.strip() for item in menu_bruto.split(",") if item.strip()
        ]

        return {
            "programa": os.getenv(f"{prefixo}PROGRAMA"),
            "usuario": os.getenv(f"{prefixo}USUARIO"),
            "senha": os.getenv(f"{prefixo}SENHA"),
            "grupo": os.getenv(f"{prefixo}GRUPO"),
            "filial": os.getenv(f"{prefixo}FILIAL"),
            "ambiente": os.getenv(f"{prefixo}AMBIENTE"),
            "menu": caminho_menu,
        }

    return _carregar_perfil


@pytest.fixture(scope="session")
def pagina_protheus(browser, protheus_url):
    """FIXTURE DE SESSÃO: Prepara a aba do navegador, navega até a URL base do Protheus
    e configura os timeouts globais.
    """
    context = browser.new_context()
    page = context.new_page()

    page.set_default_timeout(TIMEOUT_PADRAO)
    page.set_default_navigation_timeout(TIMEOUT_PADRAO)

    page.goto(protheus_url)

    yield page

    context.close()


# --- FIXTURES DOS PAGE OBJECTS DE INICIALIZAÇÃO ---


@pytest.fixture(scope="session")
def program_page(pagina_protheus):
    """Instancia a ProgramPage (Passo 1)."""
    return ProgramPage(pagina_protheus)


@pytest.fixture(scope="session")
def login_page(pagina_protheus):
    """Instancia a LoginPage (Passo 2)."""
    return LoginPage(pagina_protheus)


@pytest.fixture(scope="session")
def environment_page(pagina_protheus):
    """Instancia a EnvironmentPage (Passo 3)."""
    return EnvironmentPage(pagina_protheus)


@pytest.fixture(scope="session")
def navigation_page(pagina_protheus):
    """Instancia a NavigationPage (Passo 4)."""
    return NavigationPage(pagina_protheus)


@pytest.fixture(scope="session")
def smart_hub_page(pagina_protheus):
    """Instancia a SmartHubPage para interação no iframe PO UI (Passo 5)."""
    return SmartHubPage(pagina_protheus)