import re
import oracledb
import pyodbc

# Dicionário de conexões padrão configurável por ambiente/SGBD
CONFIGS_BANCO_PADRAO = {
    "MSSQL": {
        "tipo": "MSSQL",
        "host": "localhost",
        "porta": "1433",
        "database": "PROTHEUS",
        "usuario": "sa",
        "senha": "******",
    },
    "ORACLE": {
        "tipo": "ORACLE",
        "host": "localhost",
        "porta": "1521",
        "database": "ORCL",
        "usuario": "system",
        "senha": "******",
    },
}

MAPA_QUERIES_PROCESSOS = {
    "PRODUTO": (
        "SELECT COUNT(*) FROM SB1T10 WHERE D_E_L_E_T_ = ' ' AND B1_FILIAL = '{filial}'"
    ),
    "CLIENTE": (
        "SELECT COUNT(*) FROM SA1T10 WHERE D_E_L_E_T_ = ' ' AND A1_FILIAL = '{filial_2dig}'"
    ),
    "ADMINISTRADORA": (
        "SELECT COUNT(*) FROM SAET10 WHERE D_E_L_E_T_ = ' ' AND AE_FILIAL = '{filial_2dig}'"
    ),
    "PRECO": (
        "SELECT COUNT(*) FROM DA1T10 WHERE D_E_L_E_T_ = ' ' AND DA1_FILIAL = '{filial_2dig}'"
    ),
    "SALDO ESTOQUE": (
        "SELECT COUNT(*) FROM SB2T10 WHERE D_E_L_E_T_ = ' ' AND B2_FILIAL = '{filial}'"
    ),
    "CADASTRO LOJA": (
        "SELECT COUNT(*) FROM MIHT10 WHERE D_E_L_E_T_ = ' ' AND MIH_TIPCAD = 'CADASTRO DE LOJA'"
    ),
    "COMPARTILHAMENT": (
        "SELECT COUNT(*) FROM MIHT10 WHERE D_E_L_E_T_ = ' ' AND MIH_TIPCAD = 'COMPARTILHAMENTOS'"
    ),
    "COMPARTILHAMENTOS": (
        "SELECT COUNT(*) FROM MIHT10 WHERE D_E_L_E_T_ = ' ' AND MIH_TIPCAD = 'COMPARTILHAMENTOS'"
    ),
    "NCM": (
        "SELECT COUNT(*) FROM CLKT10 WHERE D_E_L_E_T_ = ' ' AND CLK_CODNCM <> ' '"
    ),
    "FORMA PAGAMENTO": (
        "SELECT COUNT(*) FROM MIHT10 WHERE D_E_L_E_T_ = ' ' AND MIH_TIPCAD LIKE 'FORMA DE PAGAMENTO%'"
    ),
}


def criar_conexao_mssql(host, porta, db, user, pwd):
    """
    Tenta conectar via ODBC Server testando os drivers comuns disponíveis.
    """
    drivers = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server"
    ]
    
    ultimo_erro = None
    for driver in drivers:
        try:
            str_conn = (
                f"DRIVER={{{driver}}};"
                f"SERVER={host},{porta};DATABASE={db};UID={user};PWD={pwd};"
                f"TrustServerCertificate=yes;"
            )
            return pyodbc.connect(str_conn, timeout=10)
        except Exception as e:
            ultimo_erro = e
            
    raise RuntimeError(f"Falha ao conectar no MSSQL com os drivers testados: {ultimo_erro}")


def consultar_totais_por_processos(banco_dados, processos_solicitados, filial_informada, config_banco_custom=None):
    """
    Executa dinamicamente as consultas no banco (MSSQL ou ORACLE)
    e retorna tanto os totais por processo quanto os metadados da conexão.
    """
    resultados_processos = {}
    filial_clean = str(filial_informada).strip()
    
    # Extrai formato reduzido da filial se houver sufixos numéricos (ex: '0101' -> '01')
    filial_2dig = re.sub(r"\s+\d{2}$", "", filial_clean)
    if len(filial_clean) >= 2 and not filial_2dig:
        filial_2dig = filial_clean[:2]

    tipo_banco = str(banco_dados).strip().upper()
    
    if config_banco_custom:
        cfg = config_banco_custom
    else:
        cfg = CONFIGS_BANCO_PADRAO.get(tipo_banco, CONFIGS_BANCO_PADRAO["MSSQL"])

    host = cfg.get("host", "localhost")
    porta = str(cfg.get("porta") or ("1433" if tipo_banco == "MSSQL" else "1521"))
    db = cfg.get("database", "")
    user = cfg.get("usuario", "")
    pwd = cfg.get("senha", "")

    metadados_banco = {
        "tipo": tipo_banco,
        "host": host,
        "porta": porta,
        "database": db,
        "filial_consultada": filial_clean
    }

    print(f"\n🔌 [BANCO DE DADOS] Conectando ao {tipo_banco} -> Host: {host}:{porta} | DB: {db}...")

    conn = None
    cursor = None

    try:
        if tipo_banco == "MSSQL":
            conn = criar_conexao_mssql(host, porta, db, user, pwd)
        else:
            conn = oracledb.connect(
                user=user,
                password=pwd,
                host=host,
                port=int(porta),
                service_name=db,
            )

        print("✅ [BANCO DE DADOS] Conexão estabelecida com sucesso!")
        cursor = conn.cursor()

        for proc in processos_solicitados:
            proc_key = proc.strip().upper()
            template_query = MAPA_QUERIES_PROCESSOS.get(proc_key)

            if template_query:
                query_final = template_query.format(
                    filial=filial_clean,
                    filial_2dig=filial_2dig
                )
                try:
                    cursor.execute(query_final)
                    row = cursor.fetchone()
                    total = row[0] if row else 0
                    resultados_processos[proc_key] = total
                    print(f"   ↳ Processo '{proc_key}': {total} registros em banco.")
                except Exception as err_q:
                    print(f"   ❌ Erro ao executar query ('{proc_key}'): {err_q}")
                    resultados_processos[proc_key] = f"Erro Query: {err_q}"
            else:
                print(f"   ⚠️ Processo '{proc_key}' não possui query no dicionário.")
                resultados_processos[proc_key] = "Processo Não Mapeado"

    except Exception as err_conn:
        print(f"⚠️ [DB ERRO] Falha ao conectar no banco de dados: {err_conn}")
        for proc in processos_solicitados:
            resultados_processos[proc.strip().upper()] = f"Erro Conexão Banco: {err_conn}"

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    return {
        "metadados": metadados_banco,
        "resultados": resultados_processos
    }