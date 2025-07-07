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

GitHub Actions use `.github/workflows/ci.yml`
Auto-reporting configured via `report-autosave.yml`

````

---
