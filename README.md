Email Agent
===========

LangGraph-powered Gmail automation that reads unanswered emails, categorizes
them, optionally retrieves internal knowledge via RAG, drafts a reply, and
creates a Gmail draft after a quick proofread loop.

Key features
------------
- Gmail inbox fetch + draft creation (no auto-send by default).
- Email categorization: product enquiry, complaint, feedback, unrelated.
- RAG over internal knowledge using Chroma + Cohere embeddings.
- Multi-step write -> proofread loop (up to 3 attempts).
- Optional FastAPI + LangServe API for remote invocation.

Project layout
--------------
- main.py: Run the workflow from the CLI.
- deploy_api.py: Run a FastAPI server exposing the workflow.
- create_embedding.py: Build the Chroma vector store from internal docs.
- data/company_internal_knowledge.txt: Knowledge base for RAG.
- src/: LangGraph workflow, nodes, and Gmail tools.
- agents/ + prompts/: LLM chains and prompt templates.

Setup
-----
1) Create a virtual environment and install dependencies:

	python -m venv .venv
	.\.venv\Scripts\activate
	pip install -r requirements.txt

2) Create a .env file in the project root:

	GROQ_API_KEY=your_groq_api_key
	COHERE_API_KEY=your_cohere_api_key
	MY_EMAIL=you@example.com
	# Optional paths (defaults shown)
	CREDENTIALS_PATH=credentials.json
	TOKEN_PATH=token.json

3) Configure Gmail API OAuth:

	- In Google Cloud Console, enable Gmail API.
	- Create an OAuth 2.0 Client ID (Desktop App).
	- Download the credentials JSON and save it as credentials.json
	  in the project root (or set CREDENTIALS_PATH).
	- On first run, a browser window opens to authorize and saves
	  token.json (or TOKEN_PATH) for future runs.

Build the knowledge base
------------------------
Edit data/company_internal_knowledge.txt with your internal content, then run:

	python create_embedding.py

This creates the Chroma index under db/. Re-run any time the knowledge file
changes.

Run the workflow (CLI)
----------------------

	python main.py

The workflow checks for unanswered emails within the last 8 hours, writes a
draft reply, and creates a Gmail draft in the original thread.

Run the API server
------------------

	python deploy_api.py

Open http://localhost:8000/docs to explore LangServe endpoints and test
requests.

Notes
-----
- Draft creation is enabled by default. If you want to send emails directly,
  wire the send_email_response node into the workflow in src/nodes.py.
- RAG uses the db/ directory. Delete it to rebuild from scratch.
