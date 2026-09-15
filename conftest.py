import os
from dotenv import load_dotenv
import pytest

from pages.program_page import ProgramPage
from pages.login_page import LoginPage
from pages.environment_page import EnvironmentPage
from pages.navigation_page import NavigationPage
from pages.smart_hub_page import SmartHubPage

load_dotenv()

TIMEOUT_PADRAO = int(os.getenv("PROTHEUS_TIMEOUT", "60000"))

# Caminho do seu arquivo style.css existente (ajuste o caminho relativo conforme sua pasta)
CAMINHO_STYLE_CSS = os.path.join(os.path.dirname(__file__), "style.css")


def carregar_css_customizado():
    """Lê o arquivo style.css do projeto e encapsula em uma tag <style>."""
    if os.path.exists(CAMINHO_STYLE_CSS):
        with open(CAMINHO_STYLE_CSS, "r", encoding="utf-8") as f:
            conteudo_css = f.read()
        return f"<style>\n{conteudo_css}\n</style>"
    return ""


def pytest_configure(config):
    """Gera o relatório HTML automaticamente com o mesmo nome do arquivo do teste e associa o CSS."""
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


def pytest_html_report_title(report):
    """Define o título no relatório HTML."""
    report.title = "Relatório de Execução de Testes - Protheus Smart Hub"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook que anexa o CSS do arquivo style.css e insere as evidências no relatório."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        extras = getattr(report, "extras", [])

        # Lê e injeta o conteúdo do arquivo style.css
        css_conteudo = carregar_css_customizado()
        if css_conteudo:
            import pytest_html
            extras.append(pytest_html.extras.html(css_conteudo))

        evidencias = getattr(item, "_evidencias", [])
        for caminho_foto, nome_passo in evidencias:
            try:
                caminho_relativo = os.path.relpath(caminho_foto, start="relatorios")
                
                html_embed = (
                    f'<div class="evidencia-card">'
                    f'  <div class="evidencia-titulo">📸 <b>Etapa Concluída:</b> {nome_passo}</div>'
                    f'  <img class="evidencia-img" src="{caminho_relativo}" alt="{nome_passo}" '
                    f'       onclick="window.open(this.src)" title="Clique para ampliar"/>'
                    f'</div>'
                )
                extras.append(pytest_html.extras.html(html_embed))
            except Exception:
                pass

        report.extras = extras


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