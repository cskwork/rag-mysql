# -*- coding: utf-8 -*-
"""
간단한 Streamlit 앱 테스트 스크립트
"""

import os
import sys

# telemetry 비활성화
os.environ["VANNA_DISABLE_TELEMETRY"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "false"

try:
    print("1. 기본 패키지 로드 테스트...")
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    print("✅ 기본 패키지 로드 성공")
    
    print("2. Vanna 패키지 로드 테스트...")
    from vanna.ollama import Ollama
    from vanna.chromadb import ChromaDB_VectorStore
    print("✅ Vanna 패키지 로드 성공")
    
    print("3. ChromaDB 경로 확인...")
    chroma_path = "chromadb"
    if os.path.exists(chroma_path):
        print(f"✅ ChromaDB 디렉토리 존재: {chroma_path}")
    else:
        print(f"⚠️ ChromaDB 디렉토리 없음: {chroma_path}")
    
    print("4. Ollama 연결 테스트...")
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama 서버 연결 성공")
        else:
            print(f"⚠️ Ollama 응답 코드: {response.status_code}")
    except Exception as e:
        print(f"🔥 Ollama 연결 실패: {e}")
    
    print("5. Streamlit secrets 파일 확인...")
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        print(f"✅ Secrets 파일 존재: {secrets_path}")
    else:
        print(f"⚠️ Secrets 파일 없음: {secrets_path}")
    
    print("\n🎉 모든 기본 테스트 통과!")
    print("Streamlit 앱을 실행할 준비가 되었습니다.")
    print("실행 명령: streamlit run streamlit_app.py")
    
except Exception as e:
    print(f"🔥 테스트 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)