graph TD
    subgraph User Interaction
        U[User]
    end

    subgraph Application Layer
        F[Flask Web App / Gunicorn]
        V[Vanna Library]
    end

    subgraph AI & Data Layer
        O[Ollama LLM]
        C[ChromaDB Vector Store]
        M[MySQL Database]
    end

    U --> F
    F --> V

    subgraph Training Workflow
        V -- "1. Fetches Schema" --> M
        V -- "2. Sends text for embedding" --> O
        O -- "3. Returns vector" --> V
        V -- "4. Stores vector" --> C
    end

    subgraph Query Workflow
        F -- "1. Sends user question" --> V
        V -- "2. Sends question for embedding" --> O
        O -- "3. Returns question vector" --> V
        V -- "4. Queries for similar vectors" --> C
        C -- "5. Returns relevant vectors" --> V
        V -- "6. Retrieves original DDL" --> C
        V -- "7. Sends DDL + question to LLM" --> O
        O -- "8. Generates SQL" --> V
        V -- "9. Returns SQL to app" --> F
    end

    style Training Workflow fill:#f9f9f9,stroke:#333,stroke-width:2px
    style Query Workflow fill:#f0f8ff,stroke:#333,stroke-width:2px 