# Universal Handoff Protocol

## Overview

The Handoff Protocol defines a standardized JSON format for inter-agent communication within the orchestrated multi-agent system. It ensures consistent, structured information transfer between agents with clear context, results, and actionable next steps.

## Purpose

- **Consistency**: All agent handoffs follow the same structure
- **Traceability**: Chain of custody is maintained through conversation IDs
- **Actionability**: Recipients receive clear instructions and context
- **Failure Handling**: Partial and blocked states are explicitly defined

---

## JSON Schema Specification

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentHandoff",
  "type": "object",
  "required": ["handoff_id", "from_agent", "to_agent", "status", "timestamp"],
  "properties": {
    "handoff_id": {
      "type": "string",
      "description": "Unique identifier for this handoff (UUID v4)"
    },
    "conversation_id": {
      "type": "string",
      "description": "Parent conversation/task chain ID for traceability"
    },
    "from_agent": {
      "type": "string",
      "description": "Name of the source agent"
    },
    "to_agent": {
      "type": "string",
      "description": "Name of the target agent"
    },
    "status": {
      "type": "string",
      "enum": ["success", "partial", "blocked", "error"],
      "description": "Completion status of the source agent's task"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of handoff creation"
    },
    "context": {
      "type": "object",
      "description": "Information the receiving agent needs",
      "properties": {
        "objective": {
          "type": "string",
          "description": "Original task objective"
        },
        "scope": {
          "type": "object",
          "properties": {
            "in_scope": { "type": "array", "items": { "type": "string" } },
            "out_of_scope": { "type": "array", "items": { "type": "string" } }
          }
        },
        "constraints": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Constraints the receiving agent must respect"
        },
        "prior_decisions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "decision": { "type": "string" },
              "rationale": { "type": "string" },
              "alternatives_considered": { "type": "array", "items": { "type": "string" } }
            }
          }
        }
      }
    },
    "results": {
      "type": "object",
      "description": "Output from the source agent",
      "properties": {
        "summary": {
          "type": "string",
          "description": "Brief summary of what was accomplished"
        },
        "artifacts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "path": { "type": "string" },
              "type": { "type": "string", "enum": ["code", "document", "config", "data", "report"] },
              "description": { "type": "string" }
            },
            "required": ["name", "path", "type"]
          }
        },
        "metrics": {
          "type": "object",
          "additionalProperties": true,
          "description": "Quantitative results (test coverage, lines of code, etc.)"
        },
        "verification": {
          "type": "object",
          "properties": {
            "tests_passed": { "type": "boolean" },
            "coverage": { "type": "number" },
            "execution_verified": { "type": "boolean" },
            "verification_method": { "type": "string" }
          }
        }
      }
    },
    "action_required": {
      "type": "object",
      "description": "What the receiving agent should do",
      "properties": {
        "task": {
          "type": "string",
          "description": "Primary task for the receiving agent"
        },
        "instructions": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Ordered list of instructions"
        },
        "expected_output": {
          "type": "string",
          "description": "What the receiving agent should produce"
        },
        "priority": {
          "type": "string",
          "enum": ["critical", "high", "medium", "low"]
        },
        "deadline": {
          "type": "string",
          "description": "Optional deadline or urgency indicator"
        }
      },
      "required": ["task"]
    },
    "blockers": {
      "type": "array",
      "description": "Issues preventing completion (only for partial/blocked status)",
      "items": {
        "type": "object",
        "properties": {
          "blocker_id": { "type": "string" },
          "type": { 
            "type": "string", 
            "enum": ["missing_input", "resource_unavailable", "dependency_failed", "validation_failed", "unknown"]
          },
          "description": { "type": "string" },
          "resolution_options": {
            "type": "array",
            "items": { "type": "string" }
          },
          "blocking_tasks": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Which downstream tasks are blocked"
          }
        },
        "required": ["type", "description"]
      }
    },
    "metadata": {
      "type": "object",
      "description": "Additional tracking information",
      "properties": {
        "execution_time_ms": { "type": "integer" },
        "tokens_used": { "type": "integer" },
        "tool_calls": { "type": "integer" },
        "memory_refs": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Memory MCP content hashes referenced"
        },
        "retry_count": { "type": "integer" },
        "chain_position": {
          "type": "object",
          "properties": {
            "step": { "type": "integer" },
            "total_steps": { "type": "integer" }
          }
        }
      }
    }
  }
}
```

---

## Field Descriptions

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `handoff_id` | string | UUID v4 identifying this specific handoff |
| `from_agent` | string | Source agent name (e.g., `code-generator`) |
| `to_agent` | string | Target agent name (e.g., `code-quality-reviewer`) |
| `status` | enum | One of: `success`, `partial`, `blocked`, `error` |
| `timestamp` | ISO 8601 | When the handoff was created |

### Status Definitions

| Status | Meaning | Required Fields |
|--------|---------|-----------------|
| `success` | Task completed fully | `results` with artifacts |
| `partial` | Task partially completed | `results` + `blockers` |
| `blocked` | Cannot proceed | `blockers` with resolution options |
| `error` | Unexpected failure | `blockers` with error details |

### Context Object

Provides background information the receiving agent needs:

- **objective**: The original goal being pursued
- **scope**: What is in/out of scope for the overall task
- **constraints**: Limitations the agent must respect
- **prior_decisions**: Decisions made earlier in the chain (with rationale)

### Results Object

Contains the source agent's output:

- **summary**: Human-readable summary of accomplishments
- **artifacts**: Files/documents produced (with paths and types)
- **metrics**: Quantitative measurements (coverage, LOC, etc.)
- **verification**: Whether output was verified and how

### Action Required Object

Tells the receiving agent what to do:

- **task**: Primary task description
- **instructions**: Ordered list of specific instructions
- **expected_output**: What should be produced
- **priority**: Urgency level (critical/high/medium/low)

---

## Usage Guidelines

### 1. Creating a Handoff

```python
# Agent creating handoff after completing work
handoff = {
    "handoff_id": str(uuid.uuid4()),
    "conversation_id": current_conversation_id,
    "from_agent": "code-generator",
    "to_agent": "code-quality-reviewer",
    "status": "success",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "context": {
        "objective": "Implement user authentication module",
        "constraints": ["Python 3.8+", "No external auth services"]
    },
    "results": {
        "summary": "Generated auth module with JWT support",
        "artifacts": [
            {"name": "auth.py", "path": "src/auth/auth.py", "type": "code"},
            {"name": "test_auth.py", "path": "tests/test_auth.py", "type": "code"}
        ],
        "metrics": {"test_coverage": 0.95, "lines_of_code": 245},
        "verification": {"tests_passed": True, "coverage": 0.95}
    },
    "action_required": {
        "task": "Review generated code for quality issues",
        "priority": "high"
    }
}
```

### 2. Receiving a Handoff

Receiving agents should:

1. **Validate** the handoff structure
2. **Check status** - handle `blocked`/`partial` appropriately
3. **Read context** - understand constraints and prior decisions
4. **Review results** - verify artifacts exist
5. **Execute action_required** - perform the requested task
6. **Create new handoff** - pass results to next agent

### 3. Handling Blockers

When receiving a `partial` or `blocked` handoff:

```python
if handoff["status"] in ["partial", "blocked"]:
    for blocker in handoff["blockers"]:
        if blocker["type"] == "missing_input":
            # Attempt to resolve or escalate
            resolution = attempt_resolution(blocker)
        elif blocker["type"] == "dependency_failed":
            # Check if we can proceed without dependency
            proceed = can_proceed_without(blocker)
```

---

## Integration Points

### Memory MCP Integration

Handoffs should be stored in Memory MCP for traceability:

```python
# Store handoff in memory
store_memory(
    content=json.dumps(handoff),
    metadata={
        "tags": ["handoff", handoff["from_agent"], handoff["to_agent"]],
        "memory_type": "handoff",
        "conversation_id": handoff["conversation_id"]
    }
)
```

### Retrieving Handoff History

```python
# Find all handoffs in a conversation
retrieve_memory(
    query=f"handoff conversation {conversation_id}",
    tags=["handoff"]
)
```

---

## Examples

### Example 1: Success Handoff

```json
{
  "handoff_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "conversation_id": "conv-2026-01-15-001",
  "from_agent": "code-generator",
  "to_agent": "code-quality-reviewer",
  "status": "success",
  "timestamp": "2026-01-15T10:30:00Z",
  "context": {
    "objective": "Implement data preprocessing pipeline",
    "scope": {
      "in_scope": ["CSV parsing", "Data validation", "Normalization"],
      "out_of_scope": ["Database storage", "API endpoints"]
    },
    "constraints": ["Memory < 8GB", "Process 10K rows/sec"]
  },
  "results": {
    "summary": "Complete preprocessing pipeline with validation and normalization",
    "artifacts": [
      {
        "name": "preprocessor.py",
        "path": "src/data/preprocessor.py",
        "type": "code",
        "description": "Main preprocessing module"
      },
      {
        "name": "test_preprocessor.py",
        "path": "tests/test_preprocessor.py",
        "type": "code",
        "description": "Unit tests with 98% coverage"
      }
    ],
    "metrics": {
      "test_coverage": 0.98,
      "lines_of_code": 320,
      "throughput": "12K rows/sec"
    },
    "verification": {
      "tests_passed": true,
      "coverage": 0.98,
      "execution_verified": true,
      "verification_method": "pytest with benchmark"
    }
  },
  "action_required": {
    "task": "Review code for Tier 1/2 quality issues",
    "instructions": [
      "Check for concurrency issues in batch processing",
      "Verify memory usage stays under 8GB",
      "Review error handling completeness"
    ],
    "expected_output": "Quality report with pass/fail decision",
    "priority": "high"
  },
  "metadata": {
    "execution_time_ms": 45000,
    "tool_calls": 12,
    "chain_position": {"step": 2, "total_steps": 4}
  }
}
```

### Example 2: Partial Completion

```json
{
  "handoff_id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "conversation_id": "conv-2026-01-15-002",
  "from_agent": "deep-research",
  "to_agent": "planner",
  "status": "partial",
  "timestamp": "2026-01-15T11:45:00Z",
  "context": {
    "objective": "Research distributed training frameworks",
    "constraints": ["Must support PyTorch", "Budget < $10K/month"]
  },
  "results": {
    "summary": "Completed framework comparison, blocked on pricing verification",
    "artifacts": [
      {
        "name": "framework_comparison.md",
        "path": "documents/reference/technical/framework_comparison.md",
        "type": "document"
      }
    ],
    "metrics": {
      "frameworks_analyzed": 5,
      "sources_consulted": 23
    }
  },
  "blockers": [
    {
      "blocker_id": "blk-001",
      "type": "missing_input",
      "description": "Unable to verify Ray pricing for enterprise tier",
      "resolution_options": [
        "Contact Ray sales for quote",
        "Use published pricing as estimate",
        "Exclude Ray from consideration"
      ],
      "blocking_tasks": ["final_recommendation", "budget_allocation"]
    }
  ],
  "action_required": {
    "task": "Create implementation plan with available information",
    "instructions": [
      "Use framework comparison as input",
      "Mark Ray pricing as [NEEDS VERIFICATION]",
      "Provide alternatives if Ray is chosen"
    ],
    "expected_output": "Implementation plan with contingencies",
    "priority": "medium"
  }
}
```

### Example 3: Blocked Handoff

```json
{
  "handoff_id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
  "conversation_id": "conv-2026-01-15-003",
  "from_agent": "slurm-manager",
  "to_agent": "orchestrator",
  "status": "blocked",
  "timestamp": "2026-01-15T14:20:00Z",
  "context": {
    "objective": "Submit training job on GPU cluster",
    "constraints": ["Requires 4x A100 GPUs", "24-hour time limit"]
  },
  "results": {
    "summary": "Job submission failed - no available resources",
    "artifacts": [],
    "metrics": {}
  },
  "blockers": [
    {
      "blocker_id": "blk-gpu-001",
      "type": "resource_unavailable",
      "description": "No 4x A100 nodes available. Current queue: 15 jobs, ETA: 6+ hours",
      "resolution_options": [
        "Wait for resources (ETA: 6 hours)",
        "Reduce to 2x A100 (available now)",
        "Use 4x A40 alternative (available now)",
        "Defer to off-peak hours (after 22:00)"
      ],
      "blocking_tasks": ["training_execution", "model_evaluation"]
    }
  ],
  "action_required": {
    "task": "Decide resource allocation strategy",
    "instructions": [
      "Evaluate resolution options",
      "Consider timeline constraints",
      "Select option and update plan"
    ],
    "expected_output": "Decision on resource allocation with justification",
    "priority": "critical"
  },
  "metadata": {
    "execution_time_ms": 5000,
    "retry_count": 3
  }
}
```

---

## Validation Checklist

Before sending a handoff, verify:

### Required Fields
- [ ] `handoff_id` is valid UUID v4
- [ ] `from_agent` and `to_agent` are valid agent names
- [ ] `status` is one of: success, partial, blocked, error
- [ ] `timestamp` is valid ISO 8601 format

### Status-Specific
- [ ] `success` → Has `results` with at least `summary`
- [ ] `partial` → Has both `results` and `blockers`
- [ ] `blocked` → Has `blockers` with resolution options
- [ ] `error` → Has `blockers` with error details

### Content Quality
- [ ] `context.objective` clearly states the goal
- [ ] `results.summary` is actionable, not vague
- [ ] `artifacts` have valid paths that exist
- [ ] `action_required.task` is specific and executable
- [ ] `blockers` have at least one resolution option

### Traceability
- [ ] `conversation_id` links to parent conversation
- [ ] `metadata.chain_position` reflects actual position
- [ ] Memory references are valid content hashes

---

## Anti-Patterns

### ❌ Vague Summaries
```json
// BAD
"summary": "Did some work on the code"

// GOOD
"summary": "Generated auth module with JWT support, 95% test coverage, all tests passing"
```

### ❌ Missing Resolution Options
```json
// BAD
"blockers": [{"type": "resource_unavailable", "description": "No GPUs"}]

// GOOD
"blockers": [{
  "type": "resource_unavailable",
  "description": "No 4x A100 available",
  "resolution_options": ["Wait 6 hours", "Use 2x A100", "Use 4x A40"]
}]
```

### ❌ Unverified Artifacts
```json
// BAD - path doesn't exist
"artifacts": [{"path": "src/maybe/here.py", "type": "code"}]

// GOOD - verified path
"artifacts": [{"path": "src/auth/auth.py", "type": "code", "description": "Main auth module"}]
```

### ❌ Generic Action Required
```json
// BAD
"action_required": {"task": "Review this"}

// GOOD
"action_required": {
  "task": "Review code for Tier 1 quality issues",
  "instructions": ["Check thread safety", "Verify error handling", "Review type hints"],
  "expected_output": "Quality report with specific issues or PASS"
}
```

### ❌ Blocked Without Context
```json
// BAD - no context for decision
"status": "blocked",
"blockers": [{"description": "Need approval"}]

// GOOD - context for decision
"status": "blocked",
"context": {
  "objective": "Deploy to production",
  "constraints": ["Requires security review"]
},
"blockers": [{
  "type": "missing_input",
  "description": "Security team approval required",
  "resolution_options": ["Submit security review request", "Escalate to manager"]
}]
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-15 | Initial specification |

