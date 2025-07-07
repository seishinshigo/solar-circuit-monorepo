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


## 📝 Report Generation and Submission

This project utilizes a standardized reporting mechanism for work orders.

### Creating a New Report

To generate a new report skeleton for a specific Work-Order ID, use the `sc report create` command:

```bash
sc report create WO-YYYYMMDD-XXX
```

Replace `WO-YYYYMMDD-XXX` with the actual Work-Order ID. This command will create a new Markdown file (e.g., `WO-YYYYMMDD-XXX_report.md`) in the `projects/solar_circuit/workorders/reports/` directory, pre-filled with a template.

### Report Template

The report skeleton is generated from the template located at `projects/solar_circuit/templates/report_template.md`. This template provides a structured format for documenting your work.

### Submitting a Report

Once you have completed and filled out your report, it will be automatically picked up by the `Auto-Save Reports` GitHub Action when pushed to the `main` branch. Ensure your report file is located in the `projects/solar_circuit/workorders/reports/` directory.


---
