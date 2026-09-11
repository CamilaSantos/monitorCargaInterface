import sys
import json
from pathlib import Path
from collections import defaultdict


def categorizar_carga(registros):
    if registros < 100000:
        return "PEQUENO"
    elif registros < 500000:
        return "MEDIO"
    elif registros < 1000000:
        return "GRANDE"
    else:
        return "XGRANDE"


def normalizar_cpu(cpu_pct, total_threads=8):
    if not cpu_pct:
        return 0.0
    cpu_calculada = cpu_pct / total_threads if cpu_pct > 100 else cpu_pct
    return round(min(cpu_calculada, 100.0), 2)


def interpretar_indices(entrada, total_itens):
    indices = set()
    if not entrada:
        return indices

    partes = entrada.split(",")
    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            try:
                inicio_str, fim_str = parte.split("-", 1)
                inicio, fim = int(inicio_str), int(fim_str)
                indices.update(range(inicio, fim + 1))
            except ValueError:
                print(f"⚠️ [AVISO] Intervalo inválido ignorado: '{parte}'")
        else:
            try:
                indices.add(int(parte))
            except ValueError:
                print(f"⚠️ [AVISO] Índice inválido ignorado: '{parte}'")

    return {i for i in indices if 1 <= i <= total_itens}


def varrer_pastas_historicos(base_dir):
    pasta_historicos = base_dir / "historicos"
    if not pasta_historicos.exists() or not pasta_historicos.is_dir():
        print(f"⚠️ [AVISO] Pasta {pasta_historicos.name} não foi encontrada.")
        return []

    testes_encontrados = []

    for pasta_sessao in sorted(pasta_historicos.iterdir()):
        if pasta_sessao.is_dir():
            arquivo_json = pasta_sessao / "dados.json"
            if arquivo_json.exists():
                try:
                    with open(arquivo_json, "r", encoding="utf-8") as f:
                        relatorio = json.load(f)

                    totais_resumo = relatorio.get("resumo_geral", {})
                    config_t = relatorio.get("configuracao_teste", {})
                    banco_t = relatorio.get("banco_dados", {})
                    exec_t = relatorio.get("execucao", {})
                    hora_inicio = exec_t.get("hora_inicio", "N/A")

                    caminho_rel_relativo = (
                        str((pasta_sessao / "relatorio.html").relative_to(base_dir).as_posix())
                        if (pasta_sessao / "relatorio.html").exists()
                        else str((pasta_sessao / "relatorio.html").as_posix())
                    )

                    item_estruturado = {
                        "pasta_origem": pasta_sessao.name,
                        "data_execucao": hora_inicio,
                        "banco_dados": banco_t,
                        "configuracao_teste": config_t,
                        "ambiente_hardware": relatorio.get("hardware_maquina", {}),
                        "totais_consolidados": {
                            "hora_inicio": hora_inicio,
                            "hora_fim": exec_t.get("hora_fim"),
                            "duracao_total_segundos": exec_t.get("duracao_total_segundos", 0),
                            "total_registros_json": totais_resumo.get("total_registros_json", 0),
                            "total_zips": totais_resumo.get("total_zips_gerados", 0),
                            "volume_total_zips_mb": totais_resumo.get("volume_total_zips_mb", 0.0),
                            "throughput_reg_sec": totais_resumo.get("throughput_reg_sec", 0.0),
                            "cpu_pico_maximo_pct": relatorio.get("recursos_maquina", {}).get("cpu_max_pct", 0.0),
                            "ram_pico_maxima_mb": relatorio.get("recursos_maquina", {}).get("ram_max_mb", 0.0),
                        },
                        "processos_envolvidos": config_t.get("processos_solicitados", []),
                        "caminho_relatorio_individual": caminho_rel_relativo,
                        "dados_brutos_originais": relatorio
                    }

                    testes_encontrados.append(item_estruturado)
                except Exception as e:
                    print(f"⚠️ Erro ao ler {arquivo_json}: {e}")

    return testes_encontrados


def gerenciar_arquivo_consolidado(caminho_json):
    if not caminho_json.exists():
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        print(f"📄 Arquivo '{caminho_json.name}' não existia e foi criado.")
        return [], set()

    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            dados_existentes = json.load(f)
            if not isinstance(dados_existentes, list):
                dados_existentes = []
    except Exception:
        dados_existentes = []

    chaves_existentes = {
        item.get("pasta_origem") for item in dados_existentes if item.get("pasta_origem")
    }

    return dados_existentes, chaves_existentes


def selecionar_historicos_interativo(testes):
    if not testes:
        print("⚠️ [AVISO] Nenhum teste válido (dados.json) foi encontrado em historicos/.")
        return []

    print("\n" + "=" * 85)
    print("📋 TESTES ENCONTRADOS NAS PASTAS DE HISTÓRICO")
    print("=" * 85)

    for idx, item in enumerate(testes, start=1):
        totais = item.get("totais_consolidados", {})
        config = item.get("configuracao_teste", {})
        banco = item.get("banco_dados", {}).get("tipo", "Desconhecido")
        data_exec = item.get("data_execucao", "Data N/A")
        threads = config.get("threads", 1)
        duracao = totais.get("duracao_total_segundos", 0)
        procs = len(item.get("processos_envolvidos", []))

        print(
            f"[{idx:02d}] Pasta: {item['pasta_origem']:<22} | {data_exec} | Banco: {banco:<8} | "
            f"Procs: {procs:<2} | Threads: {threads:<2} | Duração: {duracao}s"
        )

    print("=" * 85)
    print("ESCOLHA COMO DESEJA MONTAR O RELATÓRIO CONSOLIDADO:")
    print(" [1] TODOS   - Processar todos os testes listados acima")
    print(" [2] SELEÇÃO - Informar números específicos ou intervalos (ex: 1,3,5 ou 1-4)")
    print(" [3] EXCETO  - Processar todos MENOS os informados (ex: 2, 5 ou 2-4)")
    print("=" * 85)

    opcao = input("👉 Escolha a opção (1, 2 ou 3) [padrão: 1]: ").strip() or "1"

    if opcao == "1":
        print("✅ Selecionados TODOS os testes para validação.")
        return testes

    elif opcao == "2":
        entrada = input("👉 Digite os números desejados (ex: 1,3,5 ou 1-4): ").strip()
        indices = interpretar_indices(entrada, len(testes))
        testes_filtrados = [testes[i - 1] for i in indices if 1 <= i <= len(testes)]
        print(f"✅ Total de testes na seleção: {len(testes_filtrados)}")
        return testes_filtrados

    elif opcao == "3":
        entrada = input("👉 Digite os números a EXCLUIR (ex: 2,5 ou 2-4): ").strip()
        indices_excluir = interpretar_indices(entrada, len(testes))
        testes_filtrados = [
            item for idx, item in enumerate(testes, start=1) if idx not in indices_excluir
        ]
        print(f"✅ Total de testes mantidos na seleção: {len(testes_filtrados)}")
        return testes_filtrados

    else:
        print("⚠️ Opção inválida. Selecionando TODOS por padrão.")
        return testes


def processar_comparativos(cenarios_map):
    lista_bruta = []

    for chave, dados_banco in cenarios_map.items():
        mssql = dados_banco.get("MSSQL")
        oracle = dados_banco.get("ORACLE")

        if mssql and oracle:
            tempo_mssql = mssql["duracao"]
            tempo_oracle = oracle["duracao"]

            if tempo_mssql < tempo_oracle:
                vencedor = "MSSQL"
                diferenca_pct = (
                    ((tempo_oracle - tempo_mssql) / tempo_oracle) * 100
                    if tempo_oracle > 0
                    else 0.0
                )
            elif tempo_oracle < tempo_mssql:
                vencedor = "ORACLE"
                diferenca_pct = (
                    ((tempo_mssql - tempo_oracle) / tempo_mssql) * 100
                    if tempo_mssql > 0
                    else 0.0
                )
            else:
                vencedor = "EMPATE"
                diferenca_pct = 0.0

            lista_bruta.append({
                "chave": chave,
                "categoria": mssql["categoria"],
                "modo": mssql["modo"],
                "processos": mssql["processos"],
                "processos_nomes": mssql["processos_nomes"],
                "threads": int(mssql["threads"]),
                "pageSize": int(mssql["page_size"]),
                "registros": mssql["registros"],
                "tempo_mssql": round(tempo_mssql, 2),
                "tempo_oracle": round(tempo_oracle, 2),
                "throughput_mssql": round(mssql["throughput"], 2),
                "throughput_oracle": round(oracle["throughput"], 2),
                "total_zips": mssql["total_zips"],
                "volume_zips_mb": round(mssql["volume_zips_mb"], 2),
                "disco_consumido_mb": round(mssql["volume_zips_mb"] * 1.05, 2),
                "vencedor": vencedor,
                "percentual_melhor": round(diferenca_pct, 2),
                "relatorio_html_mssql": mssql.get("relatorio_html_relativo", "-"),
                "relatorio_html_oracle": oracle.get("relatorio_html_relativo", "-"),
            })

    lista_bruta.sort(key=lambda x: (x["registros"], x["processos"], x["threads"]))

    resultado = []
    percentuais_globais = []
    percentuais_single = []
    percentuais_multi = []
    vitorias = defaultdict(int)

    for idx, item in enumerate(lista_bruta, start=1):
        item["id_cenario"] = idx
        resultado.append(item)

        vitorias[item["vencedor"]] += 1
        if item["vencedor"] == "MSSQL":
            percentuais_globais.append(item["percentual_melhor"])
            if item["modo"] == "SINGLE":
                percentuais_single.append(item["percentual_melhor"])
            else:
                percentuais_multi.append(item["percentual_melhor"])

    banco_vencedor = (
        "Microsoft SQL Server"
        if vitorias["MSSQL"] >= vitorias["ORACLE"]
        else "Oracle Database"
    )

    metricas_resumo = {
        "banco_vencedor": banco_vencedor,
        "global": round(sum(percentuais_globais) / len(percentuais_globais), 2)
        if percentuais_globais
        else 0.0,
        "single": round(sum(percentuais_single) / len(percentuais_single), 2)
        if percentuais_single
        else 0.0,
        "multi": round(sum(percentuais_multi) / len(percentuais_multi), 2)
        if percentuais_multi
        else 0.0,
    }

    return resultado, metricas_resumo


def processar_individual(cenarios_map, banco_chave):
    lista_bruta = []
    tempos_totais = []
    throughputs = []

    for chave, dados_banco in cenarios_map.items():
        info_banco = dados_banco.get(banco_chave)
        if info_banco:
            duracao = info_banco["duracao"]
            tp = info_banco["throughput"]
            tempos_totais.append(duracao)
            throughputs.append(tp)

            lista_bruta.append({
                "chave": chave,
                "categoria": info_banco["categoria"],
                "modo": info_banco["modo"],
                "processos": info_banco["processos"],
                "processos_nomes": info_banco["processos_nomes"],
                "threads": int(info_banco["threads"]),
                "pageSize": int(info_banco["page_size"]),
                "registros": info_banco["registros"],
                "tempo": round(duracao, 2),
                "throughput": round(tp, 2),
                "total_zips": info_banco["total_zips"],
                "volume_zips_mb": round(info_banco["volume_zips_mb"], 2),
                "disco_consumido_mb": round(info_banco["volume_zips_mb"] * 1.05, 2),
                "relatorio_html": info_banco.get("relatorio_html_relativo", "-"),
            })

    lista_bruta.sort(key=lambda x: (x["registros"], x["processos"], x["threads"]))

    resultado = []
    for idx, item in enumerate(lista_bruta, start=1):
        item["id_cenario"] = idx
        resultado.append(item)

    nome_formatado = "Microsoft SQL Server" if banco_chave == "MSSQL" else ("Oracle Database" if banco_chave == "ORACLE" else banco_chave)

    metricas_resumo = {
        "banco_vencedor": nome_formatado,
        "tempo_total_acumulado_s": round(sum(tempos_totais), 2),
        "throughput_medio_reg_sec": round(sum(throughputs) / len(throughputs), 2) if throughputs else 0.0,
    }

    return resultado, metricas_resumo


def atualizar_relatorio_html(base_dir, testes_consolidados):
    caminho_saida = base_dir / "relatorio_consolidado.html"

    bancos_dados = defaultdict(
        lambda: {"qtd_testes": 0, "cpus_pico": [], "rams_pico": []}
    )
    cenarios_map = defaultdict(dict)

    hardware_maquina = {
        "so": "-",
        "cpu": "-",
        "ram": "-",
        "disco_total": "-",
        "disco_livre_inicio": "-",
        "disco_livre_fim": "-",
    }

    total_threads_cpu = 8

    for item in testes_consolidados:
        totais = item.get("totais_consolidados", {})
        config = item.get("configuracao_teste", {})
        banco_info = item.get("banco_dados", {})
        hw_info = item.get("ambiente_hardware", {})

        if "disco_livre_inicio_gb" in hw_info or "disco_livre_inicio_gb" in totais:
            hardware_maquina["disco_livre_inicio"] = hw_info.get(
                "disco_livre_inicio_gb"
            ) or totais.get("disco_livre_inicio_gb", "-")
            hardware_maquina["disco_livre_fim"] = hw_info.get(
                "disco_livre_fim_gb"
            ) or totais.get("disco_livre_fim_gb", "-")

        if "so" in hw_info:
            hardware_maquina["so"] = hw_info["so"]
        if "cpu" in hw_info:
            hardware_maquina["cpu"] = hw_info["cpu"]
        if "ram" in hw_info:
            hardware_maquina["ram"] = hw_info["ram"]
        if "disco_total" in hw_info:
            hardware_maquina["disco_total"] = hw_info["disco_total"]

        tipo_banco_raw = str(banco_info.get("tipo", "Desconhecido")).upper()
        banco_key = (
            "MSSQL"
            if "SQL" in tipo_banco_raw or "MSSQL" in tipo_banco_raw
            else ("ORACLE" if "ORACLE" in tipo_banco_raw else tipo_banco_raw)
        )

        tipo_execucao = item.get("tipo_execucao", "SINGLE").upper()
        processos_envolvidos = item.get("processos_envolvidos", [])

        qtd_processos = len(processos_envolvidos) if processos_envolvidos else 1
        nomes_procs = processos_envolvidos if processos_envolvidos else ["PROCES01"]

        bancos_dados[banco_key]["qtd_testes"] += 1
        bancos_dados[banco_key]["cpus_pico"].append(
            float(totais.get("cpu_pico_maximo_pct", 0.0))
        )
        bancos_dados[banco_key]["rams_pico"].append(
            float(totais.get("ram_pico_maxima_mb", 0.0))
        )

        threads = int(config.get("threads", 1))
        page_size = int(config.get("page_size", 10000))
        regs_totais = int(totais.get("total_registros_json", 0))
        duracao = float(totais.get("duracao_total_segundos", 0.0))

        tp = float(totais.get("throughput_reg_sec", 0.0))
        if tp == 0.0 and duracao > 0:
            tp = regs_totais / duracao

        caminho_relatorio_relativo = item.get("caminho_relatorio_individual", "-")
        chave_cenario = item.get(
            "cenario_id",
            f"PROC{qtd_processos}_T{threads}_P{page_size}_R{regs_totais}",
        )

        cenarios_map[chave_cenario][banco_key] = {
            "titulo": item.get("titulo_bateria", "N/A"),
            "modo": tipo_execucao,
            "processos": qtd_processos,
            "processos_nomes": ", ".join(nomes_procs),
            "threads": threads,
            "page_size": page_size,
            "registros": regs_totais,
            "duracao": duracao,
            "throughput": tp,
            "total_zips": int(totais.get("total_zips", 0)),
            "volume_zips_mb": float(totais.get("volume_total_zips_mb", 0.0)),
            "categoria": categorizar_carga(regs_totais),
            "relatorio_html_relativo": caminho_relatorio_relativo,
        }

    def calc_media(lista):
        return round(sum(lista) / len(lista), 2) if lista else 0.0

    def calc_max_cpu(lista):
        pico_bruto = max(lista) if lista else 0.0
        return normalizar_cpu(pico_bruto, total_threads_cpu)

    bancos_encontrados = list(bancos_dados.keys())

    # Seleção de Template e montagem do Payload
    if len(bancos_encontrados) > 1:
        caminho_template = base_dir / "template_consolidado.html"
        comparativos, metricas_resumo = processar_comparativos(cenarios_map)
        
        payload = {
            "resumo_global": {
                "banco_vencedor": metricas_resumo["banco_vencedor"],
                "vantagem_media_pct": metricas_resumo["global"],
                "vantagem_single_pct": metricas_resumo["single"],
                "vantagem_multi_pct": metricas_resumo["multi"],
            },
            "comparativos": comparativos,
            "hardware": {
                "so": hardware_maquina["so"],
                "cpu": hardware_maquina["cpu"],
                "ram": hardware_maquina["ram"],
                "disco_total": hardware_maquina["disco_total"],
                "disco_livre_inicio": hardware_maquina["disco_livre_inicio"],
                "disco_livre_fim": hardware_maquina["disco_livre_fim"],
                "mssql": {
                    "cpu_pico_max_pct": calc_max_cpu(bancos_dados["MSSQL"]["cpus_pico"]),
                    "ram_media_gb": round(calc_media(bancos_dados["MSSQL"]["rams_pico"]) / 1024, 2),
                },
                "oracle": {
                    "cpu_pico_max_pct": calc_max_cpu(bancos_dados["ORACLE"]["cpus_pico"]),
                    "ram_media_gb": round(calc_media(bancos_dados["ORACLE"]["rams_pico"]) / 1024, 2),
                },
            },
        }
    else:
        caminho_template = base_dir / "template_consolidado_individual.html"
        banco_unico = bancos_encontrados[0] if bancos_encontrados else "MSSQL"
        comparativos, metricas_resumo = processar_individual(cenarios_map, banco_unico)

        payload = {
            "resumo_global": metricas_resumo,
            "comparativos": comparativos,
            "hardware": {
                "so": hardware_maquina["so"],
                "cpu": hardware_maquina["cpu"],
                "ram": hardware_maquina["ram"],
                "disco_total": hardware_maquina["disco_total"],
                "disco_livre_inicio": hardware_maquina["disco_livre_inicio"],
                "disco_livre_fim": hardware_maquina["disco_livre_fim"],
                "banco_unico": {
                    "cpu_pico_max_pct": calc_max_cpu(bancos_dados[banco_unico]["cpus_pico"]),
                    "ram_media_gb": round(calc_media(bancos_dados[banco_unico]["rams_pico"]) / 1024, 2),
                }
            },
        }

    if not caminho_template.exists():
        print(f"❌ [ERRO] Template não encontrado em: {caminho_template}")
        return

    with open(caminho_template, "r", encoding="utf-8") as f:
        html = f.read()

    css_caminho = base_dir / "style.css"
    css_text = css_caminho.read_text(encoding="utf-8") if css_caminho.exists() else ""

    html = html.replace("{{ESTILOS_CSS}}", css_text)
    html = html.replace("{{DADOS_JSON}}", json.dumps(payload, ensure_ascii=False))

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"📊 Relatório HTML gerado/atualizado ({caminho_template.name}): {caminho_saida.name}")


def gerar_relatorio_consolidado():
    base_dir = Path(__file__).resolve().parent
    caminho_json_consolidado = base_dir / "historico_consolidado.json"

    print("\n" + "=" * 85)
    print("⚙️  GERENCIADOR DO HISTÓRICO CONSOLIDADO")
    print("=" * 85)
    print(" [1] ADICIONAR / ATUALIZAR - Manter dados existentes e validar novos")
    print(" [2] RECRIAR TUDO           - Apagar historico_consolidado.json e recriar do zero")
    print("=" * 85)

    acao_inicial = input("👉 Escolha a ação (1 ou 2) [padrão: 1]: ").strip() or "1"

    if acao_inicial == "2":
        if caminho_json_consolidado.exists():
            caminho_json_consolidado.unlink()
            print(f"💥 Arquivo '{caminho_json_consolidado.name}' apagado com sucesso.")
        dados_consolidados, chaves_existentes = gerenciar_arquivo_consolidado(caminho_json_consolidado)
    else:
        dados_consolidados, chaves_existentes = gerenciar_arquivo_consolidado(caminho_json_consolidado)

    todos_testes = varrer_pastas_historicos(base_dir)

    if not todos_testes:
        print("❌ [ERRO] Nenhum arquivo dados.json foi encontrado na pasta historicos/.")
        return

    if len(sys.argv) > 1 and "--todos" in sys.argv:
        testes_selecionados = todos_testes
    else:
        testes_selecionados = selecionar_historicos_interativo(todos_testes)

    if not testes_selecionados:
        print("🚫 [CANCELADO] Nenhum teste foi selecionado.")
        return

    novos_inseridos = 0
    ignorados = 0

    print("\n🔍 Validando registros para inclusão no consolidado...")

    for item in testes_selecionados:
        pasta_origem = item.get("pasta_origem")

        if pasta_origem in chaves_existentes:
            print(f" ⏭️  [IGNORADO] A pasta '{pasta_origem}' já existe em {caminho_json_consolidado.name}.")
            ignorados += 1
        else:
            dados_consolidados.append(item)
            chaves_existentes.add(pasta_origem)
            novos_inseridos += 1
            print(f" ➕ [INSERIDO] A pasta '{pasta_origem}' foi adicionada ao consolidado.")

    with open(caminho_json_consolidado, "w", encoding="utf-8") as f:
        json.dump(dados_consolidados, f, indent=4, ensure_ascii=False)

    print("-" * 85)
    print(f"💾 Arquivo '{caminho_json_consolidado.name}' sincronizado: +{novos_inseridos} inserido(s), {ignorados} ignorado(s). Total no consolidado: {len(dados_consolidados)}.")

    if dados_consolidados:
        atualizar_relatorio_html(base_dir, dados_consolidados)
    else:
        print("⚠️ Nenhum registro acumulado no consolidado para renderizar o HTML.")

    print("=" * 85 + "\n")


if __name__ == "__main__":
    gerar_relatorio_consolidado()