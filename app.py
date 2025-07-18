# -*- coding: utf-8 -*-
import os
import argparse
from dotenv import load_dotenv

# telemetry 비활성화로 capture() 에러 해결
os.environ["VANNA_DISABLE_TELEMETRY"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "false"

from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore
from vanna.flask import VannaFlaskApp

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()

# Database connection details
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "your-db")

# Ollama model configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3n:latest")

# Vanna.ai API key and model (optional)
VANNA_API_KEY = os.getenv("VANNA_API_KEY")
VANNA_MODEL = os.getenv("VANNA_MODEL", "rag-mysql-ollama")

# Flask app configuration
FLASK_PORT = int(os.getenv("FLASK_PORT", 8084))

# --- Vanna Setup ---
class MyVanna(ChromaDB_VectorStore, Ollama):
    """
    Custom Vanna class that uses ChromaDB for the vector store
    and a local Ollama instance for the LLM.
    """
    def __init__(self, config=None):
        # Default ChromaDB path
        chroma_db_path = "chromadb"
        # Ensure the directory exists
        if not os.path.exists(chroma_db_path):
            os.makedirs(chroma_db_path)
        
        # ChromaDB 설정에 telemetry 비활성화 추가
        chroma_config = {
            'path': chroma_db_path,
            'anonymized_telemetry': False  # ChromaDB telemetry 비활성화
        }
        ChromaDB_VectorStore.__init__(self, config=chroma_config)
        Ollama.__init__(self, config={'model': OLLAMA_MODEL})

vn = MyVanna()

# --- Database Connection ---
try:
    print(f"🔌 Attempting to connect to MySQL: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    vn.connect_to_mysql(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME  # 올바른 매개변수명: dbname
    )
    print("✅ Successfully connected to MySQL database.")
except Exception as e:
    print(f"🔥 Failed to connect to MySQL database: {e}")
    print("Please check your database credentials in the .env file.")
    # exit(1) # Uncomment this line to exit if the database connection fails

# --- Training ---
def train_vanna():
    """
    Trains the Vanna instance on the database schema and custom data.
    """
    print("💡 Starting Vanna training...")

    # 1. Information Schema
    # This query might need adjustments depending on your MySQL version and dialect.
    try:
        df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
        print(f"Extracted {len(df_information_schema)} columns from INFORMATION_SCHEMA.")
        
        # Break the schema into smaller, manageable chunks for the LLM
        plan = vn.get_training_plan_generic(df_information_schema)
        print("Generated a training plan based on the information schema.")
        
        # Train Vanna on the schema plan
        vn.train(plan=plan)
        print("✅ Training on information schema completed.")

    except Exception as e:
        print(f"🔥 Error during information schema training: {e}")

    # 2. Custom DDL Statements
    # Add any custom DDL statements here to provide more context to the LLM.
    # This is particularly useful for specifying primary keys, foreign keys, and indexes.
    # Example:
    # vn.train(ddl="""
    #     CREATE TABLE employees (
    #         employee_id INT PRIMARY KEY,
    #         first_name VARCHAR(50),
    #         last_name VARCHAR(50),
    #         department_id INT,
    #         hire_date DATE,
    #         FOREIGN KEY (department_id) REFERENCES departments(department_id)
    #     );
    # """)
    # print("✅ Training on custom DDL completed.")


    # 3. Custom Documentation
    # Add documentation about business terminology, definitions, and common queries.
    # This helps the LLM understand the semantics of your data.
    # Example:
    # vn.train(documentation="The 'sales' table contains all customer transactions.")
    # vn.train(documentation="OTIF score is the percentage of orders delivered on time and in full.")
    # print("✅ Training on custom documentation completed.")

    # 4. Custom SQL Queries
    # Add example SQL queries that are frequently used in your organization.
    # This helps the LLM learn common query patterns.
    # Example:
    # vn.train(sql="SELECT first_name, last_name FROM employees WHERE hire_date > '2023-01-01'")
    # print("✅ Training on custom SQL queries completed.")
    
    print("🎉 Vanna training finished.")

# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG with MySQL, Ollama, and ChromaDB")
    parser.add_argument("--train", action="store_true", help="Run the training process.")
    args = parser.parse_args()

    if args.train:
        train_vanna()
    else:
        print(f"🚀 Starting Flask app on http://localhost:{FLASK_PORT}")
        print("ℹ️ Use the --train flag to retrain the model (e.g., python app.py --train)")
        app = VannaFlaskApp(vn)
        app.run(host="0.0.0.0", port=FLASK_PORT) 