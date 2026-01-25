---
name: data-analysis
description: 'Protocol for analyzing experiment results, visualizing metrics, and deriving insights from JSON result files. Use for plotting and comparison tasks.'
---

# Data Analysis Skill

## Usage

Use this skill when analyzing experiment results, creating plots, or comparing metrics across runs.

## Protocol

### 1. Data Loading

- **Source**: Load JSON files from `results/<experiment>/`.
- **Tool**: Use `pandas` to aggregate multiple result files into a DataFrame.

```python
import pandas as pd
import json
from pathlib import Path

def load_results(experiment_dir: str) -> pd.DataFrame:
    """Load all result JSON files from an experiment directory."""
    results = []
    for path in Path(experiment_dir).glob("*.json"):
        with open(path) as f:
            results.append(json.load(f))
    return pd.DataFrame(results)
```

### 2. Visualization

- **Library**: Use `matplotlib` or `seaborn`.
- **Style**: Ensure graphs are legible (labels, legends, titles).
- **Output**: Save figures to `documents/final/figures/` or `results/<experiment>/plots/`.
- **Korean Font**: If using Korean labels, ensure font compatibility.

```python
import matplotlib.pyplot as plt

def plot_metrics(df: pd.DataFrame, metric: str, save_path: str) -> None:
    """Plot a metric across experiments."""
    plt.figure(figsize=(10, 6))
    plt.plot(df["experiment_name"], df[metric], marker="o")
    plt.xlabel("Experiment")
    plt.ylabel(metric)
    plt.title(f"{metric} Comparison")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
```

### 3. Comparison

- **Baseline**: Always compare against a baseline (e.g., "Previous Best" or "Vanilla").
- **Metrics**: Focus on key metrics (Loss, Accuracy, F1) but also consider efficiency (Time, Memory).

### 4. Reporting

- Summarize findings in an **Experiment Note** or **Final Report**.
- Include the generated plots.
- Use tables for numeric comparisons.

## Transparency & Thinking

```
🧠 THINKING:
- **Data Source**: [Which result files?]
- **Metrics**: [Which metrics to analyze?]
- **Baseline**: [What is the comparison baseline?]
- **Output**: [Where to save plots/reports?]
```
