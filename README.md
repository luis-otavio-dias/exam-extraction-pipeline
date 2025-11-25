# Agente de Extração de Dados de PDFs

Este projeto é um agente baseado em LangGraph projetado para extrair e estruturar dados de documentos PDF. O foco principal é extrair eficientemente questões de múltipla escolha de cadernos de prova (como o ENEM e vestibulares) e seus respectivos gabaritos, salvando o resultado em um formato JSON estruturado. Além disso, o agente é capaz de extrair imagens contidas nos PDFs e salvá-las em formato JPEG.  
Na raiz do projeto, você encontrará o arquivo [`expected_output.json`](expected_output.json), que demonstra o formato esperado do JSON resultante após a extração e estruturação dos dados.

## Funcionalidades

- **Extração de Texto de PDFs**: Processa tanto o PDF da prova quanto o PDF do gabarito para extrair o conteúdo textual completo.
- **Extração de Imagens**: Capaz de extrair e salvar imagens no formato JPEG contidas no PDF da prova.
- **Estruturação de Dados**: Utiliza um modelo de linguagem (`langchain-google-genai`) para analisar o texto extraído e estruturar as questões de múltipla escolha em um formato JSON limpo.
- **Orquestração com LangGraph**: Emprega um grafo para gerenciar o fluxo de trabalho, desde a entrada do usuário até a chamada das ferramentas e a resposta final.

## Tecnologias Utilizadas

- **Langchain**: Para integração com o modelo de linguagem e gerenciamento de prompts.
  - `langchain`
  - `langchain-core`
  - `langchain-google-genai`
- **LangGraph**: Para orquestrar o fluxo de execução do agente.
- **pypdf**: Para extração de imagens de PDFs.
- **fitz (PyMuPDF)**: Para extração de texto de PDFs.

## Estrutura do Projeto

```
.
├── .env-example
├── .gitignore
├── .python-version
├── README.md
├── data/                   # Pasta para armazar pdfs de entrada
│   └── exemplo.pdf
├── pyproject.toml          # Definições do projeto e dependências
├── src/
│   ├── graph.py            # Definição do StateGraph
│   ├── main.py             # Ponto de entrada principal da aplicação
│   ├── prompts.py          # Prompts do sistema e do usuário
│   ├── state.py            # Definição do estado do grafo
│   ├── tools.py            # Ferramentas de extração (texto, imagens, JSON)
│   └── utils.py            # Utilitários (ex: carregar modelo)
└── uv.lock                 # Lockfile do gerenciador de pacotes uv
```

## Instalação

1.  **Clone o repositório**:

    ```bash
    git clone https://github.com/luis-otavio-dias/data-extraction-agent.git
    cd data-extraction-agent
    ```

2.  **Dependências**:

    - **Com UV**  
      O projeto usa uv para gerenciar dependências. Se você utiliza uv, execute no diretório do projeto:

      ```bash
      uv sync
      ```

    - **Alternativa sem UV**

      - Crie e ative um ambiente virtual:

        ```bash
        python -m venv .venv
        source .venv/bin/activate
        # No Windows: .venv\Scripts\activate
        ```

      - Instale as dependências:

        ```bash
        pip install -e .
        ```

3.  **Configure as variáveis de ambiente**:
    Crie um arquivo `.env` copiando o `.env-example` e adicione sua chave de API:

    ```bash
    cp .env-example .env
    ```

    Em seguida, edite o arquivo `.env`:

    ```ini
    AI_MODEL_API_KEY="sua_chave_de_api_aqui"
    ```

## Como Usar

O agente **precisa** receber os caminhos dos arquivos PDF para iniciar o processo de extração e estruturação dos dados, também é necessário indicar onde salvar as imagens extraídas.  
Essas informações estão definidas nos `HUMAN_PROMPTS` localizados em `src/prompts.py` e devem ser ajustadas conforme necessário.

Para executar o agente usando uv, basta rodar o `main.py` indicando seu arquivo `.env`:

```bash
  uv run --env-file=".env" src/main.py
```

O script executará o grafo de forma assíncrona. Ele irá:

1.  Ler os prompts de `src/prompts.py`.
2.  Chamar a ferramenta `extract_exam_pdf_text` para ler os PDFs.
3.  Chamar a ferramenta `pdf_extract_jpegs` para salvar as imagens em `media_images/`.
4.  Chamar a ferramenta `structure_questions` para converter o texto em JSON.
5.  Salvar o JSON estruturado no arquivo `src/final_output.json`.

Você pode monitorar o progresso pelas mensagens impressas no console, que indicam qual ferramenta está sendo invocada.

---
