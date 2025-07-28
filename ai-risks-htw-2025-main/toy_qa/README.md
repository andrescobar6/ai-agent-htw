# Setup & Run Instructions

## 1. Setup Instructions

1. Navigate to the `toy_qa` directory where the agent code and requirements file are located.
2. Environment variables (.env)
3. Create a `.env` file in the `toy_qa` directory with the following variables (you can copy from the root `.env.example` file):

```
OPENAI_API_KEY=sk-your_openai_api_key_here
TAVILY_API_KEY=tvly-your_tavily_api_key_here
```

3. Install the package manager **uv** (choose based on your OS)

*MacOS & Linux*:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
*Windows* (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
## 4. Install dependencies & run the agent

**Note:** Make sure you're in the `toy_qa` directory when running these commands.

### Basic usage:
```bash
uv run --with-requirements requirements.txt --python 3.13 \
   python agent.py --document_path "./your_document.pdf" --question "Your question here"
```

### Advanced usage with search modes:
```bash
# Search both document and online (default)
uv run --with-requirements requirements.txt --python 3.13 \
   python agent.py --document_path "./your_document.pdf" --question "Your question here" --search_mode "both"

# Search only in the document
uv run --with-requirements requirements.txt --python 3.13 \
   python agent.py --document_path "./your_document.pdf" --question "Your question here" --search_mode "doc"

# Search only online (document file is not read)
uv run --with-requirements requirements.txt --python 3.13 \
   python agent.py --document_path "./your_document.pdf" --question "Your question here" --search_mode "online"
```

### Supported Document Types:
- **PDF files** (.pdf): Full text extraction with page numbers
- **Markdown files** (.md, .markdown): Raw markdown content
- **Text files** (.txt): Plain text content

### Examples with different document types:
```bash
# PDF document
uv run --with-requirements requirements.txt --python 3.13 python agent.py --document_path "research_paper.pdf" --question "What are the main findings?"

# Markdown document
uv run --with-requirements requirements.txt --python 3.13 python agent.py --document_path "README.md" --question "What is this project about?"

# Text document
uv run --with-requirements requirements.txt --python 3.13 python agent.py --document_path "notes.txt" --question "What are the key points?"
```

### Search Modes:
- `doc`: Only search within the provided document content
- `online`: Only search online (document file is not read)
- `both`: Search both document and online sources (default behavior)

Replace the document path and the question with your own values. The script will:
1. Load environment variables
2. Extract text from the document (unless online_only mode)
3. Invoke the agent to answer the question based on the specified search mode
4. Save a full execution trace to `agent_eval_trace.json` and print the structured answer.