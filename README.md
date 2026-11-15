# Local Document Search

A local-first note library with full-text search powered by SQLite FTS5, a FastAPI JSON API, and a small browser UI. Documents remain in a local SQLite file; there is no account or cloud sync.

## Requirements

Python 3.10+ and a SQLite build with FTS5 support (bundled in common Python distributions).

## Run

```sh
python -m venv .venv
# activate the environment, then:
pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://127.0.0.1:8000. API docs are at http://127.0.0.1:8000/docs. Data lives in the ignored `library.sqlite3` file.

### Category

Additional project | Python, FastAPI, SQLite FTS5
