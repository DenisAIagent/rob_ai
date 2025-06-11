# DevCraft AI

This repository contains a minimal prototype for the **DevCraft AI** project.
The goal is to orchestrate a set of AI agents that generate full-stack
applications. The `main.py` file implements the locked CrewAI pipeline. A
FastAPI backend exposes endpoints that can trigger this generation process and
stream logs to the frontend.

## Structure

```
.
├── main.py                # CrewAI pipeline (do not modify)
├── api/
│   ├── server.py          # FastAPI backend
│   ├── models.py          # Pydantic request/response models
│   └── utils.py           # Helper functions for job management
└── tests/
    └── test_server.py     # Unit tests for the API
```

Run the tests with:

```bash
pytest
```

## Frontend

The `frontend` directory contains a simple web interface that interacts with the
API. It displays analysis results, streams logs via WebSockets and provides a
link to download the generated project.

Open `frontend/index.html` in a browser while the API server is running.

## Deployment

Sample Docker and Railway configurations are provided in the `deploy/` folder
together with a minimal GitHub Actions workflow.
