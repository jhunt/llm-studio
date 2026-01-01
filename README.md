# LLM Studio

LLM Studio is an open-source system for orchestrating data-driven,
parallel LLM prompt engineering at scale. It features a
user-friendly front-end editor, a powerful backend API for
scheduled generation, and a command-line utility for scripting
support.

## Background

LLM (Large Language Model) technology has revolutionized the field
of natural language processing (NLP), enabling machines to
understand and generate human-like text with unprecedented
accuracy. LLM Studio is designed to simplify the process of prompt
engineering, which involves crafting high-quality prompts that
elicit desired responses from these models.

## Use Cases

- **Research**: LLM Studio can be used as a tool for researchers to
  efficiently generate and analyze text data.

- **Content Generation**: The system can help automate content creation
  tasks, such as generating product descriptions or article
  summaries.
- **Data Analysis**: By providing a platform for exploratory execution,
  LLM Studio enables users to quickly analyze large datasets and
  identify patterns.

## Getting Started

To run LLM Studio, we recommend using the official `filefrog/llm-studio`
Docker image. Here's an example of how to start the container:

```
docker run --restart=always -d --name llm-studio \
  -v /srv/data:/data \
  -v ./inputs:/app/inputs \
  -p 9000:5000 \
  -e PORT=5000 \
  -e OLLAMA_HOST=http://hosted.ollama.int:11434 \
  -e OLLAMA_MODEL=llama3.2 \
  -e LLM_STUDIO_DB=/data/studio.db \
  filefrog/llm-studio:latest
```

## Environment Variables

The following environment variables are understood:

- **OLLAMA_HOST**: The URL of the Ollama installation.
- **OLLAMA_MODEL**: The name of the LLM model to use. Defaults to
  `llama3.2`.
- **PORT**: The TCP port to bind on all interfaces (i.e., 0.0.0.0).
  Defaults to 5000.
- **LLM_STUDIO_DB**: The full path (inside the container FS) of the
  SQLite3 database that houses folio definitions and cached responses.
  Defaults to `/data/studio.db` (which means you probably want to
  bind-mount the `/data` directory).

## Recommended Volumes/Mountpoints

We recommend mounting the following volumes:

- `/data`: The meta database housing folio definitions and cached
  responses will be stored in here by default.

- `/app/inputs`: For storing flat files (CSV, Parquet, JSON, raw text
  directories) to access with the DuckDB data gateway.

Using a volume of input files mounted at `/app/inputs`, for example,
we can create a folio with a data query of:

```sql
select * from 'inputs/accounts/*.csv'
```

To parse all of the CSVs in the accounts/ directory and return them as
tables, suitable for a per-account prompt definition.

## Troubleshooting

Please consult the official Docker documentation for assistance
with troubleshooting or modifying the container configuration.
