import os
import time
from dotenv import load_dotenv
import pytest

from pages.program_page import ProgramPage
from pages.login_page import LoginPage
from pages.environment_page import EnvironmentPage
from pages.navigation_page import NavigationPage
from pages.smart_hub_page import SmartHubPage

load_dotenv()

TIMEOUT_PADRAO = int(os.getenv("PROTHEUS_TIMEOUT", "60000"))
CAMINHO_STYLE_CSS = os.path.join(os.path.dirname(__file__), "style.css")

# Variáveis globais para controle de tempo e armazenamento dos dados de ambiente
TEMPO_INICIO_SESSAO = 0.0
DADOS_SISTEMA = {
    "info_ambiente": "Pendente de execução (Aguardando captura da NavigationPage)"
}


def carregar_css_customizado():
    """Lê o arquivo style.css do projeto e encapsula em uma tag <style>."""
    if os.path.exists(CAMINHO_STYLE_CSS):
        with open(CAMINHO_STYLE_CSS, "r", encoding="utf-8") as f:
            conteudo_css = f.read()
        return f"<style>\n{conteudo_css}\n</style>"
    return ""


# ==============================================================================
# HOOKS DE CAPTURA DA SESSÃO, METADADOS E RELATÓRIO HTML
# ==============================================================================

def pytest_sessionstart(session):
    """Marca o horário exato de início da suíte de testes."""
    global TEMPO_INICIO_SESSAO
    TEMPO_INICIO_SESSAO = time.time()


def pytest_configure(config):
    """Gera o relatório HTML, define o Base URL e injeta configurações de ambiente."""
    os.makedirs("relatorios", exist_ok=True)
    os.makedirs("evidencias", exist_ok=True)

    protheus_url = os.getenv("PROTHEUS_URL", "Não configurado")
    config.option.base_url = protheus_url

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


@pytest.hookimpl(tryfirst=True)
def pytest_metadata(metadata, config):
    """Limpa metadados padrão do Pytest e adiciona informações customizadas da execução."""
    # Remove as informações padrão do sistema
    metadata.pop("JAVA_HOME", None)
    metadata.pop("Plugins", None)
    metadata.pop("Packages", None)
    metadata.pop("Platform", None)
    metadata.pop("Python", None)

    # Identifica o comando e o arquivo rodado no CMD
    args = config.args
    comando_executado = " ".join(args) if args else "Todos os Testes"
    nome_arquivo = "N/A"

    for arg in args:
        if "test_" in arg:
            nome_arquivo = os.path.basename(arg).split("::")[0]
            break

    # Registra os novos metadados na tabela inicial
    metadata["Arquivo de Teste Executado"] = nome_arquivo
    metadata["Comando Solicitado (CMD)"] = f"pytest {comando_executado}"
    metadata["Base URL"] = os.getenv("PROTHEUS_URL", "Não configurada")
    metadata["Informações do Sistema (Empresa/Banco/Build)"] = (
        lambda: DADOS_SISTEMA["info_ambiente"]
    )


def pytest_html_results_summary(prefix, summary, postfix, session):
    """Calcula o tempo total da execução e injeta o bloco com Status Geral no topo."""
    global TEMPO_INICIO_SESSAO

    tempo_total_segundos = time.time() - TEMPO_INICIO_SESSAO
    minutos, segundos = divmod(tempo_total_segundos, 60)
    tempo_formatado = f"{int(minutos):02d}m {int(segundos):02d}s"

    failed = session.testsfailed
    passed = getattr(session, "testspassed", 0)
    total = session.testscollected

    if failed > 0:
        status_geral = '<span style="color:#dc2626; font-weight:bold; background:#fee2e2; padding:4px 10px; border-radius:4px;">❌ FALHA (Erros Detectados)</span>'
    elif passed == total and total > 0:
        status_geral = '<span style="color:#16a34a; font-weight:bold; background:#dcfce7; padding:4px 10px; border-radius:4px;">✅ SUCESSO (Todos os testes passaram)</span>'
    else:
        status_geral = '<span style="color:#d97706; font-weight:bold; background:#fef3c7; padding:4px 10px; border-radius:4px;">⚠️ ALERTA (Execução Parcial/Incompleta)</span>'

    prefix.append(
        f"""
        <div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:8px; padding:16px; margin-bottom:20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display:flex; gap:30px; font-size:15px; font-family:'Inter', sans-serif;">
                <div><b>Status da Suíte:</b> {status_geral}</div>
                <div><b>Tempo Total de Execução:</b> <span style="font-weight:600; color:#0f172a;">{tempo_formatado}</span></div>
            </div>
        </div>
        """
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook que anexa o CSS, adiciona links customizados e insere as evidências."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        extras = getattr(report, "extras", [])
        import pytest_html

        # Injeta o CSS customizado
        css_conteudo = carregar_css_customizado()
        if css_conteudo:
            extras.append(pytest_html.extras.html(css_conteudo))

        # Preenche a coluna 'Links' com atalho para a URL do sistema
        url_sistema = os.getenv("PROTHEUS_URL", "#")
        extras.append(pytest_html.extras.url(url_sistema, name="Acessar Sistema"))

        # Anexa evidências/screenshots da etapa
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
# FIXTURES DE CAPTURA DE EVIDÊNCIAS
# ==============================================================================

@pytest.fixture
def tirar_evidencia(request):
    """Fixture para tirar print da página e incluir no relatório HTML."""

    def _capturar(page, nome_passo: str):
        if not page or page.is_closed():
            return

        nome_teste = request.node.name
        nome_arquivo_foto = f"{nome_teste}_{nome_passo}.png"
        caminho_foto = os.path.join("evidencias", nome_arquivo_foto)

        page.screenshot(path=caminho_foto)

        if not hasattr(request.node, "_evidencias"):
            request.node._evidencias = []
        request.node._evidencias.append((caminho_foto, nome_passo))

    return _capturar


@pytest.fixture
def retirar_evidencia(tirar_evidencia):
    """Alias para garantir funcionamento caso o teste solicite 'retirar_evidencia'."""
    return tirar_evidencia


# ==============================================================================
# FIXTURES DE SESSÃO E PAGE OBJECTS
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