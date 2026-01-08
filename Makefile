.PHONY: test test-all test-agent test-tui test-prior help

help:
	@echo "Available test commands:"
	@echo "  make test        - Run all tests (same as test-all)"
	@echo "  make test-all    - Run all tests across all packages"
	@echo "  make test-agent  - Run only agent package tests"
	@echo "  make test-tui    - Run only tui package tests"
	@echo "  make test-prior   - Run only prior main package tests"

test: test-all

test-all:
	@echo "========================================="
	@echo "Running all tests across all packages..."
	@echo "========================================="
	@echo ""
	@echo "--- Running prior main tests ---"
	@uv run pytest tests -v
	@echo ""
	@echo "--- Running agent package tests ---"
	@PYTHONPATH=packages/agent/src uv run pytest packages/agent/tests -v
	@echo ""
	@echo "--- Running tui package tests ---"
	@PYTHONPATH=packages/tui/src uv run pytest packages/tui/tests -v
	@echo ""
	@echo "========================================="
	@echo "All tests completed!"

test-agent:
	@echo "Running agent package tests..."
	@PYTHONPATH=packages/agent/src uv run pytest packages/agent/tests -v

test-tui:
	@echo "Running tui package tests..."
	@PYTHONPATH=packages/tui/src uv run pytest packages/tui/tests -v

test-prior:
	@echo "Running prior main package tests..."
	@uv run pytest tests -v
