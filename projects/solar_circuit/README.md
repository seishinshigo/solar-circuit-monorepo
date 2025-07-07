# Solar Circuit System

This repository contains the core components for the **Solar Circuit** project, including:

- 🎛️ `solar_circuit/cli.py`: Lightweight command-line interface using [Typer](https://typer.tiangolo.com/)
- 🧠 `orchestrator/`: Execution logic for task automation and agent coordination
- 🧪 `tests/`: Full pytest test suite with coverage support

## 🧪 Testing

```bash
pytest --cov=projects/solar_circuit
````

## 📦 Installation (Editable mode)

```bash
pip install -e projects/solar_circuit
```

## 🧾 Development Dependencies

Install from:

```bash
pip install -r projects/solar_circuit/requirements-dev.txt
```

## 📁 Workflows

GitHub Actions are configured for this project:

- **CI (`ci.yml`):** Runs `pytest` with coverage on every push and pull request to the `main` branch for paths under `projects/solar_circuit/`.
- **Auto-Save Reports (`report-autosave.yml`):** Automatically generates a new report file whenever a new work order (e.g., `WO-20250708-001.json`) is added to the `projects/solar_circuit/workorders/incoming/` directory. This ensures that every work order has a corresponding report file ready for edits.


---
