# Martial Arts Teaching Agent (武术教学智能体)

An AI-powered martial arts teaching assistant that combines Large Language Models (LLM) with domain-specific knowledge (RAG).
This project corresponds to the research: *"Generative AI in Traditional Martial Arts Teaching: Development and Effectiveness Evaluation"*.

## Features

- **Domain Knowledge Integration (RAG)**: Retrieves accurate martial arts theory from books/Excel files.
- **Local LLM Support**: Runs completely offline using Ollama (Qwen2.5) for privacy and cost-efficiency.
- **Multi-modal Interaction**: Supports text Q&A and basic motion analysis concepts.
- **Web Interface**: User-friendly Streamlit UI.

## Getting Started

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com) installed

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/YOUR_USERNAME/martial-arts-agent.git
    cd martial-arts-agent
    ```

2.  Install dependences:
    ```bash
    pip install -r requirements.txt
    ```

3.  Download AI Models (Free):
    ```bash
    ollama pull qwen2.5:1.5b
    ollama pull nomic-embed-text
    ```

### Usage

**CLI Mode:**
```bash
python src/main.py
```

**Web Interface:**
```bash
streamlit run src/interface/app.py
```

## Structure

- `src/`: Source code for agent and RAG logic.
- `data/knowledge_base/`: Place your martial arts documents here (txt, xlsx).

## License

MIT
