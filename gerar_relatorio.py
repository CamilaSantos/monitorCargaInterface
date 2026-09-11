import json
import math
import os
import sys
from pathlib import Path


def formatar_tamanho_mb(mb_val):
    if mb_val is None or mb_val == 0:
        return "0 B"

    bytes_val = mb_val * (1024**2)
    unidades = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(bytes_val, 1024)))
    i = min(i, len(unidades) - 1)

    p = math.pow(1024, i)
    s = round(bytes_val / p, 2 if i > 0 else 0)

    if s.is_integer():
        s = int(s)

    return f"{s} {unidades[i]}"


def formatar_tamanho_disco_gb(tamanho_gb):
    if tamanho_gb is None or tamanho_gb <= 0:
        return "0 MB"

    bytes_val = tamanho_gb * (1024**3)
    unidades = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(bytes_val, 1024)))
    i = min(i, len(unidades) - 1)

    p = math.pow(1024, i)
    s = round(bytes_val / p, 2 if i > 0 else 0)

    if s.is_integer():
        s = int(s)

    return f"{s} {unidades[i]}"


def obter_escala_dinamica_mb(lista_mb):
    max_mb = max(lista_mb) if lista_mb else 0

    if max_mb >= 1024:
        return [round(mb / 1024, 2) for mb in lista_mb], "GB"
    elif max_mb >= 1:
        return [round(mb, 2) for mb in lista_mb], "MB"
    elif max_mb > 0:
        return [round(mb * 1024, 1) for mb in lista_mb], "KB"
    else:
        return [round(mb * (1024**2), 0) for mb in lista_mb], "Bytes"


def resolver_status_badge(execucao):
    categoria = execucao.get("categoria_status")
    status_api = execucao.get("status_api", "N/A")

    if categoria == "SUCESSO":
        return "badge-success", "check_circle", f"HTTP {status_api}"
    elif categoria == "ALERTA":
        return "badge-warning", "warning", f"HTTP {status_api}"
    elif categoria == "ERRO":
        return "badge-error", "error", f"HTTP {status_api}"

    if isinstance(status_api, int) and 200 <= status_api < 400:
        return "badge-success", "check_circle", f"HTTP {status_api}"
    elif isinstance(status_api, int) and 400 <= status_api < 500:
        return "badge-warning", "warning", f"HTTP {status_api}"
    else:
        return "badge-error", "error", f"HTTP {status_api}"


def gerar_dados_relatorio(dados_totais, caminho_css=None):
    execucao = dados_totais.get("execucao", {})
    hardware = dados_totais.get("hardware_maquina", {})
    banco = dados_totais.get("banco_dados", {})
    config_teste = dados_totais.get("configuracao_teste", {})
    resumo_geral = dados_totais.get("resumo_geral", {})
    resumo_proc = dados_totais.get("resumo_por_processo", {})
    processos = execucao.get("processos", [])

    ram_total_gb = hardware.get("ram_total_gb", 0)

    labels, duracoes, tamanhos_mb, cpus_media = [], [], [], []
    rams_pico_pct, rams_pico_gb, redes_mb = [], [], []
    qtd_zips_list, qtd_arqs_list, regs_json_list = [], [], []

    linhas_tabela_detalhada = ""

    for p in processos:
        nome = p.get("processo", "N/A")
        inicio_ext = p.get("hora_inicio_extracao", "-")
        fim_ext = p.get("hora_fim_extracao", "-")
        duracao = p.get("duracao_extracao_segundos", 0)
        fim_comp = p.get("hora_fim_compactacao", "-")
        qtd_zips = p.get("total_zips_gerados", 0)
        qtd_arqs = p.get("total_arquivos_internos", 0)
        tam_mb = p.get("tamanho_zips_mb", 0.0)

        hw = p.get("consumo_hardware", {})
        cpu_med = hw.get("cpu_media_pct", 0)
        ram_pico_mb = hw.get("ram_pico_mb", 0)
        rede_mb = round(hw.get("rede_total_mb", 0.0), 2)

        ram_pico_gb = round(ram_pico_mb / 1024, 2)
        ram_pico_pct = round((ram_pico_gb / ram_total_gb) * 100, 1) if ram_total_gb > 0 else 0
        reg_json = resumo_proc.get(nome, {}).get("registros_json_contados", 0)

        labels.append(nome)
        duracoes.append(duracao)
        tamanhos_mb.append(tam_mb)
        cpus_media.append(cpu_med)
        rams_pico_pct.append(ram_pico_pct)
        rams_pico_gb.append(ram_pico_gb)
        redes_mb.append(rede_mb)
        qtd_zips_list.append(qtd_zips)
        qtd_arqs_list.append(qtd_arqs)
        regs_json_list.append(reg_json)

        tam_formatado = formatar_tamanho_mb(tam_mb)

        linhas_tabela_detalhada += f"""
        <tr>
            <td><strong>{nome}</strong></td>
            <td>{inicio_ext}</td>
            <td>{fim_ext}</td>
            <td><strong>{duracao}s</strong></td>
            <td>{fim_comp}</td>
            <td>{qtd_zips} pacote(s)</td>
            <td>{qtd_arqs} arquivo(s)</td>
            <td><strong>{tam_formatado}</strong></td>
        </tr>
        """

    linhas_tabela_espelho = ""
    total_registros_banco = 0

    for nome_proc, info in resumo_proc.items():
        tam_fmt = formatar_tamanho_mb(info.get("tamanho_total_mb", 0))

        reg_b = info.get("registros_banco", "N/A")
        if isinstance(reg_b, int):
            total_registros_banco += reg_b
            reg_b_fmt = f"{reg_b:,}".replace(",", ".")
        elif "não encontrado" in str(reg_b).lower():
            reg_b_fmt = "Indisponível"
        else:
            reg_b_fmt = str(reg_b)

        reg_json = info.get("registros_json_contados", 0)
        reg_json_fmt = f"{reg_json:,}".replace(",", ".")

        linhas_tabela_espelho += f"""
        <tr>
            <td><strong>{nome_proc}</strong></td>
            <td><strong>{reg_b_fmt}</strong></td>
            <td><strong style="color: var(--accent-green);">{reg_json_fmt}</strong></td>
            <td>{info.get('qtd_execucoes', 1)}</td>
            <td>{info.get('total_zips', 0)} pacote(s)</td>
            <td>{info.get('total_arquivos_internos', 0)} arquivo(s)</td>
            <td><strong>{tam_fmt}</strong></td>
        </tr>
        """

    total_processos_count = len(processos)
    exibir_grafico = total_processos_count > 1 or (total_processos_count == 1 and total_registros_banco > 100000)

    tamanhos_escalados, unidade_grafico = obter_escala_dinamica_mb(tamanhos_mb)

    dados_grafico = {
        "labels": labels,
        "duracao_extracao": duracoes,
        "tamanho_escala": tamanhos_escalados,
        "unidade_tamanho": unidade_grafico,
        "qtd_zips": qtd_zips_list,
        "qtd_arqs": qtd_arqs_list,
        "registros_json": regs_json_list,
        "cpu_media": cpus_media,
        "ram_pico_pct": rams_pico_pct,
        "ram_pico_gb": rams_pico_gb,
        "ram_total_gb": ram_total_gb,
        "rede_mb": redes_mb,
    }

    estilos_css = ""
    if caminho_css and os.path.exists(caminho_css):
        with open(caminho_css, "r", encoding="utf-8") as f:
            estilos_css = f.read()

    disco_info = hardware.get("disco_monitorado", {})
    procs_solicitados = config_teste.get("processos_solicitados", [])
    str_processos_solicitados = ", ".join(procs_solicitados) if procs_solicitados else "N/A"

    badge_class, badge_icon, badge_text = resolver_status_badge(execucao)

    # Identificação do Tipo de Banco de Dados e Filial Solicitada
    tipo_db = str(banco.get("tipo", config_teste.get("banco_dados", "N/A"))).upper()
    filial_consultada = banco.get("filial_consultada", config_teste.get("filial", "N/A"))

    if "MSSQL" in tipo_db or "SQL SERVER" in tipo_db:
        db_class_color = "highlight-mssql"
    elif "ORACLE" in tipo_db:
        db_class_color = "highlight-oracle"
    else:
        db_class_color = "highlight-default"

    duracao_total_s = float(execucao.get("duracao_total_segundos", 0.0))
    throughput_calculado = (
        f"{round(total_registros_banco / duracao_total_s, 2):,}".replace(",", ".")
        if duracao_total_s > 0 and total_registros_banco > 0
        else "N/A"
    )

    return {
        "ESTILOS_CSS": estilos_css,
        "HORA_INICIO": execucao.get("hora_inicio", "-"),
        "DURACAO_TOTAL": execucao.get("duracao_total_segundos", 0),
        "THROUGHPUT_REG_SEC": throughput_calculado,
        "STATUS_API_TEXT": badge_text,
        "BADGE_CLASS": badge_class,
        "BADGE_ICON": badge_icon,
        "SO_NOME": hardware.get("sistema_operacional", "N/A"),
        "CPU_MODELO": hardware.get("processador", "N/A"),
        "CPU_CORES": f"{hardware.get('nucleos_fisicos', 0)} Cores / {hardware.get('nucleos_logicos', 0)} Threads",
        "RAM_TOTAL_SPEC": f"{ram_total_gb} GB",
        "DISCO_TOTAL_SPEC": f"{disco_info.get('total_gb', 0)} GB",
        "DISCO_LIVRE_INICIO": f"{disco_info.get('livre_inicio_gb', 0.0)} GB",
        "DISCO_LIVRE_FIM": f"{disco_info.get('livre_fim_gb', 0.0)} GB",
        "DB_TIPO": tipo_db,
        "FILIAL": filial_consultada,
        "DB_CLASS_COLOR": db_class_color,
        "DB_HOST": banco.get("host", "localhost"),
        "DB_PORTA": banco.get("porta", "N/A"),
        "PAGE_SIZE": config_teste.get("page_size", "N/A"),
        "THREADS": config_teste.get("threads", "N/A"),
        "SERVICO_MONITORADO": config_teste.get("servico_monitorado", "appserver.exe"),
        "PROCESSOS_SOLICITADOS": str_processos_solicitados,
        "TOTAL_REGISTROS_BANCO": f"{total_registros_banco:,}".replace(",", "."),
        "TOTAL_PROCESSOS": resumo_geral.get("total_processos_executados", len(resumo_proc)),
        "TOTAL_ZIPS_GERADOS": resumo_geral.get("total_zips_gerados", 0),
        "TOTAL_ARQUIVOS_INTERNOS": resumo_geral.get("total_arquivos_internos", 0),
        "VOLUME_TOTAL_ZIPS": formatar_tamanho_mb(resumo_geral.get("volume_total_zips_mb", 0)),
        "DISCO_UNIDADE": disco_info.get("unidade", "C:"),
        "DISCO_CONSUMIDO": formatar_tamanho_disco_gb(resumo_geral.get("espaco_disco_consumido_gb", 0)),
        "TABELA_ESPELHO_PROCESSOS": linhas_tabela_espelho,
        "TABELA_PROCESSOS": linhas_tabela_detalhada,
        "DADOS_GRAFICO_PROCESSOS": json.dumps(dados_grafico),
        "EXIBIR_GRAFICO": "true" if exibir_grafico else "false",
        "MOSTRAR_GRAFICO_CLASS": "" if exibir_grafico else "display-none",
    }


def renderizar_e_salvar_relatorio(pasta_sessao_str):
    pasta_sessao = Path(pasta_sessao_str)
    caminho_json = pasta_sessao / "dados.json"
    caminho_saida_html = pasta_sessao / "relatorio.html"

    caminho_template = Path("template.html")
    caminho_css = Path("style.css")

    if not caminho_json.exists():
        print(f"❌ [ERRO] Arquivo de dados não encontrado em: {caminho_json}")
        return

    if not caminho_template.exists():
        print(f"❌ [ERRO] Template HTML não encontrado em: {caminho_template}")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        dados_totais = json.load(f)

    dicionario_substituicao = gerar_dados_relatorio(dados_totais, caminho_css)

    with open(caminho_template, "r", encoding="utf-8") as f:
        html_conteudo = f.read()

    for chave, valor in dicionario_substituicao.items():
        tag = f"{{{{{chave}}}}}"
        html_conteudo = html_conteudo.replace(tag, str(valor))

    with open(caminho_saida_html, "w", encoding="utf-8") as f:
        f.write(html_conteudo)

    print(f"✅ Relatório HTML gerado com sucesso em: {caminho_saida_html.resolve()}")


def obter_ultima_pasta_historicos(pasta_historicos="historicos"):
    caminho_historicos = Path(pasta_historicos)
    if not caminho_historicos.exists() or not caminho_historicos.is_dir():
        print(f"❌ [ERRO] A pasta de histórico '{pasta_historicos}' não foi encontrada.")
        return None

    pastas = [p for p in caminho_historicos.iterdir() if p.is_dir()]
    if not pastas:
        print(f"❌ [ERRO] Nenhum relatório/sessão encontrado em '{pasta_historicos}'.")
        return None

    return max(pastas, key=lambda p: p.stat().st_mtime)


if __name__ == "__main__":
    pasta_alvo = sys.argv[1] if len(sys.argv) > 1 else obter_ultima_pasta_historicos()
    if pasta_alvo:
        print(f"🔄 Renderizando relatório para a sessão: {pasta_alvo}")
        renderizar_e_salvar_relatorio(pasta_alvo)