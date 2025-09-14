.PHONY: all copy-static clean help

# Default target
all: copy-static

# Copy web files to static directory
copy-static:
	@echo "Copying web files to static directory..."
	@mkdir -p static
	@cp web/index.html static/ 2>/dev/null || echo "Warning: web/index.html not found"
	@cp web/rules.html static/ 2>/dev/null || echo "Warning: web/rules.html not found"
	@echo "✅ Static files updated"

# Clean static directory
clean:
	@echo "Cleaning static directory..."
	@rm -rf static/
	@echo "✅ Static directory cleaned"

# Initialize submodules (useful for CI/CD)
init-submodules:
	@echo "Initializing git submodules..."
	@git submodule init
	@git submodule update
	@echo "✅ Submodules initialized"

# Full setup (submodules + static files)
setup: init-submodules copy-static
	@echo "✅ Full setup complete"

# Help target
help:
	@echo "Available targets:"
	@echo "  all           - Copy static files (default)"
	@echo "  copy-static   - Copy web files to static directory"
	@echo "  clean         - Remove static directory"
	@echo "  init-submodules - Initialize git submodules"
	@echo "  setup         - Full setup (submodules + static files)"
	@echo "  help          - Show this help message"