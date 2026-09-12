# Arquitetura do Framework de Testes de Performance e Benchmark

## 1. Visão Geral
Este framework foi desenvolvido para automatizar a execução de testes de carga, estresse e benchmark comparativo entre diferentes Motores de Bancos de Dados (ex: SQL Server, Oracle). O ecossistema mensura tempo de execução, *throughput* (registros por segundo), comportamento com *multithreading* e métricas de uso de hardware (CPU e Memória).

## 2. Estrutura e Componentes do Projeto

O ecossistema é composto por dois módulos principais de relatórios e scripts de execução de carga:

```
├── historicos/                         # Diretório de armazenamento de execuções passadas
│   └── [data_execucao]/
│       ├── dados.json                  # Telemetria bruta da execução
│       └── relatorio.html              # Relatório gráfico individual
├── templates/
│   ├── template.html                   # Template para execução individual
│   ├── template_consolidado.html       # Template comparativo multi-banco
│   └── template_consolidado_individual.html # Template evolutivo mono-banco
├── gerar_relatorio.py                  # Módulo de processamento individual
└── gerar_relatorio_consolidado.py      # Módulo de consolidação e benchmark
```

---

## 3. Detalhamento dos Módulos

### 3.1. Módulo Individual (`gerar_relatorio.py`)
Responsável por capturar, estruturar e apresentar os dados de uma **única sessão de teste**.

* **Principais Funções:**
  * Captura de logs brutos e conversão para o formato estruturado (`dados.json`).
  * Normalização de consumo de CPU considerando o número de núcleos (*threads*) da máquina.
  * Cálculo de *throughput* em tempo real (`registros / segundo`).
  * Injeção de dados no template `template.html` para criação do `relatorio.html` autônomo.

### 3.2. Módulo Consolidado e Benchmark (`gerar_relatorio_consolidado.py`)
Responsável pela **análise agregada e comparativa** entre diferentes execuções e bancos de dados.

* **Principais Funções:**
  * **Varredura e Mapeamento:** Leitura dinâmica do diretório `historicos/`.
  * **Menu Interativo:** Seleção flexível de execuções via CLI (Todas, Seleção Específica ou Exclusão).
  * **Motor de Benchmark Comparativo:**
    * **Modo Multi-Banco:** Identifica automaticamente a melhor performance entre bancos (ex: MSSQL vs Oracle) em cenários idênticos e calcula a porcentagem de vantagem.
    * **Modo Banco Único:** Consolida métricas acumuladas de tempo, volume total e *throughput* médio.
  * **Categorização de Carga:** Classificação automática da volumetria (Pequeno, Médio, Grande e XGrande - acima de 1 milhão de registros).
  * **Injeção Dinâmica:** Seleção automática do template apropriado (`template_consolidado.html` ou `template_consolidado_individual.html`) e geração do `relatorio_consolidado.html`.

---

## 4. Fluxo de Dados e Execução

1. **Execução do Teste:** O script de carga realiza a operação no banco de dados e gera a telemetria inicial.
2. **Processamento Individual (`gerar_relatorio.py`):**
   * Processa o resultado.
   * Cria a pasta no diretório `historicos/[timestamp]/`.
   * Salva `dados.json` e gera `relatorio.html`.
3. **Consolidação e Benchmark (`gerar_relatorio_consolidado.py`):**
   * O analista executa o script sob demanda.
   * Seleciona os cenários a serem comparados.
   * O script identifica se a análise é comparativa (multi-banco) ou evolutiva (banco único).
   * Gera o arquivo final `relatorio_consolidado.html`.

---

## 5. Fontes das Informações e Dependências

* **Linguagem:** Python 3.x
* **Bibliotecas Padrão:** `os`, `json`, `re`, `shutil`, `datetime`
* **Arquivos de Interface:** Templates HTML com suporte a JavaScript embutido para renderização de gráficos em tempo de execução.
