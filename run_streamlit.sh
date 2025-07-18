#!/bin/bash

# Streamlit RAG-MySQL App 실행 스크립트
# Custom Streamlit frontend for RAG-MySQL project

echo "🎯 RAG-MySQL Streamlit App 시작 중..."

# 가상환경 활성화
echo "📦 가상환경 활성화..."
source venv/bin/activate

# 필요한 패키지 확인
echo "🔍 필요한 패키지 확인 중..."
python -c "import streamlit, plotly, vanna" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️ 필요한 패키지가 설치되지 않았습니다. 설치 중..."
    pip install streamlit plotly
fi

# Ollama 서버 확인
echo "🤖 Ollama 서버 상태 확인..."
curl -s http://localhost:11434/api/tags > /dev/null
if [ $? -ne 0 ]; then
    echo "🔥 Ollama 서버가 실행되지 않고 있습니다."
    echo "💡 다음 명령으로 Ollama를 시작하세요: ollama serve"
    exit 1
fi

# ChromaDB 디렉토리 확인
if [ ! -d "chromadb" ]; then
    echo "⚠️ ChromaDB 디렉토리가 없습니다. 기존 Flask 앱으로 훈련을 먼저 실행하세요."
    echo "💡 훈련 명령: python app.py --train-hybrid"
fi

# Secrets 파일 확인
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "🔥 Streamlit secrets 파일이 없습니다."
    echo "💡 .streamlit/secrets.toml 파일을 확인하고 데이터베이스 설정을 완료하세요."
    exit 1
fi

echo "🚀 Streamlit 앱 시작..."
echo "📱 브라우저에서 http://localhost:8502 에 접속하세요"
echo "🛑 종료하려면 Ctrl+C를 눌러주세요"
echo ""

streamlit run streamlit_app.py --server.port=8502 --server.headless=false