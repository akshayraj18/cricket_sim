.PHONY: install run kill test lint clean

# Install/sync project + dev dependencies (pytest, pyflakes) via uv.
install:
	uv sync

# Start the local web UI at http://localhost:8765
run:
	uv run python3 ui_server.py

# Kill any running ui_server.py processes.
kill:
	pkill -f ui_server.py || true

# Run the test suite (use `make test ARGS="-k impact_sub"` to filter).
test:
	uv run pytest $(ARGS)

# Static-check for undefined names, unused imports, etc.
lint:
	uv run pyflakes engine.py models.py players_data.py ui_server.py sim tests

# Remove cached bytecode.
clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete
