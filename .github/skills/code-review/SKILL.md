---
name: code-review
description: 'Checklist for reviewing research code, focusing on reproducibility, correctness, and data integrity. Use before committing or merging experiment code.'
---

# Code Review Skill (Research)

## Usage

Use this skill when reviewing research code for reproducibility, correctness, and quality. Apply before committing or merging experiment code.

## Checklist

### 1. Reproducibility

- [ ] **Random Seeds**: Are seeds fixed for `torch`, `numpy`, and `random`?
- [ ] **Config**: Are all hyperparameters in a config file (not hardcoded)?
- [ ] **Environment**: Is `pyproject.toml` or `requirements.txt` up to date?
- [ ] **Git Hash**: Is the commit hash logged with results?

```python
# Example: Setting seeds for reproducibility
import random
import numpy as np
import torch

def set_seed(seed: int = 42) -> None:
    """Set seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
```

### 2. Data Integrity

- [ ] **Leakage**: Is there any overlap between Train and Test sets?
- [ ] **Preprocessing**: Is the exact same preprocessing applied to Train/Val/Test?
- [ ] **Splits**: Are splits deterministic (seeded)?
- [ ] **Normalization**: Are normalization stats computed only from training data?

### 3. Logic & Correctness

- [ ] **Metrics**: Is the metric calculation standard and correct?
- [ ] **Gradient**: Is `optimizer.zero_grad()` called correctly?
- [ ] **Evaluation**: Is the model in `.eval()` mode during validation?
- [ ] **Device**: Is `to(device)` applied to both model and data?
- [ ] **Gradient Accumulation**: Is loss scaled correctly if using gradient accumulation?

### 4. Efficiency

- [ ] **Dataloader**: Is `num_workers` > 0?
- [ ] **Pin Memory**: Is `pin_memory=True` for GPU training?
- [ ] **Logging**: Is logging frequency appropriate (not too frequent)?
- [ ] **Checkpointing**: Are checkpoints saved periodically?

### 5. Type Safety

- [ ] **Type Hints**: Are all functions properly typed?
- [ ] **Assertions**: Are critical assumptions validated?

## Transparency & Thinking

```
🧠 THINKING:
- **File Under Review**: [Path]
- **Issues Found**: [List of issues]
- **Severity**: [Critical/Warning/Info]
- **Recommendation**: [How to fix?]
```
