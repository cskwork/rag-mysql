# Project Architecture

This document provides a detailed overview of the architecture for the RAG (Retrieval-Augmented Generation) with MySQL, Ollama, and ChromaDB project.

## Overview

The application is designed to convert natural language questions into SQL queries that can be executed against a MySQL database. It follows a classic RAG pattern, where a generative language model is augmented with information retrieved from a knowledge base. In this case, the knowledge base contains information about the database schema.

The architecture can be broken down into two main phases: the **Training Phase** and the **Query Phase**.

![Project Architecture Diagram](diagrams/architecture.svg)

*(This diagram will be created in the next step)*

## Components

The project is composed of the following key components:

### 1. **Flask Web Application (`app.py`)**

-   **Role**: Serves as the main entry point for the application and provides the user interface.
-   **Functionality**:
    -   Initializes and configures all other components.
    -   Provides a web interface using the `VannaFlaskApp` for users to ask questions.
    -   Includes a command-line interface to trigger the training process (`--train`).

### 2. **Vanna (`vanna` library)**

-   **Role**: The core library that orchestrates the entire RAG process.
-   **Functionality**:
    -   Connects to the MySQL database to extract schema information.
    -   Manages the training data (DDL, documentation, sample queries).
    -   Coordinates the interaction between the LLM (Ollama) and the vector store (ChromaDB).
    -   Constructs the final prompts sent to the LLM.

### 3. **Ollama (Local LLM)**

-   **Role**: The generative language model that powers the application.
-   **Functionality**:
    -   **Embedding**: Converts text (DDL, documentation, questions) into numerical vectors.
    -   **SQL Generation**: Generates SQL queries based on the user's question and the context provided by Vanna.
-   **Note**: Ollama runs as a separate, local service. The application communicates with it via an API.

### 4. **ChromaDB (Vector Store)**

-   **Role**: The knowledge base for the application.
-   **Functionality**:
    -   Stores the vector embeddings of the training data.
    -   Provides fast and efficient similarity search to find the most relevant information for a given question.
-   **Note**: In this project, ChromaDB runs locally, storing its data in the `chromadb` directory.

### 5. **Gunicorn (Production Server)**

-   **Role**: A production-ready web server for deploying the application.
-   **Functionality**:
    -   Manages multiple worker processes to handle concurrent requests.
    -   Provides a more robust and secure environment than the default Flask development server.

## Workflow

### Training Phase

1.  The user initiates the training process via the command line (`python app.py --train`).
2.  `Vanna` connects to the **MySQL** database and fetches the schema information (`INFORMATION_SCHEMA.COLUMNS`).
3.  `Vanna` sends this schema information (and any other training data) to **Ollama** to be converted into vector embeddings.
4.  `Vanna` stores these embeddings in **ChromaDB**.

### Query Phase

1.  A user submits a question through the **Flask Web Application**.
2.  `Vanna` sends the question to **Ollama** to get a vector embedding.
3.  `Vanna` uses this question embedding to query **ChromaDB** for the most similar (i.e., most relevant) schema information.
4.  `Vanna` retrieves the original schema text (DDL) from ChromaDB.
5.  `Vanna` constructs a detailed prompt containing the user's question and the retrieved schema information.
6.  This prompt is sent to **Ollama**, which generates the final SQL query.
7.  The Flask app displays the generated SQL to the user and can execute it against the database. 