# Agents.md for AudioMesh

## 1. Project Layout

* `discovery/`: Peer discovery module (Python package)
* `audio_core/`: PulseAudio & JACK wrappers (Python package)
* `api/`: FastAPI server handling JSON endpoints
* `ui/`: Static assets (HTML/JS) served by API or separate web server
* `tests/`: Unit and integration tests (pytest)
* `pyproject.toml`: Poetry configuration and dependency management

## 2. Coding Standards

* **Python**: Follow PEP8; format with `black --line-length 88` and sort imports with `isort`.
* **Type Checking**: Use `mypy` with strict settings (`--strict` flag).
* **Linting**: Enforce with `flake8` (max complexity 10, max line length 88).
* **Docstrings**: Google style or NumPy style in all public functions/classes.

## 3. Tests

* **Run tests**:

  ```bash
  poetry run pytest --maxfail=1 --disable-warnings --cov=audio_core --cov-report=term-missing
  ```
* **Coverage requirement**: 90%+ for `audio_core/` and `api/` packages.
* **Fixtures & Mocks**: Use pytest fixtures for PulseAudio/Jack backends; mock external calls.

## 4. Build & Run

* **Install dependencies**:

  ```bash
  poetry install
  ```
* **Start services (local)**:

  ```bash
  poetry run audio_mesh discovery --config config.yaml &
  poetry run audio_mesh audio-core --config config.yaml &
  poetry run audio_mesh api --reload --host 0.0.0.0 --port 8080 &
  ```
* **Web UI**: Open `http://localhost:8080/` in browser.

## 5. Commits & PRs

* **Commit message format**: `<type>(<scope>): <subject>`

  * `feat`, `fix`, `chore`, `docs`, `test`, `refactor`
  * e.g. `feat(audio_core): add RTP send wrapper`
* **Branch naming**: `feature/<short-description>`, `bugfix/<issue-number>`.
* **PR checks**: Must pass `poetry run pytest`, `flake8`, `mypy`, and `black --check`.

## 6. Agent-Specific Overrides

* **Nested Agents.md**: A file in subpackages (e.g., `audio_core/Agents.md`) overrides root settings for that module.
* **Inline prompts**: Any in-code `# codex:` comments take precedence over Agents.md.

