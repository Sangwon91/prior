.PHONY: test test-all test-agent test-tui test-tools test-workflow test-workflow-visual test-prior test-protocol test-adapter help

help:
	@echo "Available test commands:"
	@echo "  make test                - Run all tests (same as test-all)"
	@echo "  make test-all            - Run all tests across all packages"
	@echo "  make test-protocol       - Run only protocol package tests"
	@echo "  make test-adapter        - Run only adapter package tests"
	@echo "  make test-agent          - Run only agent package tests"
	@echo "  make test-tui            - Run only tui package tests"
	@echo "  make test-tools          - Run only tools package tests"
	@echo "  make test-workflow       - Run only workflow package tests (CI mode)"
	@echo "  make test-workflow-visual - Run workflow tests with image output saved"
	@echo "  make test-prior          - Run only prior main package tests"

test: test-all

test-all:
	@echo "========================================="
	@echo "Running all tests across all packages..."
	@echo "========================================="
	@echo ""
	@echo "--- Running prior main tests ---"
	@uv run pytest tests -v
	@echo ""
	@echo "--- Running protocol package tests ---"
	@uv run --package protocol pytest packages/protocol/tests -v
	@echo ""
	@echo "--- Running adapter package tests ---"
	@uv run --package adapter pytest packages/adapter/tests -v
	@echo ""
	@echo "--- Running tools package tests ---"
	@uv run --package tools pytest packages/tools/tests -v
	@echo ""
	@echo "--- Running workflow package tests ---"
	@uv run --package workflow pytest packages/workflow/tests -v
	@echo ""
	@echo "--- Running agent package tests ---"
	@uv run --package agent pytest packages/agent/tests -v
	@echo ""
	@echo "--- Running tui package tests ---"
	@uv run --package tui pytest packages/tui/tests -v
	@echo ""
	@echo "========================================="
	@echo "All tests completed!"

test-protocol:
	@echo "Running protocol package tests..."
	@uv run --package protocol pytest packages/protocol/tests -v

test-adapter:
	@echo "Running adapter package tests..."
	@uv run --package adapter pytest packages/adapter/tests -v

test-agent:
	@echo "Running agent package tests..."
	@uv run --package agent pytest packages/agent/tests -v

test-tui:
	@echo "Running tui package tests..."
	@uv run --package tui pytest packages/tui/tests -v

test-tools:
	@echo "Running tools package tests..."
	@uv run --package tools pytest packages/tools/tests -v

test-workflow:
	@echo "Running workflow package tests..."
	@uv run --package workflow pytest packages/workflow/tests -v

test-workflow-visual:
	@echo "Running workflow package tests with visual output..."
	@echo "This will save generated mermaid images to test_output/images/"
	@uv run --package workflow pytest packages/workflow/tests -v --save-images --image-output-dir=test_output/images

test-prior:
	@echo "Running prior main package tests..."
	@uv run pytest tests -v
