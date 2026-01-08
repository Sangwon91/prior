# Prior

A principled coding agent that enforces software engineering fundamentals by design.

---

## The Problem

Current commercial coding agents fail to produce quality code by default. Instead of empowering developers, they often lead those unfamiliar with coding into dangerous territory.

- **False freedom**: To provide a "frictionless experience," vendors allow excessive degrees of freedom that degrade code quality.
- **Low baseline**: Training data averages toward mediocre code, making poor practices the default output.
- **Essential as optional**: Critical practices like testing are treated as optional. These agents produce spaghetti code without a single test—and feel no resistance doing so.
- **Misleading accessibility**: Non-developers are led to believe they can ship production code, unaware of the technical debt accumulating beneath the surface.

## Our Philosophy

Good code is more constrained than people realize. Too much freedom leads to poor quality.

- Quality emerges from **principled constraints**, not unlimited flexibility.
- **Fundamentals must be enforced**, not suggested.
- Software-level guardrails should be **built-in by default**, not bolted on after the fact.

## Why Not Rules or Hooks?

Existing solutions like custom rules and hooks fall short:

| Issue | Description |
|-------|-------------|
| **Lack of transparency** | Which rules are being applied? It's often unclear. |
| **Vendor lock-in** | When the vendor's implementation changes, your carefully crafted rules become obsolete. |
| **Non-seamless updates** | Maintaining and updating rules is cumbersome and unsystematic. |
| **No workflow enforcement** | Commands and hooks don't guarantee execution—randomness remains a frustration. |

Fundamentals shouldn't be managed through fragile text files. They should be explicitly configured, managed, and updated through structured software interactions.

## Core Fundamentals

Prior focuses on enforcing these essential elements of professional software development:

1. **Version Control**
   - Proper commit hygiene and branching strategies

2. **Project Architecture**
   - Coherent file tree structure and module organization

3. **Tech Stack Management**
   - Package managers, dependency versions, and library choices

4. **Knowledge Synchronization**
   - Bridging the gap between agent knowledge cutoff and latest library versions

5. **Review Process**
   - Code review workflows and quality gates

6. **Testing Strategy**
   - Test libraries, coverage requirements, and execution methods

## Motivation

After wrestling with the limitations of existing tools—watching them produce untested, unstructured code while hiding behind configurable rules that never quite work—the conclusion became clear:

**Build it ourselves.**

---

## Development

### Running Tests

This project uses a uv workspace with multiple packages. You can run tests in several ways:

**Run all tests (recommended):**
```bash
# Using Makefile (easiest)
make test
# or
make test-all

# Or manually with pytest
uv run pytest tests -v
PYTHONPATH=packages/agent/src uv run pytest packages/agent/tests -v
PYTHONPATH=packages/tui/src uv run pytest packages/tui/tests -v
```

**Run tests for specific packages:**
```bash
# Agent package only
make test-agent
# or
PYTHONPATH=packages/agent/src uv run pytest packages/agent/tests -v

# TUI package only
make test-tui
# or
PYTHONPATH=packages/tui/src uv run pytest packages/tui/tests -v

# Prior main package only
make test-prior
# or
uv run pytest tests -v
```

**Run tests with coverage:**
```bash
uv run pytest --cov=packages/agent/src --cov=packages/tui/src --cov=src/prior tests packages/agent/tests packages/tui/tests
```

---

*Prior is not about restricting creativity. It's about channeling it through proven engineering practices.*
