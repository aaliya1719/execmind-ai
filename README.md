# ExecMind AI

ExecMind AI is an autonomous multi-agent business intelligence platform for small businesses.

## Overview

This project scaffolds a modular Python application that will eventually:
- ingest sales data from CSV or Excel files,
- coordinate specialized AI agents for sales, marketing, and finance analysis,
- produce executive-style business insights and recommendations,
- expose a Streamlit-based user interface.

## Architecture

- app/agents/: specialized AI agents
- app/mcp/: MCP-facing tools for files and reports
- app/ui/: Streamlit front-end
- app/utils/: configuration, file handling, and logging helpers

## Getting Started

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and populate secrets.
4. Start the Streamlit app with `streamlit run app/ui/streamlit_app.py`.

## Security Notes

- Keep secrets in environment variables.
- Do not commit `.env` files.
- Validate uploaded files before processing.

## Roadmap

See [TODO.md](TODO.md) for the next implementation milestones.
