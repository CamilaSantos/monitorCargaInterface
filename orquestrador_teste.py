import csv
import json
import os
import platform
import re
import statistics
import subprocess
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path

import psutil

# Importação do módulo dinâmico de consulta de banco
try:
    from consulta_banco import consultar_totais_por_processos
except ImportError:
    def consultar_totais_por_processos(banco_dados, processos_solicitados, filial_informada, config_banco_custom=None):
        return {
            p.upper(): "Módulo 'consulta_banco.py' não encontrado"
            for p in processos_solicitados
        }


CAMINHO_CONSOLE_LOG = Path("C:/PSH-2510/console_2510.log")

PADRAO_REGEX_INICIO = re.compile(
    r"pshExtractor:\s*Iniciando\s+extra[çc]?[ãa]?o\s+do\s+processo:\s*([A-Za-z0-9_\s-]+?)\s*-\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
    re.IGNORECASE,
)

PADRAO_REGEX_FIM = re.compile(
    r"pshExtractor:\s*Finalizada\s+a\s+extra[çc]?[ãa]?o\s+dos\s+processos\.(?:\s*-\s*|\s+)(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
    re.IGNORECASE,
)


def obter_nome_tecnico_processador():
    proc_tecnico = ""
    try:
        if platform.system() == "Windows":
            comando = "wmic cpu get Name"
            saida = subprocess.check_output(
                comando, shell=True, stderr=subprocess.DEVNULL
            )
            linhas = [
                line.strip()
                for line in saida.decode("utf-8", errors="ignore").splitlines()
                if line.strip()
            ]
            if len(linhas) > 1:
                proc_tecnico = linhas[1]
        elif platform.system() == "Linux":
            comando = (
                "cat /proc/cpuinfo | grep 'model name' | head -n 1 | cut -d ':' -f2"
            )
            saida = subprocess.check_output(comando, shell=True)
            proc_tecnico = saida.decode("utf-8").strip()
    except Exception:
        proc_tecnico = ""

    if not proc_tecnico:
        proc_tecnico = platform.processor() or "Não identificado"

    return proc_tecnico


def obter_informacoes_maquina(pasta_destino):
    caminho_path = Path(pasta_destino)
    unidade_disco = caminho_path.anchor or "C:\\"

    try:
        disco_info = psutil.disk_usage(unidade_disco)
        disco_total_gb = round(disco_info.total / (1024**3), 2)
        disco_livre_gb = round(disco_info.free / (1024**3), 2)
    except Exception:
        disco_total_gb = 0.0
        disco_livre_gb = 0.0

    return {
        "sistema_operacional": f"{platform.system()} {platform.release()}",
        "versao_so": platform.version(),
        "arquitetura": platform.architecture()[0],
        "nome_computador": platform.node(),
        "processador": obter_nome_tecnico_processador(),
        "nucleos_fisicos": psutil.cpu_count(logical=False) or 0,
        "nucleos_logicos": psutil.cpu_count(logical=True) or 0,
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "disco_monitorado": {
            "unidade": unidade_disco,
            "total_gb": disco_total_gb,
            "livre_inicio_gb": disco_livre_gb,
            "livre_fim_gb": disco_livre_gb,
        },
    }


class RoboMonitorRecursos(threading.Thread):

    def __init__(self, nome_servico="appserver.exe", intervalo=0.2):
        super().__init__()
        self.intervalo = intervalo
        self.nome_servico = nome_servico.strip().lower()
        self._rodando = True
        self.amostras = []

    def _obter_processos_alvo(self):
        if not self.nome_servico:
            return []

        processos = []
        for p in psutil.process_iter(["pid", "name"]):
            try:
                if p.info["name"] and self.nome_servico in p.info["name"].lower():
                    processos.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processos

    def run(self):
        psutil.cpu_percent(interval=None)
        net_init = psutil.net_io_counters()
        bytes_iniciais = net_init.bytes_sent + net_init.bytes_recv

        while self._rodando:
            try:
                ts_atual = datetime.now()

                if self.nome_servico:
                    procs = self._obter_processos_alvo()
                    cpu_total = 0.0
                    ram_total_mb = 0.0

                    for p in procs:
                        try:
                            cpu_total += p.cpu_percent(interval=None)
                            ram_total_mb += p.memory_info().rss / (1024**2)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                    cpu = round(cpu_total, 1)
                    ram = round(ram_total_mb, 2)
                else:
                    cpu = psutil.cpu_percent(interval=None)
                    ram = psutil.virtual_memory().used / (1024**2)

                net_atual = psutil.net_io_counters()
                bytes_totais = net_atual.bytes_sent + net_atual.bytes_recv
                rede_mb = (bytes_totais - bytes_iniciais) / (1024**2)

                self.amostras.append({
                    "ts": ts_atual,
                    "cpu": cpu,
                    "ram": ram,
                    "rede_mb": round(max(rede_mb, 0.0), 2),
                })
            except Exception:
                pass
            time.sleep(self.intervalo)

    def parar(self):
        self._rodando = False
        return self.amostras

    def obter_metricas_janela(self, dt_inicio, dt_fim):
        amostras_janela = [
            a for a in self.amostras if dt_inicio <= a["ts"] <= dt_fim
        ]

        if not amostras_janela:
            return {
                "servico_monitorado": self.nome_servico if self.nome_servico else "Sistema Global",
                "cpu_media_pct": 0.0,
                "cpu_pico_pct": 0.0,
                "ram_media_mb": 0.0,
                "ram_pico_mb": 0.0,
                "rede_total_mb": 0.0,
            }

        cpus = [a["cpu"] for a in amostras_janela]
        rams = [a["ram"] for a in amostras_janela]
        redes = [a["rede_mb"] for a in amostras_janela]

        delta_rede = max(redes) - min(redes) if redes else 0.0

        return {
            "servico_monitorado": self.nome_servico if self.nome_servico else "Sistema Global",
            "cpu_media_pct": round(statistics.mean(cpus), 1),
            "cpu_pico_pct": round(max(cpus), 1),
            "ram_media_mb": round(statistics.mean(rams), 2),
            "ram_pico_mb": round(max(rams), 2),
            "rede_total_mb": round(max(delta_rede, 0.0), 2),
        }


def obter_ponteiro_fim_log(caminho_log):
    if caminho_log.exists():
        try:
            with open(caminho_log, "rb") as f:
                f.seek(0, os.SEEK_END)
                return f.tell()
        except Exception:
            return 0
    return 0


def monitorar_log_processos(
    caminho_log,
    posicao_inicio,
    lista_processos,
    timeout_global=1800,
):
    print(f"\n👀 [MONITOR LOG] Escutando processos no log: {lista_processos}")
    inicio_espera = time.time()
    ponteiro_atual = posicao_inicio

    linha_tempo_processos = []
    processo_atual = None
    dt_inicio_atual = None

    while True:
        if time.time() - inicio_espera > timeout_global:
            print("⚠️ [MONITOR LOG] Timeout atingido.")
            break

        if caminho_log.exists():
            try:
                with open(caminho_log, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(ponteiro_atual)
                    linhas = f.readlines()
                    ponteiro_atual = f.tell()

                    for linha in linhas:
                        linha_str = linha.strip()
                        if not linha_str:
                            continue

                        match_inicio = PADRAO_REGEX_INICIO.search(linha_str)
                        if match_inicio:
                            nome_proc = match_inicio.group(1).strip().upper()
                            ts_str = match_inicio.group(2)
                            dt_evento = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")

                            if processo_atual and dt_inicio_atual:
                                linha_tempo_processos.append({
                                    "processo": processo_atual,
                                    "dt_inicio": dt_inicio_atual,
                                    "dt_fim": dt_evento,
                                    "duracao_segundos": round(
                                        max((dt_evento - dt_inicio_atual).total_seconds(), 0.0),
                                        2,
                                    ),
                                })

                            processo_atual = nome_proc
                            dt_inicio_atual = dt_evento

                        match_fim = PADRAO_REGEX_FIM.search(linha_str)
                        if match_fim:
                            ts_fim_str = match_fim.group(1)
                            dt_fim_evento = datetime.strptime(
                                ts_fim_str, "%Y-%m-%dT%H:%M:%S"
                            )

                            if processo_atual and dt_inicio_atual:
                                duracao = round(
                                    max(
                                        (dt_fim_evento - dt_inicio_atual).total_seconds(), 0.0
                                    ),
                                    2,
                                )
                                linha_tempo_processos.append({
                                    "processo": processo_atual,
                                    "dt_inicio": dt_inicio_atual,
                                    "dt_fim": dt_fim_evento,
                                    "duracao_segundos": duracao,
                                })

                            return linha_tempo_processos

            except Exception as e:
                print(f"⚠️ [LOG ERROR] {e}")

        time.sleep(0.1)

    return linha_tempo_processos


def inspecionar_conteudo_zip(caminho_zip, page_size_esperado):
    detalhes_jsons = []
    total_registros_zip = 0

    try:
        with zipfile.ZipFile(caminho_zip, "r") as z:
            for info in z.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".json"):
                    continue

                tamanho_json_mb = round(info.file_size / (1024**2), 4)
                qtd_registros = 0

                with z.open(info) as f:
                    try:
                        conteudo = json.load(f)
                        if isinstance(conteudo, list):
                            qtd_registros = len(conteudo)
                        elif isinstance(conteudo, dict):
                            for val in conteudo.values():
                                if isinstance(val, list):
                                    qtd_registros = len(val)
                                    break
                    except Exception:
                        f.seek(0)
                        texto = f.read().decode("utf-8", errors="ignore")
                        qtd_registros = texto.count("{")

                total_registros_zip += qtd_registros
                conforme_pagesize = (qtd_registros == page_size_esperado)

                detalhes_jsons.append({
                    "nome_json": info.filename,
                    "tamanho_json_mb": tamanho_json_mb,
                    "registros_contados": qtd_registros,
                    "conforme_pagesize": conforme_pagesize,
                })

    except Exception as e:
        print(f"⚠️ [ERRO ZIP] Falha ao inspecionar {caminho_zip.name}: {e}")

    return detalhes_jsons, total_registros_zip


def consolidar_dados_pasta_por_processo(pasta, lista_processos, dt_inicio_execucao, page_size_esperado):
    resultado = {}

    for proc in lista_processos:
        resultado[proc.upper()] = {
            "total_zips": 0,
            "total_arquivos_internos": 0,
            "total_registros_json": 0,
            "tamanho_total_mb": 0.0,
            "dt_ultimo_zip": None,
            "lista_zips": [],
        }

    if not pasta.exists():
        return resultado

    arquivos_zip = set(
        arq.resolve() for arq in pasta.rglob("*") if arq.suffix.lower() == ".zip"
    )

    for arq in arquivos_zip:
        mtime_arq = datetime.fromtimestamp(arq.stat().st_mtime)

        if (mtime_arq - dt_inicio_execucao).total_seconds() < -2:
            continue

        tamanho_bytes = arq.stat().st_size
        tamanho_mb = tamanho_bytes / (1024**2)

        detalhes_jsons, qtd_registros_zip = inspecionar_conteudo_zip(
            arq, page_size_esperado
        )
        qtd_arquivos_internos = len(detalhes_jsons)

        nome_arq_clean = arq.name.lower().replace("_", "").replace("-", "")

        proc_encontrado = None
        for proc in lista_processos:
            proc_clean = proc.lower().replace("_", "").replace("-", "").strip()
            if proc_clean in nome_arq_clean:
                proc_encontrado = proc.upper()
                break

        if proc_encontrado in resultado:
            resultado[proc_encontrado]["total_zips"] += 1
            resultado[proc_encontrado]["total_arquivos_internos"] += qtd_arquivos_internos
            resultado[proc_encontrado]["total_registros_json"] += qtd_registros_zip
            resultado[proc_encontrado]["tamanho_total_mb"] += tamanho_mb
            resultado[proc_encontrado]["lista_zips"].append({
                "nome": arq.name,
                "tamanho_mb": round(tamanho_mb, 6),
                "qtd_arquivos_internos": qtd_arquivos_internos,
                "total_registros_zip": qtd_registros_zip,
                "arquivos_json": detalhes_jsons,
                "data_modificacao": mtime_arq.strftime("%Y-%m-%d %H:%M:%S"),
            })

            dt_atual = resultado[proc_encontrado]["dt_ultimo_zip"]
            if dt_atual is None or mtime_arq > dt_atual:
                resultado[proc_encontrado]["dt_ultimo_zip"] = mtime_arq

    return resultado


def salvar_historico_csv(caminho_csv, lista_processos_relatorio):
    campos = [
        "processo",
        "registros_banco",
        "registros_json_contados",
        "hora_inicio_extracao",
        "hora_fim_extracao",
        "duracao_extracao_segundos",
        "hora_fim_compactacao",
        "total_zips_gerados",
        "total_arquivos_internos",
        "tamanho_zips_mb",
        "cpu_media_pct",
        "cpu_pico_pct",
        "ram_media_mb",
        "ram_pico_mb",
        "rede_total_mb",
    ]

    with open(caminho_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()

        for item in lista_processos_relatorio:
            hw = item.get("consumo_hardware", {})
            writer.writerow({
                "processo": item.get("processo", ""),
                "registros_banco": item.get("registros_banco", "N/A"),
                "registros_json_contados": item.get("registros_json_contados", 0),
                "hora_inicio_extracao": item.get("hora_inicio_extracao", ""),
                "hora_fim_extracao": item.get("hora_fim_extracao", ""),
                "duracao_extracao_segundos": item.get(
                    "duracao_extracao_segundos", 0
                ),
                "hora_fim_compactacao": item.get("hora_fim_compactacao", ""),
                "total_zips_gerados": item.get("total_zips_gerados", 0),
                "total_arquivos_internos": item.get("total_arquivos_internos", 0),
                "tamanho_zips_mb": round(item.get("tamanho_zips_mb", 0.0), 6),
                "cpu_media_pct": hw.get("cpu_media_pct", 0.0),
                "cpu_pico_pct": hw.get("cpu_pico_pct", 0.0),
                "ram_media_mb": hw.get("ram_media_mb", 0.0),
                "ram_pico_mb": hw.get("ram_pico_mb", 0.0),
                "rede_total_mb": hw.get("rede_total_mb", 0.0),
            })


def gerar_resumo_consolidado_por_processo(
    processos_relatorio, mapa_totais_banco
):
    resumo = {}
    for item in processos_relatorio:
        nome = item["processo"]
        if nome not in resumo:
            resumo[nome] = {
                "qtd_execucoes": 0,
                "registros_banco": mapa_totais_banco.get(nome, "N/A"),
                "registros_json_contados": 0,
                "total_zips": 0,
                "total_arquivos_internos": 0,
                "tamanho_total_mb": 0.0,
                "duracao_total_segundos": 0.0,
            }

        resumo[nome]["qtd_execucoes"] += 1
        resumo[nome]["registros_json_contados"] += item.get("registros_json_contados", 0)
        resumo[nome]["total_zips"] += item["total_zips_gerados"]
        resumo[nome]["total_arquivos_internos"] += item["total_arquivos_internos"]
        resumo[nome]["tamanho_total_mb"] += item["tamanho_zips_mb"]
        resumo[nome]["duracao_total_segundos"] += item["duracao_extracao_segundos"]

    for nome in resumo:
        resumo[nome]["tamanho_total_mb"] = round(resumo[nome]["tamanho_total_mb"], 6)
        resumo[nome]["duracao_total_segundos"] = round(
            resumo[nome]["duracao_total_segundos"], 2
        )

    return resumo


def executar_orquestrador(
    banco_dados="MSSQL",
    threads=1,
    page_size=10000,
    processos=None,
    filial="f D 01",
    nome_servico="appserver.exe",
    config_banco_custom=None,
):
    """
    Função principal do orquestrador chamada pelo Pytest.
    Recebe os parâmetros dinâmicos e repassa para a consulta no banco
    e no relatório final.
    """
    if processos is None:
        processos = ["COMPARTILHAMENT"]

    lista_processos = [p.strip().upper() for p in processos]
    pasta_destino = Path("C:/PSH-2510/Protheus_data/autocom/psh/extractor/")
    page_size_int = int(page_size)

    print(f"\n🚀 [ORQUESTRADOR] Iniciando monitoramento:")
    print(f"   - Banco: {banco_dados}")
    print(f"   - Filial: {filial}")
    print(f"   - Processos: {lista_processos}")
    print(f"   - Threads: {threads} | PageSize: {page_size_int}")

    # Consulta totais no Banco de Dados repassando filial e o tipo do banco dinamicamente
    mapa_totais_banco = consultar_totais_por_processos(
        banco_dados=banco_dados,
        processos_solicitados=lista_processos,
        filial_informada=filial,
        config_banco_custom=config_banco_custom,
    )

    dt_inicio = datetime.now()
    timestamp_execucao = dt_inicio.strftime("%Y%m%d_%H%M%S")
    pasta_sessao = Path("historicos") / timestamp_execucao
    pasta_sessao.mkdir(parents=True, exist_ok=True)

    info_maquina = obter_informacoes_maquina(pasta_destino)
    unidade_disco = pasta_destino.anchor or "C:\\"

    disco_inicio = psutil.disk_usage(unidade_disco)
    disco_livre_inicio_gb = round(disco_inicio.free / (1024**3), 2)

    posicao_log_inicio = obter_ponteiro_fim_log(CAMINHO_CONSOLE_LOG)

    # Inicia robô de monitoramento de recursos
    robo_recursos = RoboMonitorRecursos(nome_servico=nome_servico, intervalo=0.2)
    robo_recursos.start()

    tempo_inicio = time.time()
    hora_inicio_str = dt_inicio.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    # Monitora o log do processo local
    linha_tempo_processos = monitorar_log_processos(
        caminho_log=CAMINHO_CONSOLE_LOG,
        posicao_inicio=posicao_log_inicio,
        lista_processos=lista_processos,
    )

    robo_recursos.parar()

    tempo_fim = time.time()
    duracao_total_teste = round(tempo_fim - tempo_inicio, 2)
    hora_fim_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    disco_fim = psutil.disk_usage(unidade_disco)
    disco_livre_fim_gb = round(disco_fim.free / (1024**3), 2)

    info_maquina["disco_monitorado"]["livre_inicio_gb"] = disco_livre_inicio_gb
    info_maquina["disco_monitorado"]["livre_fim_gb"] = disco_livre_fim_gb

    espaco_consumido_bytes = disco_inicio.free - disco_fim.free
    espaco_consumido_gb = round(max(espaco_consumido_bytes, 0) / (1024**3), 4)

    dados_zip_processos = consolidar_dados_pasta_por_processo(
        pasta_destino, lista_processos, dt_inicio, page_size_int
    )

    processos_relatorio = []
    for item in linha_tempo_processos:
        proc_nome = item["processo"]
        dt_i = item["dt_inicio"]
        dt_f = item["dt_fim"]

        metricas_proc = robo_recursos.obter_metricas_janela(dt_i, dt_f)
        zips_info = dados_zip_processos.get(
            proc_nome,
            {
                "total_zips": 0,
                "total_arquivos_internos": 0,
                "total_registros_json": 0,
                "tamanho_total_mb": 0.0,
                "dt_ultimo_zip": None,
                "lista_zips": [],
            },
        )

        dt_fim_comp = zips_info["dt_ultimo_zip"]
        str_fim_comp = (
            dt_fim_comp.strftime("%Y-%m-%d %H:%M:%S")
            if dt_fim_comp
            else dt_f.strftime("%Y-%m-%d %H:%M:%S")
        )

        qtd_banco = mapa_totais_banco.get(proc_nome, "N/A")

        processos_relatorio.append({
            "processo": proc_nome,
            "registros_banco": qtd_banco,
            "registros_json_contados": zips_info["total_registros_json"],
            "hora_inicio_extracao": dt_i.strftime("%Y-%m-%d %H:%M:%S"),
            "hora_fim_extracao": dt_f.strftime("%Y-%m-%d %H:%M:%S"),
            "duracao_extracao_segundos": item["duracao_segundos"],
            "hora_fim_compactacao": str_fim_comp,
            "total_zips_gerados": zips_info["total_zips"],
            "total_arquivos_internos": zips_info["total_arquivos_internos"],
            "tamanho_zips_mb": round(zips_info["tamanho_total_mb"], 6),
            "consumo_hardware": metricas_proc,
            "detalhe_zips": zips_info["lista_zips"],
        })

    resumo_por_processo = gerar_resumo_consolidado_por_processo(
        processos_relatorio, mapa_totais_banco
    )

    relatorio = {
        "hardware_maquina": info_maquina,
        "banco_dados": {
            "tipo": banco_dados.upper(),
            "filial_consultada": filial,
        },
        "configuracao_teste": {
            "banco_dados": banco_dados.upper(),
            "filial": filial,
            "processos_solicitados": lista_processos,
            "pasta_destino_extractor": str(pasta_destino.resolve()),
            "page_size": page_size_int,
            "threads": int(threads),
            "servico_monitorado": nome_servico if nome_servico else "Sistema Global",
        },
        "execucao": {
            "hora_inicio": hora_inicio_str,
            "hora_fim": hora_fim_str,
            "duracao_total_segundos": duracao_total_teste,
            "processos": processos_relatorio,
        },
        "resumo_por_processo": resumo_por_processo,
        "resumo_geral": {
            "total_processos_executados": len(resumo_por_processo),
            "total_zips_gerados": sum(
                p["total_zips"] for p in resumo_por_processo.values()
            ),
            "total_arquivos_internos": sum(
                p["total_arquivos_internos"] for p in resumo_por_processo.values()
            ),
            "total_registros_json": sum(
                p["registros_json_contados"] for p in resumo_por_processo.values()
            ),
            "volume_total_zips_mb": round(
                sum(p["tamanho_total_mb"] for p in resumo_por_processo.values()),
                6,
            ),
            "espaco_disco_consumido_gb": espaco_consumido_gb,
        },
    }

    arquivo_saida_json = pasta_sessao / "dados.json"
    with open(arquivo_saida_json, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=4, ensure_ascii=False)

    salvar_historico_csv(pasta_sessao / "dados.csv", processos_relatorio)

    print("\n" + "=" * 50)
    print("✅ TESTE CONCLUÍDO E SALVO LOCALMENTE!")
    print(f"📊 Pasta da Sessão: '{pasta_sessao.resolve()}'")
    print("=" * 50)

    # Dispara a geração do relatório HTML individual para a pasta criada
    try:
        subprocess.run(
            ["python", "gerar_relatorio.py", str(pasta_sessao)], check=True
        )
        print("📄 Relatório HTML individual gerado com sucesso.")
    except Exception as err:
        print(f"⚠️ [AVISO] Falha ao gerar o relatório individual via gerar_relatorio.py: {err}")

    return pasta_sessao


if __name__ == "__main__":
    import sys

    # Suporte para chamadas diretas via terminal
    banco = sys.argv[1] if len(sys.argv) > 1 else "MSSQL"
    thr = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    ps = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
    filial_cmd = sys.argv[4] if len(sys.argv) > 4 else "D RJ 02"

    executar_orquestrador(
        banco_dados=banco,
        threads=thr,
        page_size=ps,
        filial=filial_cmd,
    )