
# agent.py

# good to have

# ALWAYS used
import json
from pathlib import Path
from dotenv import load_dotenv
from any_agent import AgentConfig, AnyAgent, AgentRunError
from pydantic import BaseModel, Field
from fire import Fire

# ADD BELOW HERE: tools made available by any-agent or agent-factory
from any_agent.tools import search_tavily, visit_webpage

# Document reading functionality
import PyPDF2
import os

load_dotenv()

# ========== Structured output definition ==========
# ========= Structured output definition =========
class StructuredOutput(BaseModel):
    answer: str = Field(..., description="Answer to the user's question with inline citations such as (PDF p 4) or [1].")
    sources: list[str] = Field(..., description="List of sources used in the answer – PDF page references and/or URLs.")

# ========== System (Multi-step) Instructions ===========
INSTRUCTIONS='''
You are a research assistant that answers user questions using the text of a user-supplied document (PDF, Markdown, or text) and, when necessary, additional online information. Follow this workflow based on the search mode specified:

SEARCH MODES:
- "doc": Only search within the provided document content
- "online": Only search online (ignore document content)
- "both": Search both document and online sources (default behavior)

WORKFLOW:

Step 1 – Understand the task and search mode
• Read the user's question and the specified search mode
• If search_mode is "doc": Only use document content
• If search_mode is "online": Only use web search tools
• If search_mode is "both": Use both document and web search

Step 2 – Document Search (if applicable)
• If search_mode is "doc" or "both": Scan the document text for relevant sections
• For PDFs: Capture exact sentence(s) and their page numbers (cite as "PDF page X")
• For Markdown/Text: Capture exact sentence(s) and cite as "Document section"

Step 3 – Web Search (if applicable)
• If search_mode is "online" or "both": Formulate a focused search query and call `search_tavily`
• Review returned results; for any promising URL, call `visit_webpage` to inspect the content
• Record the URLs actually used

Step 4 – Compose the answer
• Write a concise, fact-based answer (≤300 words)
• Include inline citations: use "(PDF p X)" for PDF sources, "(Document section)" for Markdown/Text, and numbered brackets like "[1]" for web URLs
• Only include information from sources you have actually accessed

Step 5 – Structured output
Return a JSON object that matches the provided `StructuredOutput` schema:
{
  answer: <answer_with_inline_citations>,
  sources: ["PDF page 3", "Document section", "https://example.com/...", …]
}
Always include at least one source. List only the sources you actually used based on the search mode.
'''

# ========== Tools definition ===========
# ========= Tools definition =========
TOOLS = [
    search_tavily,   # Web search when external information is required
    visit_webpage,   # Retrieve and inspect any promising webpages found via search
]

 

# ========== Running the agent via CLI ===========
agent = AnyAgent.create(
    "openai",
    AgentConfig(
        model_id="ollama/granite3.3",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
        output_type=StructuredOutput,
        model_args={"tool_choice": "required"},
    ),
)

def read_document(file_path: str) -> str:
    """Read document content based on file extension.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Document content as string
        
    Raises:
        ValueError: If file type is not supported or file cannot be read
    """
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        # Read PDF content
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = ""
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    content += f"--- Page {page_num} ---\n{page_text}\n\n"
                return content
        except Exception as e:
            raise ValueError(f"Failed to read PDF file '{file_path}': {str(e)}")
    
    elif file_extension in ['.md', '.markdown']:
        # Read Markdown content
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return f"--- Markdown Document ---\n{content}\n"
        except Exception as e:
            raise ValueError(f"Failed to read Markdown file '{file_path}': {str(e)}")
    
    elif file_extension == '.txt':
        # Read plain text content
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return f"--- Text Document ---\n{content}\n"
        except Exception as e:
            raise ValueError(f"Failed to read text file '{file_path}': {str(e)}")
    
    else:
        raise ValueError(f"Unsupported file type: {file_extension}. Supported types: .pdf, .md, .markdown, .txt")

def main(document_path: str, question: str, search_mode: str = "both"):
    """Answer questions based on an uploaded document (PDF, Markdown, or text), optionally augmenting with web search, and return the answer with proper source citations.
    
    Args:
        document_path: Path to the document file to analyze (PDF, .md, or .txt)
        question: The question to answer
        search_mode: Search mode - "doc", "online", or "both" (default: "both")
    """
    
    # Read document content (only if not online mode)
    document_text = ""
    if search_mode != "online":
        document_text = read_document(document_path)
    
    # Build input prompt based on search mode
    if search_mode == "online":
        input_prompt = f"You are asked to answer a question using only online search.\n\nSearch mode: {search_mode}\n\nQuestion: {question}\n\nFollow the system instructions to produce your answer based on the specified search mode."
    else:
        input_prompt = f"You are provided with the full text of a document and a question.\n\nSearch mode: {search_mode}\n\nDocument content (delimited by triple backticks):\n```document\n{document_text}\n```\n\nQuestion: {question}\n\nFollow the system instructions to produce your answer based on the specified search mode."
    try:
        agent_trace = agent.run(prompt=input_prompt, max_turns=20)
    except AgentRunError as e:
        agent_trace = e.trace
        print(f"Agent execution failed: {str(e)}")
        print("Retrieved partial agent trace...")

    # Extract cost information (with error handling)
    try:
        cost_info = agent_trace.cost
        if cost_info.total_cost > 0:
            cost_msg = (
                f"input_cost=${cost_info.input_cost:.6f} + "
                f"output_cost=${cost_info.output_cost:.6f} = "
                f"${cost_info.total_cost:.6f}"
            )
    except Exception:
        class DefaultCost:
            input_cost = 0.0
            output_cost = 0.0
            total_cost = 0.0
        cost_info = DefaultCost()

    # Create enriched trace data with costs as separate metadata
    script_dir = Path(__file__).resolve().parent
    output_path = script_dir / "agent_eval_trace.json"

    # Prepare the trace data with costs
    trace_data = agent_trace.model_dump()
    trace_data["execution_costs"] = {
        "input_cost": cost_info.input_cost,
        "output_cost": cost_info.output_cost,
        "total_cost": cost_info.total_cost
    }

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, indent=2))

    return agent_trace.final_output

if __name__ == "__main__":
    Fire(main)

