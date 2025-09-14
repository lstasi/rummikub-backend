.PHONY: all clean help test

# Default target
all: test

# Clean static directory and temporary files
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf __pycache__/
	@rm -rf tests/__pycache__/
	@echo "✅ Build artifacts cleaned"

# Run tests
test:
	@echo "Running tests..."
	@python -m py_compile *.py tests/*.py
	@cd tests && python test_api.py
	@cd tests && python test_actions.py
	@cd tests && python test_openapi.py
	@echo "✅ All tests completed"

# Help target
help:
	@echo "Available targets:"
	@echo "  all           - Run tests (default)"
	@echo "  clean         - Remove build artifacts"
	@echo "  test          - Run all tests and validation"
	@echo "  help          - Show this help message"