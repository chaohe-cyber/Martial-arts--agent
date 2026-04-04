# Martial Arts Teaching Agent

[中文说明](README.md) | [English](README_EN.md)

A retrieval-enhanced teaching assistant for traditional martial arts education.

## Highlights

- Domain knowledge retrieval over txt/xlsx teaching materials
- Local model support with Ollama
- CLI and Web entry points for classroom and demo use
- Extensible structure for evaluation and motion-analysis modules

## Getting Started

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Pull Local Models

```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

### Run CLI

```bash
./scripts/run_cli.sh
```

### Run Web UI

```bash
./scripts/run_web.sh
```

### Health Check

```bash
./scripts/health_check.sh
```

## Repository Structure

- src: core logic
- data/knowledge_base: source teaching materials
- docs: project documentation
- scripts: utility scripts
- tests: test placeholders

## Open Source Workflow

- Contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Large file strategy: [docs/LARGE_FILES.md](docs/LARGE_FILES.md)
- GitHub release steps: [docs/GITHUB_RELEASE_GUIDE.md](docs/GITHUB_RELEASE_GUIDE.md)
- Issue templates: [.github/ISSUE_TEMPLATE](.github/ISSUE_TEMPLATE)
- PR template: [.github/pull_request_template.md](.github/pull_request_template.md)

## License

MIT License. See [LICENSE](LICENSE).
