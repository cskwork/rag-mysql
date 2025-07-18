# RAG with MySQL, Ollama, and ChromaDB

This project demonstrates how to use the `vanna` library to generate SQL queries for a MySQL database using a Retrieval-Augmented Generation (RAG) approach. It leverages a local Large Language Model (LLM) via Ollama and uses ChromaDB as the vector store for the training data.

The application provides a web interface using Flask, allowing users to ask questions in natural language, which are then converted into SQL queries and executed against the database.

For a detailed explanation of the project's components and workflow, please see the [**Project Architecture Documentation**](.docs/architecture.md).

## Features

- **Natural Language to SQL**: Ask questions in plain English and get SQL queries in return.
- **Local LLM**: Uses a locally running Ollama instance, ensuring data privacy and cost-effectiveness.
- **Vector Store**: Employs ChromaDB to store and retrieve training data (DDL, documentation, and sample queries).
- **Web Interface**: A user-friendly web UI built with Flask for easy interaction.
- **Configuration-driven**: Easy to set up and configure using environment variables.

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com/) installed and running.
- A MySQL database.

## Setup

Follow these steps to get the project up and running:

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rag-mysql
```

### 2. Create and Activate a Virtual Environment

It is recommended to use a virtual environment to manage project dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file by copying the example file:

```bash
cp .env.example .env
```

Now, open the `.env` file and fill in your configuration details, especially your MySQL database credentials.

```ini
# --- Database Configuration ---
DB_HOST=your-mysql-host
DB_PORT=3306
DB_USER=your-mysql-user
DB_PASSWORD=your-mysql-password
DB_NAME=your-mysql-database

# --- Ollama Configuration ---
# See https://ollama.com/library
OLLAMA_MODEL="gemma3n:latest"

# --- Vanna.ai Configuration ---
# You can get a free API key from https://vanna.ai
# This is optional and only used if you want to use the Vanna.ai hosted vector store.
# VANNA_API_KEY="" 
# You can create a model name at https://vanna.ai/models
# VANNA_MODEL="my-model" # Your model name from Vanna.ai

# --- Application Configuration ---
FLASK_PORT=8084
```

### 5. Train the Model

Before you can ask questions, you need to "train" the Vanna instance on your database schema and any other relevant information. This process involves extracting metadata from your database and storing it in the ChromaDB vector store.

Run the following command to start the training process:

```bash
python app.py --train
```

This will connect to your database, extract the schema, and store it for the LLM to use as context. You can also add custom DDL statements, documentation, and SQL queries to the `app.py` file to improve accuracy.

## Usage

After the training is complete, you can start the Flask web application:

```bash
python app.py
```

The application will be running on `http://localhost:8084` by default. Open this URL in your web browser to access the Vanna UI and start asking questions.

### Production Usage

For a production environment, it is recommended to use a more robust web server like Gunicorn. A `run.sh` script is provided to make this easy.

First, make sure the script is executable:
```bash
chmod +x run.sh
```

Then, run the script to start the application with Gunicorn:
```bash
./run.sh
```

This will start the server on the configured host and port with a default of 4 worker processes. You can adjust the number of workers by setting the `GUNICORN_WORKERS` environment variable in your `.env` file.

## Glossary

- **RAG (Retrieval-Augmented Generation)**: A technique that combines a retrieval system (like a vector database) with a generative model (like an LLM). It first retrieves relevant information and then uses that information as context to generate a more accurate and informed response.
- **LLM (Large Language Model)**: A type of artificial intelligence model trained on vast amounts of text data to understand and generate human-like text.
- **Ollama**: A tool that allows you to run open-source LLMs, such as Llama 2, locally on your own machine.
- **ChromaDB**: An open-source vector database that makes it easy to store and search embeddings (numerical representations) of your data.
- **Vanna**: A Python library that helps you build AI-powered SQL generation applications. It connects to your database, "learns" from your schema and data, and allows you to ask questions that it translates into SQL.
- **Flask**: A lightweight web framework for Python used here to create the user interface for the application.
- **Gunicorn**: A Python WSGI HTTP Server for UNIX. It's a pre-fork worker model, meaning it's a production-ready server that is much more robust than the default Flask development server.

---
*This file was generated by an AI assistant.* 