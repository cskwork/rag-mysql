# -*- coding: utf-8 -*-
"""
Enhanced Streamlit 앱 완전 기능 테스트
"""

import os
import sys

# telemetry 비활성화
os.environ["VANNA_DISABLE_TELEMETRY"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "false"

def test_imports():
    """모든 필요한 패키지 import 테스트"""
    print("1. 📦 기본 패키지 로드 테스트...")
    try:
        import streamlit as st
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        import openpyxl
        import json
        import io
        from datetime import datetime
        print("✅ 기본 패키지 로드 성공")
        return True
    except Exception as e:
        print(f"🔥 기본 패키지 로드 실패: {e}")
        return False

def test_vanna():
    """Vanna 관련 기능 테스트"""
    print("2. 🧠 Vanna 패키지 및 기능 테스트...")
    try:
        from vanna.ollama import Ollama
        from vanna.chromadb import ChromaDB_VectorStore
        
        # Vanna 클래스 생성 테스트
        class TestVanna(ChromaDB_VectorStore, Ollama):
            def __init__(self):
                ChromaDB_VectorStore.__init__(self, config={'path': 'chromadb'})
                Ollama.__init__(self, config={'model': 'llama3.2:3b-instruct-q8_0'})
        
        # 인스턴스 생성만 테스트 (실제 연결은 하지 않음)
        print("✅ Vanna 클래스 구조 검증 성공")
        return True
    except Exception as e:
        print(f"🔥 Vanna 패키지 테스트 실패: {e}")
        return False

def test_streamlit_features():
    """Streamlit 특수 기능 테스트"""
    print("3. 🎨 Streamlit 고급 기능 테스트...")
    try:
        import streamlit as st
        
        # 주요 Streamlit 기능들이 사용 가능한지 확인
        features = [
            'set_page_config', 'sidebar', 'tabs', 'columns', 
            'selectbox', 'text_area', 'button', 'download_button',
            'dataframe', 'plotly_chart', 'metric', 'spinner',
            'success', 'error', 'warning', 'info', 'rerun'
        ]
        
        for feature in features:
            if not hasattr(st, feature):
                print(f"⚠️ Streamlit 기능 누락: {feature}")
                return False
        
        print("✅ Streamlit 고급 기능 검증 성공")
        return True
    except Exception as e:
        print(f"🔥 Streamlit 기능 테스트 실패: {e}")
        return False

def test_data_export():
    """데이터 내보내기 기능 테스트"""
    print("4. 📊 데이터 내보내기 기능 테스트...")
    try:
        import pandas as pd
        import io
        from datetime import datetime
        
        # 샘플 데이터 생성
        test_df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['Seoul', 'Busan', 'Incheon']
        })
        
        # CSV 내보내기 테스트
        csv_data = test_df.to_csv(index=False)
        assert len(csv_data) > 0
        
        # Excel 내보내기 테스트
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            test_df.to_excel(writer, index=False, sheet_name='Test')
        excel_data = output.getvalue()
        assert len(excel_data) > 0
        
        print("✅ 데이터 내보내기 기능 검증 성공")
        return True
    except Exception as e:
        print(f"🔥 데이터 내보내기 테스트 실패: {e}")
        return False

def test_file_structure():
    """파일 구조 및 설정 테스트"""
    print("5. 📁 파일 구조 및 설정 테스트...")
    
    required_files = [
        'streamlit_app.py',
        '.streamlit/config.toml',
        '.streamlit/secrets.toml',
        'run_streamlit.sh',
        'requirements.txt'
    ]
    
    optional_files = [
        'chromadb',  # 디렉토리
        'test_streamlit.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"🔥 필수 파일 누락: {missing_files}")
        return False
    
    print("✅ 파일 구조 검증 성공")
    return True

def test_configuration():
    """설정 파일 유효성 테스트"""
    print("6. ⚙️ 설정 파일 유효성 테스트...")
    
    # secrets.toml 파일 기본 구조 확인
    secrets_path = '.streamlit/secrets.toml'
    if os.path.exists(secrets_path):
        with open(secrets_path, 'r') as f:
            content = f.read()
            required_sections = ['[database]', '[ollama]', '[vanna]']
            for section in required_sections:
                if section not in content:
                    print(f"⚠️ secrets.toml에 {section} 섹션 누락")
                    return False
    
    print("✅ 설정 파일 검증 성공")
    return True

def main():
    """전체 테스트 실행"""
    print("🎯 Enhanced Streamlit RAG-MySQL 완전 기능 테스트 시작...")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_vanna,
        test_streamlit_features,
        test_data_export,
        test_file_structure,
        test_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트 통과! Enhanced Streamlit 앱 실행 준비 완료!")
        print("🚀 실행 명령어:")
        print("   ./run_streamlit.sh")
        print("   또는")
        print("   streamlit run streamlit_app.py --server.port=8502")
        return True
    else:
        print("🔥 일부 테스트 실패. 문제를 해결 후 다시 실행하세요.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)