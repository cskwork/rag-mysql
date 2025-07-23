# -*- coding: utf-8 -*-
import os
import argparse
from dotenv import load_dotenv

# telemetry 비활성화로 capture() 에러 해결
os.environ["VANNA_DISABLE_TELEMETRY"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "false"

from vanna.ollama import Ollama
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from vanna.flask import VannaFlaskApp
from openai import OpenAI

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()

# Database connection details
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "your-db")

# LLM Provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Ollama model configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3n:latest")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8084")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "RAG-MySQL")

# Vanna.ai API key and model (optional)
VANNA_API_KEY = os.getenv("VANNA_API_KEY")
VANNA_MODEL = os.getenv("VANNA_MODEL", "rag-mysql-ollama")

# Flask app configuration
FLASK_PORT = int(os.getenv("FLASK_PORT", 8084))

# LLM 데이터 접근 설정
ALLOW_LLM_TO_SEE_DATA = os.getenv("ALLOW_LLM_TO_SEE_DATA", "True").lower() == "true"

# --- Vanna Setup ---
class MyVannaOllama(ChromaDB_VectorStore, Ollama):
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

class MyVannaOpenAI(ChromaDB_VectorStore, OpenAI_Chat):
    """
    Custom Vanna class that uses ChromaDB for the vector store
    and OpenAI's GPT models for the LLM.
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
        OpenAI_Chat.__init__(self, config={'api_key': OPENAI_API_KEY, 'model': OPENAI_MODEL})

class MyVannaOpenRouter(ChromaDB_VectorStore, OpenAI_Chat):
    """
    Custom Vanna class that uses ChromaDB for the vector store
    and OpenRouter's unified API for accessing multiple LLM providers.
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
        
        # Create custom OpenAI client for OpenRouter
        openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": OPENROUTER_SITE_URL,
                "X-Title": OPENROUTER_SITE_NAME,
            }
        )
        
        OpenAI_Chat.__init__(
            self, 
            client=openrouter_client,
            config={'model': OPENROUTER_MODEL}
        )

def create_vanna_instance():
    """
    팩토리 함수: 설정된 LLM 프로바이더에 따라 적절한 Vanna 인스턴스를 생성
    """
    if LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-api-key-here":
            raise ValueError("OpenAI API key가 설정되지 않았습니다. .env 파일에서 OPENAI_API_KEY를 설정해주세요.")
        print(f"🤖 OpenAI provider 사용 중 (model: {OPENAI_MODEL})")
        return MyVannaOpenAI()
    elif LLM_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "sk-your-api-key-here":
            raise ValueError("OpenRouter API key가 설정되지 않았습니다. .env 파일에서 OPENROUTER_API_KEY를 설정해주세요.")
        print(f"🌐 OpenRouter provider 사용 중 (model: {OPENROUTER_MODEL})")
        return MyVannaOpenRouter()
    elif LLM_PROVIDER == "ollama":
        print(f"🦙 Ollama provider 사용 중 (model: {OLLAMA_MODEL})")
        return MyVannaOllama()
    else:
        raise ValueError(f"지원하지 않는 LLM provider: {LLM_PROVIDER}. 'ollama', 'openai', 또는 'openrouter'를 사용하세요.")

vn = create_vanna_instance()

# --- Database Connection ---
def connect_to_database():
    """데이터베이스 연결 함수 (재연결 지원)"""
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
        return True
    except Exception as e:
        print(f"🔥 Failed to connect to MySQL database: {e}")
        print("Please check your database credentials in the .env file.")
        return False

def ensure_database_connection():
    """데이터베이스 연결 상태 확인 및 재연결"""
    try:
        # 간단한 쿼리로 연결 상태 테스트
        vn.run_sql("SELECT 1")
        return True
    except Exception:
        print("🔄 Database connection lost, attempting to reconnect...")
        return connect_to_database()

# 초기 데이터베이스 연결
if not connect_to_database():
    print("⚠️ Starting without database connection. Please fix database settings and restart.")
    # exit(1) # Uncomment this line to exit if the database connection fails

# Create Flask app for Gunicorn (module-level)
vanna_flask_app = VannaFlaskApp(vn, allow_llm_to_see_data=ALLOW_LLM_TO_SEE_DATA)
app = vanna_flask_app.flask_app

# --- DDL File Processing ---
def chunk_ddl_content(content, max_chunk_size=4000):
    """
    긴 DDL 내용을 토큰 제한에 맞게 청크로 분할
    각 청크는 완전한 CREATE TABLE 문을 포함하도록 보장
    
    Args:
        content (str): 분할할 DDL 내용
        max_chunk_size (int): 최대 청크 크기 (문자 단위)
    
    Returns:
        list: DDL 청크들의 리스트
    """
    if len(content) <= max_chunk_size:
        return [content]
    
    chunks = []
    statements = []
    
    # CREATE TABLE 문으로 분할
    lines = content.split('\n')
    current_statement = []
    in_create_table = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # CREATE TABLE 시작 감지
        if line.upper().startswith('CREATE TABLE'):
            if current_statement:  # 이전 문 저장
                statements.append('\n'.join(current_statement))
            current_statement = [line]
            in_create_table = True
        # CREATE TABLE 종료 감지 (세미콜론으로 끝나는 라인)
        elif in_create_table and line.endswith(';'):
            current_statement.append(line)
            statements.append('\n'.join(current_statement))
            current_statement = []
            in_create_table = False
        # CREATE TABLE 내부 라인
        elif in_create_table:
            current_statement.append(line)
        # 기타 DDL 문
        else:
            if current_statement:
                statements.append('\n'.join(current_statement))
                current_statement = []
            statements.append(line)
    
    # 마지막 문 처리
    if current_statement:
        statements.append('\n'.join(current_statement))
    
    # 청크 생성 (크기 제한 고려)
    current_chunk = []
    current_size = 0
    
    for statement in statements:
        statement_size = len(statement)
        
        # 단일 문이 max_chunk_size를 초과하는 경우
        if statement_size > max_chunk_size:
            if current_chunk:  # 현재 청크 저장
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            # 큰 문을 별도 청크로 처리
            chunks.append(statement)
            continue
        
        # 현재 청크에 추가할 수 있는지 확인
        if current_size + statement_size + 2 <= max_chunk_size:  # +2 for \n\n
            current_chunk.append(statement)
            current_size += statement_size + 2
        else:
            # 현재 청크 저장하고 새 청크 시작
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            current_chunk = [statement]
            current_size = statement_size
    
    # 마지막 청크 저장
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks

def read_ddl_files(input_folder="input", chunk_large_files=True, max_chunk_size=4000):
    """
    input 폴더에서 DDL 파일들을 읽어와서 훈련 데이터로 반환
    긴 파일은 자동으로 청크로 분할
    
    Args:
        input_folder (str): DDL 파일이 있는 폴더
        chunk_large_files (bool): 큰 파일을 청크로 분할할지 여부
        max_chunk_size (int): 최대 청크 크기 (문자 단위)
    """
    ddl_files = []
    input_path = os.path.join(os.getcwd(), input_folder)
    
    if not os.path.exists(input_path):
        print(f"⚠️ Input folder '{input_path}' does not exist.")
        return ddl_files
    
    # .sql 확장자 파일들 찾기
    for filename in os.listdir(input_path):
        if filename.lower().endswith('.sql'):
            file_path = os.path.join(input_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read().strip()
                    if content:
                        # 큰 파일 청킹 처리
                        if chunk_large_files and len(content) > max_chunk_size:
                            chunks = chunk_ddl_content(content, max_chunk_size)
                            for i, chunk in enumerate(chunks):
                                ddl_files.append({
                                    'filename': f"{filename}_chunk_{i+1}",
                                    'content': chunk,
                                    'original_file': filename
                                })
                            print(f"📄 Loaded DDL file: {filename} (분할됨: {len(chunks)} 청크)")
                        else:
                            ddl_files.append({
                                'filename': filename,
                                'content': content
                            })
                            print(f"📄 Loaded DDL file: {filename}")
            except Exception as e:
                print(f"🔥 Error reading file {filename}: {e}")
    
    return ddl_files

def train_ddl_files(chunk_large_files=True, max_chunk_size=4000):
    """
    input 폴더의 DDL 파일들로 Vanna 훈련 (자동 청킹 지원)
    
    Args:
        chunk_large_files (bool): 큰 파일을 청크로 분할할지 여부
        max_chunk_size (int): 최대 청크 크기 (문자 단위)
    """
    print("💡 Starting DDL file training with smart chunking...")
    
    ddl_files = read_ddl_files(
        chunk_large_files=chunk_large_files, 
        max_chunk_size=max_chunk_size
    )
    
    if not ddl_files:
        print("⚠️ No DDL files found in input/ folder.")
        return
    
    # 각 DDL 파일/청크로 훈련
    success_count = 0
    error_count = 0
    
    for ddl_file in ddl_files:
        try:
            chunk_info = f" (크기: {len(ddl_file['content'])} 문자)"
            print(f"🔄 Training: {ddl_file['filename']}{chunk_info}")
            
            vn.train(ddl=ddl_file['content'])
            print(f"✅ Training completed for: {ddl_file['filename']}")
            success_count += 1
            
        except Exception as e:
            print(f"🔥 Error training with {ddl_file['filename']}: {e}")
            error_count += 1
    
    print(f"🎉 DDL training finished. Success: {success_count}, Errors: {error_count}")

def train_per_table():
    """
    데이터베이스의 각 테이블별로 개별 DDL 훈련 (가장 세밀한 단위)
    """
    print("💡 Starting per-table DDL training...")
    
    try:
        # 모든 테이블 목록 조회
        tables_df = vn.run_sql(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{DB_NAME}'")
        
        if tables_df.empty:
            print("⚠️ No tables found in the database.")
            return
        
        table_count = 0
        for _, row in tables_df.iterrows():
            table_name = row['TABLE_NAME']
            try:
                # 개별 테이블의 DDL 생성
                ddl_query = f"SHOW CREATE TABLE {table_name}"
                ddl_result = vn.run_sql(ddl_query)
                
                if not ddl_result.empty:
                    ddl_content = ddl_result.iloc[0, 1]  # CREATE TABLE 문
                    vn.train(ddl=ddl_content)
                    print(f"✅ Training completed for table: {table_name}")
                    table_count += 1
                    
            except Exception as e:
                print(f"🔥 Error training table {table_name}: {e}")
                
        print(f"🎉 Per-table training finished. Processed {table_count} tables.")
        
    except Exception as e:
        print(f"🔥 Error during per-table training: {e}")

def clear_training_data():
    """
    모든 훈련 데이터를 삭제 (ChromaDB 컬렉션 초기화)
    """
    print("🗑️ Clearing all training data...")
    
    try:
        # ChromaDB 컬렉션들 제거
        collections_to_clear = ["ddl", "sql", "documentation"]
        
        for collection_name in collections_to_clear:
            try:
                vn.remove_collection(collection_name)
                print(f"✅ Cleared collection: {collection_name}")
            except Exception as e:
                print(f"⚠️ Collection '{collection_name}' not found or already empty: {e}")
        
        print("🎉 All training data cleared successfully.")
        
    except Exception as e:
        print(f"🔥 Error clearing training data: {e}")

# --- Training ---
def train_vanna(include_ddl_files=True, include_per_table=False):
    """
    하이브리드 접근법: Information Schema + DDL 파일들로 종합 훈련
    
    Args:
        include_ddl_files (bool): input/ 폴더의 DDL 파일들 포함 여부
        include_per_table (bool): 개별 테이블 DDL 훈련 포함 여부
    """
    print("💡 Starting comprehensive Vanna training (hybrid approach)...")
    
    training_steps = []
    
    # 1. Information Schema 훈련
    try:
        print("📊 Step 1: Training with Information Schema...")
        
        # 연결 상태 확인 및 재연결
        if not ensure_database_connection():
            print("⚠️ Cannot connect to database for Information Schema training")
            return training_steps
            
        df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
        print(f"Extracted {len(df_information_schema)} columns from INFORMATION_SCHEMA.")
        
        # 스키마를 LLM이 처리할 수 있는 작은 청크로 분할
        plan = vn.get_training_plan_generic(df_information_schema)
        print("Generated a training plan based on the information schema.")
        
        # 훈련 계획으로 Vanna 훈련
        vn.train(plan=plan)
        print("✅ Training on information schema completed.")
        training_steps.append("Information Schema")

    except Exception as e:
        print(f"🔥 Error during information schema training: {e}")
        print("🔄 Attempting to reconnect...")
        if ensure_database_connection():
            print("✅ Reconnected successfully, please retry training")

    # 2. DDL 파일들로 훈련 (선택적)
    if include_ddl_files:
        try:
            print("📄 Step 2: Training with DDL files...")
            ddl_files = read_ddl_files()
            
            if ddl_files:
                for ddl_file in ddl_files:
                    try:
                        vn.train(ddl=ddl_file['content'])
                        print(f"✅ Training completed for: {ddl_file['filename']}")
                    except Exception as e:
                        print(f"🔥 Error training with {ddl_file['filename']}: {e}")
                        
                print(f"✅ DDL files training completed. Processed {len(ddl_files)} files.")
                training_steps.append(f"DDL Files ({len(ddl_files)} files)")
            else:
                print("⚠️ No DDL files found in input/ folder.")
                
        except Exception as e:
            print(f"🔥 Error during DDL files training: {e}")

    # 3. 개별 테이블 훈련 (선택적)
    if include_per_table:
        try:
            print("🗂️ Step 3: Training with individual table DDLs...")
            
            # 연결 상태 확인 및 재연결
            if not ensure_database_connection():
                print("⚠️ Cannot connect to database for per-table training")
                return training_steps
                
            tables_df = vn.run_sql(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{DB_NAME}'")
            
            if not tables_df.empty:
                table_count = 0
                for _, row in tables_df.iterrows():
                    table_name = row['TABLE_NAME']
                    try:
                        # 각 테이블마다 연결 상태 확인
                        if not ensure_database_connection():
                            print(f"⚠️ Connection lost while processing table {table_name}")
                            break
                            
                        ddl_query = f"SHOW CREATE TABLE {table_name}"
                        ddl_result = vn.run_sql(ddl_query)
                        
                        if not ddl_result.empty:
                            ddl_content = ddl_result.iloc[0, 1]
                            vn.train(ddl=ddl_content)
                            table_count += 1
                            
                    except Exception as e:
                        print(f"⚠️ Error training table {table_name}: {e}")
                        
                print(f"✅ Per-table training completed. Processed {table_count} tables.")
                training_steps.append(f"Individual Tables ({table_count} tables)")
            else:
                print("⚠️ No tables found in the database.")
                
        except Exception as e:
            print(f"🔥 Error during per-table training: {e}")
            print("🔄 Attempting to reconnect...")
            if ensure_database_connection():
                print("✅ Reconnected successfully, please retry training")

    # 4. 사용자 정의 문서화 (향후 확장 가능)
    # 비즈니스 용어, 정의, 일반적인 쿼리에 대한 문서 추가
    # 예시:
    # vn.train(documentation="The 'sales' table contains all customer transactions.")
    # vn.train(documentation="OTIF score is the percentage of orders delivered on time and in full.")
    # training_steps.append("Custom Documentation")

    # 5. 사용자 정의 SQL 쿼리 (향후 확장 가능)
    # 조직에서 자주 사용되는 예시 SQL 쿼리 추가
    # 예시:
    # vn.train(sql="SELECT first_name, last_name FROM employees WHERE hire_date > '2023-01-01'")
    # training_steps.append("Custom SQL Queries")
    
    print(f"🎉 Comprehensive training finished! Completed steps: {', '.join(training_steps)}")
    return training_steps

# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG with MySQL, Ollama, and ChromaDB")
    parser.add_argument("--train", action="store_true", help="Run the training process.")
    parser.add_argument("--train-ddl", action="store_true", help="Train using DDL files from input/ folder.")
    parser.add_argument("--train-per-table", action="store_true", help="Train using individual table DDLs from database.")
    parser.add_argument("--train-hybrid", action="store_true", help="Train using hybrid approach (schema + DDL files).")
    parser.add_argument("--no-chunking", action="store_true", help="Disable automatic DDL file chunking.")
    parser.add_argument("--chunk-size", type=int, default=4000, help="Maximum chunk size for DDL files (default: 4000).")
    parser.add_argument("--clear", action="store_true", help="Clear all training data from ChromaDB.")
    args = parser.parse_args()

    if args.train:
        train_vanna()
    elif args.train_ddl:
        train_ddl_files(
            chunk_large_files=not args.no_chunking,
            max_chunk_size=args.chunk_size
        )
    elif args.train_per_table:
        train_per_table()
    elif args.train_hybrid:
        train_vanna(
            include_ddl_files=True,
            include_per_table=False
        )
    elif args.clear:
        clear_training_data()
    else:
        # 기본 훈련: 하이브리드 접근법 (정보 스키마 + DDL 파일들) - 가장 권장되는 방법
        print("🎯 No specific training mode specified. Using optimal hybrid training...")
        print("💡 This combines information schema + DDL files for best results")
        
        # 하이브리드 훈련 실행
        training_steps = train_vanna(
            include_ddl_files=True,
            include_per_table=False
        )
        
        if training_steps:
            print("✅ Default training completed successfully!")
            print("📝 Available training options:")
            print("   --train          : Information schema only")
            print("   --train-ddl      : DDL files only (with chunking)")
            print("   --train-per-table: Individual table DDLs")
            print("   --train-hybrid   : Hybrid approach (recommended)")
            print("   --clear          : Clear all training data")
            print("💡 Available LLM providers: ollama, openai, openrouter")
        
        print(f"🚀 Starting Flask app on http://localhost:{FLASK_PORT}")
        print(f"🔍 LLM data access: {'Enabled' if ALLOW_LLM_TO_SEE_DATA else 'Disabled'}")
        
        # Flask 앱 시작 전 연결 재확인
        if ensure_database_connection():
            print("✅ Database connection verified before starting Flask app")
        else:
            print("⚠️ Starting Flask app without database connection")
            
        vanna_flask_app.run(host="0.0.0.0", port=FLASK_PORT) 