# -*- coding: utf-8 -*-
"""
Streamlit RAG Frontend for MySQL Database
Custom frontend using Streamlit with Vanna.ai, Ollama, and ChromaDB
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import io

# telemetry 비활성화로 capture() 에러 해결
os.environ["VANNA_DISABLE_TELEMETRY"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "false"

from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore

# --- Streamlit 페이지 설정 ---
st.set_page_config(
    page_title="🎯 RAG-MySQL Chat",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Vanna 설정 (Streamlit용) ---
class StreamlitVanna(ChromaDB_VectorStore, Ollama):
    """
    Streamlit용 사용자 정의 Vanna 클래스
    ChromaDB를 벡터 스토어로, Ollama를 LLM으로 사용
    """
    def __init__(self, config=None):
        # ChromaDB 경로 설정 (기존 데이터 재사용)
        chroma_db_path = "chromadb"
        if not os.path.exists(chroma_db_path):
            os.makedirs(chroma_db_path)
        
        # ChromaDB 설정
        chroma_config = {
            'path': chroma_db_path,
            'anonymized_telemetry': False
        }
        ChromaDB_VectorStore.__init__(self, config=chroma_config)
        
        # Ollama 모델 설정 (Streamlit secrets에서 가져오기)
        ollama_model = st.secrets.get("ollama", {}).get("model", "llama3.2:3b-instruct-q8_0")
        Ollama.__init__(self, config={'model': ollama_model})

@st.cache_resource(ttl=3600)
def setup_vanna():
    """
    Vanna 인스턴스 설정 (1시간 캐시)
    """
    vn = StreamlitVanna()
    
    # 데이터베이스 연결
    try:
        db_config = st.secrets["database"]
        vn.connect_to_mysql(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            dbname=db_config["name"]
        )
        return vn, True
    except Exception as e:
        st.error(f"🔥 데이터베이스 연결 실패: {e}")
        return None, False

def generate_plotly_chart(df, sql_query=""):
    """
    데이터프레임을 기반으로 적절한 Plotly 차트 생성
    """
    if df.empty:
        return None
    
    # 숫자형 컬럼과 문자형 컬럼 분리
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # 차트 타입 결정 로직
    if len(numeric_cols) >= 2:
        # 숫자형 컬럼이 2개 이상: 산점도
        fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], 
                        title=f"{numeric_cols[0]} vs {numeric_cols[1]}")
    elif len(numeric_cols) == 1 and len(categorical_cols) >= 1:
        # 숫자 1개 + 카테고리 1개: 막대 차트
        fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0],
                    title=f"{numeric_cols[0]} by {categorical_cols[0]}")
    elif len(numeric_cols) == 1:
        # 숫자형 컬럼 1개: 히스토그램
        fig = px.histogram(df, x=numeric_cols[0],
                          title=f"Distribution of {numeric_cols[0]}")
    elif len(categorical_cols) >= 1:
        # 카테고리만 있는 경우: 카운트 차트
        value_counts = df[categorical_cols[0]].value_counts()
        fig = px.bar(x=value_counts.index, y=value_counts.values,
                    title=f"Count of {categorical_cols[0]}")
    else:
        # 기본: 간단한 테이블 표시
        return None
    
    fig.update_layout(
        template="plotly_white",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def display_sql_result(df, query):
    """
    SQL 결과를 표시하고 시각화
    """
    if df is not None and not df.empty:
        st.subheader("📊 쿼리 결과")
        
        # 기본 정보 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("레코드 수", len(df))
        with col2:
            st.metric("컬럼 수", len(df.columns))
        with col3:
            st.metric("실행 시간", "< 1초")
        
        # 데이터 테이블 표시
        st.dataframe(df, use_container_width=True)
        
        # 차트 생성 및 표시
        fig = generate_plotly_chart(df, query)
        if fig:
            st.subheader("📈 데이터 시각화")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("쿼리 결과가 비어있습니다.")

def training_data_management_page(vn):
    """
    훈련 데이터 관리 페이지
    """
    st.header("🎓 훈련 데이터 관리")
    
    # 탭으로 기능 분리
    tab1, tab2, tab3, tab4 = st.tabs(["📊 현재 데이터", "➕ 데이터 추가", "🗑️ 데이터 삭제", "📋 훈련 계획"])
    
    with tab1:
        st.subheader("현재 훈련 데이터 조회")
        try:
            training_data = vn.get_training_data()
            if training_data is not None and len(training_data) > 0:
                st.dataframe(training_data, use_container_width=True)
                st.info(f"총 {len(training_data)}개의 훈련 데이터가 있습니다.")
            else:
                st.warning("아직 훈련 데이터가 없습니다.")
        except Exception as e:
            st.error(f"훈련 데이터 조회 실패: {e}")
    
    with tab2:
        st.subheader("새로운 훈련 데이터 추가")
        
        data_type = st.selectbox(
            "데이터 타입 선택:",
            ["DDL (데이터베이스 스키마)", "SQL (쿼리 예시)", "Documentation (비즈니스 문서)"]
        )
        
        if data_type == "DDL (데이터베이스 스키마)":
            ddl_content = st.text_area(
                "DDL 문장 입력:",
                placeholder="CREATE TABLE customers (\n    id INT PRIMARY KEY,\n    name VARCHAR(100),\n    email VARCHAR(255)\n);",
                height=150
            )
            
            if st.button("DDL 추가", type="primary"):
                if ddl_content.strip():
                    try:
                        vn.train(ddl=ddl_content)
                        st.success("✅ DDL이 성공적으로 추가되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"DDL 추가 실패: {e}")
                else:
                    st.warning("DDL 내용을 입력해주세요.")
        
        elif data_type == "SQL (쿼리 예시)":
            sql_content = st.text_area(
                "SQL 쿼리 입력:",
                placeholder="SELECT c.name, COUNT(o.id) as order_count\nFROM customers c\nLEFT JOIN orders o ON c.id = o.customer_id\nGROUP BY c.id, c.name;",
                height=150
            )
            
            if st.button("SQL 추가", type="primary"):
                if sql_content.strip():
                    try:
                        vn.train(sql=sql_content)
                        st.success("✅ SQL이 성공적으로 추가되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"SQL 추가 실패: {e}")
                else:
                    st.warning("SQL 내용을 입력해주세요.")
        
        elif data_type == "Documentation (비즈니스 문서)":
            doc_content = st.text_area(
                "비즈니스 문서 입력:",
                placeholder="고객의 OTIF 점수는 정시 완전 배송률을 의미하며, 주문이 정확한 시간에 완전한 수량으로 배송된 비율을 나타냅니다.",
                height=150
            )
            
            if st.button("문서 추가", type="primary"):
                if doc_content.strip():
                    try:
                        vn.train(documentation=doc_content)
                        st.success("✅ 문서가 성공적으로 추가되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"문서 추가 실패: {e}")
                else:
                    st.warning("문서 내용을 입력해주세요.")
    
    with tab3:
        st.subheader("훈련 데이터 삭제")
        try:
            training_data = vn.get_training_data()
            if training_data is not None and len(training_data) > 0:
                # ID와 내용의 일부를 보여주는 선택박스
                if 'id' in training_data.columns:
                    options = []
                    for _, row in training_data.iterrows():
                        content_preview = str(row.get('content', ''))[:50] + "..." if len(str(row.get('content', ''))) > 50 else str(row.get('content', ''))
                        options.append(f"{row['id']}: {content_preview}")
                    
                    selected = st.selectbox("삭제할 데이터 선택:", options)
                    
                    if st.button("🗑️ 선택된 데이터 삭제", type="secondary"):
                        try:
                            selected_id = selected.split(":")[0]
                            vn.remove_training_data(id=selected_id)
                            st.success(f"✅ ID {selected_id} 데이터가 삭제되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"데이터 삭제 실패: {e}")
                else:
                    st.warning("훈련 데이터에 ID 필드가 없습니다.")
            else:
                st.info("삭제할 훈련 데이터가 없습니다.")
        except Exception as e:
            st.error(f"훈련 데이터 조회 실패: {e}")
    
    with tab4:
        st.subheader("데이터베이스 기반 훈련 계획")
        
        if st.button("📋 정보 스키마 기반 훈련 계획 생성"):
            try:
                with st.spinner("훈련 계획 생성 중..."):
                    # 정보 스키마 조회
                    df_info_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
                    if not df_info_schema.empty:
                        plan = vn.get_training_plan_generic(df_info_schema)
                        st.success("✅ 훈련 계획이 생성되었습니다!")
                        st.json(plan)
                        
                        if st.button("🚀 이 계획으로 훈련 실행"):
                            try:
                                vn.train(plan=plan)
                                st.success("✅ 훈련이 완료되었습니다!")
                            except Exception as e:
                                st.error(f"훈련 실행 실패: {e}")
                    else:
                        st.warning("정보 스키마 데이터를 조회할 수 없습니다.")
            except Exception as e:
                st.error(f"훈련 계획 생성 실패: {e}")

def sample_questions_generator(vn):
    """
    샘플 질문 생성기
    """
    st.subheader("💡 추천 질문들")
    
    # 데이터베이스 기반 샘플 질문 생성
    try:
        db_name = st.secrets["database"]["name"]
        tables_df = vn.run_sql(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{db_name}'")
        
        if not tables_df.empty:
            sample_questions = [
                "모든 테이블의 목록을 보여줘",
                "각 테이블의 레코드 수를 조회해줘",
                f"{tables_df.iloc[0]['TABLE_NAME']} 테이블의 모든 데이터를 보여줘",
                "가장 최근에 추가된 데이터 10개를 보여줘",
                "데이터베이스 스키마 요약을 보여줘"
            ]
            
            if len(tables_df) > 1:
                sample_questions.extend([
                    f"{tables_df.iloc[0]['TABLE_NAME']}와 {tables_df.iloc[1]['TABLE_NAME']} 테이블을 조인해서 보여줘",
                    "테이블 간 관계를 분석해줘"
                ])
            
            # 질문 버튼들
            cols = st.columns(2)
            for i, question in enumerate(sample_questions):
                with cols[i % 2]:
                    if st.button(f"💭 {question}", key=f"sample_q_{i}"):
                        st.session_state.suggested_question = question
            
    except Exception as e:
        st.error(f"샘플 질문 생성 실패: {e}")

def main():
    """
    메인 Streamlit 애플리케이션
    """
    # 헤더
    st.title("🎯 RAG-MySQL Chat Interface")
    st.markdown("자연어로 데이터베이스에 질문하고 SQL 쿼리와 결과를 확인하세요.")
    
    # Vanna 설정
    vn, connection_success = setup_vanna()
    
    if not connection_success:
        st.stop()
    
    # 페이지 네비게이션
    page = st.sidebar.selectbox(
        "페이지 선택:",
        ["💬 채팅", "🎓 훈련 데이터 관리", "🗄️ 스키마 탐색", "⚙️ 설정"]
    )
    
    if page == "💬 채팅":
        chat_interface(vn)
    elif page == "🎓 훈련 데이터 관리":
        training_data_management_page(vn)
    elif page == "🗄️ 스키마 탐색":
        schema_explorer_page(vn)
    elif page == "⚙️ 설정":
        settings_page(vn)

def schema_explorer_page(vn):
    """
    스키마 탐색 페이지
    """
    st.header("🗄️ 데이터베이스 스키마 탐색")
    
    try:
        db_name = st.secrets["database"]["name"]
        
        # 탭으로 기능 분리
        tab1, tab2, tab3 = st.tabs(["📋 테이블 목록", "🔍 테이블 상세", "📊 데이터 샘플"])
        
        with tab1:
            st.subheader("전체 테이블 목록")
            tables_df = vn.run_sql(f"""
                SELECT 
                    TABLE_NAME as '테이블명',
                    TABLE_ROWS as '레코드수',
                    TABLE_COMMENT as '설명'
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{db_name}'
                ORDER BY TABLE_NAME
            """)
            
            if not tables_df.empty:
                st.dataframe(tables_df, use_container_width=True)
                
                # 테이블별 레코드 수 차트
                if 'TABLE_ROWS' in tables_df.columns:
                    fig = px.bar(
                        tables_df, 
                        x='테이블명', 
                        y='레코드수',
                        title="테이블별 레코드 수"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("테이블을 찾을 수 없습니다.")
        
        with tab2:
            st.subheader("테이블 상세 정보")
            tables_df = vn.run_sql(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{db_name}'")
            
            if not tables_df.empty:
                selected_table = st.selectbox(
                    "테이블 선택:",
                    tables_df['TABLE_NAME'].tolist()
                )
                
                if selected_table:
                    # 컬럼 정보
                    columns_df = vn.run_sql(f"""
                        SELECT 
                            COLUMN_NAME as '컬럼명',
                            DATA_TYPE as '데이터타입',
                            IS_NULLABLE as '널허용',
                            COLUMN_DEFAULT as '기본값',
                            COLUMN_COMMENT as '설명'
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA = '{db_name}' AND TABLE_NAME = '{selected_table}'
                        ORDER BY ORDINAL_POSITION
                    """)
                    
                    st.subheader(f"📋 {selected_table} 테이블 구조")
                    st.dataframe(columns_df, use_container_width=True)
                    
                    # 테이블 DDL 조회
                    try:
                        ddl_df = vn.run_sql(f"SHOW CREATE TABLE {selected_table}")
                        if not ddl_df.empty:
                            st.subheader("🔧 DDL 구문")
                            st.code(ddl_df.iloc[0, 1], language="sql")
                    except Exception as e:
                        st.warning(f"DDL 조회 실패: {e}")
        
        with tab3:
            st.subheader("데이터 샘플 조회")
            
            if not tables_df.empty:
                selected_table = st.selectbox(
                    "샘플 조회할 테이블:",
                    tables_df['TABLE_NAME'].tolist(),
                    key="sample_table_select"
                )
                
                sample_size = st.slider("샘플 크기:", 5, 100, 10)
                
                if st.button("📊 샘플 데이터 조회"):
                    try:
                        sample_df = vn.run_sql(f"SELECT * FROM {selected_table} LIMIT {sample_size}")
                        if not sample_df.empty:
                            st.dataframe(sample_df, use_container_width=True)
                            
                            # 다운로드 버튼
                            csv = sample_df.to_csv(index=False)
                            st.download_button(
                                label="📥 CSV 다운로드",
                                data=csv,
                                file_name=f"{selected_table}_sample.csv",
                                mime="text/csv"
                            )
                        else:
                            st.warning("데이터가 없습니다.")
                    except Exception as e:
                        st.error(f"샘플 데이터 조회 실패: {e}")
            
    except Exception as e:
        st.error(f"스키마 탐색 실패: {e}")

def settings_page(vn):
    """
    설정 관리 페이지
    """
    st.header("⚙️ 설정 관리")
    
    # 현재 설정 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 연결 정보")
        try:
            db_config = st.secrets["database"]
            st.info(f"호스트: {db_config['host']}:{db_config['port']}")
            st.info(f"데이터베이스: {db_config['name']}")
            st.info(f"사용자: {db_config['user']}")
        except:
            st.error("데이터베이스 설정 정보를 불러올 수 없습니다.")
    
    with col2:
        st.subheader("🤖 AI 모델 정보")
        try:
            ollama_model = st.secrets.get("ollama", {}).get("model", "알 수 없음")
            st.info(f"Ollama 모델: {ollama_model}")
            
            # 모델 상태 확인
            import requests
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Ollama 서버 연결됨")
                else:
                    st.error("🔥 Ollama 서버 응답 오류")
            except:
                st.error("🔥 Ollama 서버 연결 실패")
                
        except:
            st.error("AI 모델 정보를 불러올 수 없습니다.")
    
    # 권한 설정
    st.subheader("🔐 권한 설정")
    
    llm_data_access = st.secrets.get("vanna", {}).get("allow_llm_to_see_data", True)
    st.info(f"LLM 데이터 접근: {'✅ 허용' if llm_data_access else '❌ 차단'}")
    
    if not llm_data_access:
        st.warning("⚠️ LLM 데이터 접근이 비활성화되어 있습니다. SQL 생성만 가능하며 실행 결과는 표시되지 않습니다.")
    
    # 성능 통계
    st.subheader("📊 성능 통계")
    
    if 'query_count' not in st.session_state:
        st.session_state.query_count = 0
    
    if 'total_queries' not in st.session_state:
        st.session_state.total_queries = 0
        
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("이번 세션 질문 수", st.session_state.query_count)
    with col2:
        st.metric("총 질문 수", st.session_state.total_queries)
    with col3:
        training_data_count = 0
        try:
            training_data = vn.get_training_data()
            if training_data is not None:
                training_data_count = len(training_data)
        except:
            pass
        st.metric("훈련 데이터 수", training_data_count)
    
    # 리셋 버튼
    if st.button("🔄 세션 통계 리셋"):
        st.session_state.query_count = 0
        st.session_state.query_history = []
        st.success("세션 통계가 리셋되었습니다.")
        st.rerun()

def chat_interface(vn):
    """
    채팅 인터페이스 (기존 main 함수 내용)
    """
    
    # 사이드바 - 데이터베이스 정보
    with st.sidebar:
        st.header("🗄️ 데이터베이스 정보")
        
        # 연결 상태
        st.success("✅ MySQL 연결됨")
        
        # 데이터베이스 스키마 정보
        try:
            db_name = st.secrets["database"]["name"]
            st.info(f"📊 데이터베이스: {db_name}")
            
            # 테이블 목록 조회
            tables_df = vn.run_sql(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{db_name}'")
            if not tables_df.empty:
                st.subheader("📋 테이블 목록")
                for table in tables_df['TABLE_NAME']:
                    st.text(f"• {table}")
        except Exception as e:
            st.error(f"스키마 정보 로드 실패: {e}")
        
        # 설정 정보
        st.subheader("⚙️ 설정")
        llm_access = st.secrets.get("vanna", {}).get("allow_llm_to_see_data", True)
        st.text(f"LLM 데이터 접근: {'허용' if llm_access else '차단'}")
        
        # 도움말
        st.subheader("💡 사용 팁")
        st.markdown("""
        **예시 질문들:**
        - "모든 고객 목록을 보여줘"
        - "지난 달 주문 건수는?"
        - "가장 인기 있는 상품 5개"
        - "고객별 총 주문 금액"
        """)
    
    # 샘플 질문 표시
    sample_questions_generator(vn)
    
    # 메인 채팅 인터페이스
    st.subheader("💬 질문하기")
    
    # 제안된 질문 사용
    suggested_question = st.session_state.get('suggested_question', '')
    
    # 질문 입력
    question = st.text_input(
        "데이터베이스에 대해 자연어로 질문하세요:",
        value=suggested_question,
        placeholder="예: 모든 고객의 이름과 이메일을 보여줘",
        key="question_input"
    )
    
    # 제안된 질문 사용 후 초기화
    if suggested_question:
        st.session_state.suggested_question = ''
    
    # 쿼리 실행 버튼
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_query = st.button("🚀 실행", type="primary")
    
    # 질문 처리
    if execute_query and question:
        with st.spinner("🤔 AI가 SQL 쿼리를 생성 중..."):
            try:
                # SQL 생성
                generated_sql = vn.generate_sql(question)
                
                st.subheader("🔍 생성된 SQL 쿼리")
                st.code(generated_sql, language="sql")
                
                # SQL 실행 여부 확인
                col1, col2 = st.columns([1, 4])
                with col1:
                    run_sql = st.button("▶️ SQL 실행", key="run_sql_btn")
                
                # SQL 실행
                if run_sql:
                    # 쿼리 카운터 증가
                    st.session_state.query_count += 1
                    st.session_state.total_queries += 1
                    
                    with st.spinner("📊 쿼리 실행 중..."):
                        try:
                            # LLM 데이터 접근 설정에 따라 쿼리 실행
                            allow_data_access = st.secrets.get("vanna", {}).get("allow_llm_to_see_data", True)
                            
                            if allow_data_access:
                                result_df = vn.run_sql(generated_sql)
                                display_sql_result(result_df, generated_sql)
                                
                                # 피드백 수집 및 자동 학습
                                st.subheader("🎯 결과 피드백")
                                feedback_col1, feedback_col2, feedback_col3 = st.columns(3)
                                
                                with feedback_col1:
                                    if st.button("👍 정확한 결과", key=f"good_{st.session_state.query_count}"):
                                        # 좋은 질문-SQL 쌍을 훈련 데이터로 추가
                                        try:
                                            vn.train(sql=generated_sql)
                                            st.success("✅ 이 쿼리가 훈련 데이터에 추가되었습니다!")
                                            st.info("💡 향후 비슷한 질문에 더 정확한 답변을 제공할 수 있습니다.")
                                        except Exception as e:
                                            st.error(f"훈련 데이터 추가 실패: {e}")
                                
                                with feedback_col2:
                                    if st.button("👎 부정확한 결과", key=f"bad_{st.session_state.query_count}"):
                                        st.warning("피드백이 수집되었습니다. 더 나은 결과를 위해 질문을 다시 표현해보세요.")
                                        
                                        # 개선 제안 표시
                                        st.info("""
                                        💡 **더 나은 결과를 위한 팁:**
                                        - 더 구체적인 컬럼명이나 테이블명 사용
                                        - 원하는 결과의 예시 추가
                                        - 필터 조건을 명확히 명시
                                        """)
                                
                                with feedback_col3:
                                    if st.button("📝 수정해서 학습", key=f"edit_{st.session_state.query_count}"):
                                        st.session_state.show_edit_sql = True
                                
                                # SQL 수정 인터페이스
                                if st.session_state.get('show_edit_sql', False):
                                    st.subheader("✏️ SQL 수정 및 학습")
                                    edited_sql = st.text_area(
                                        "수정된 SQL을 입력하세요:",
                                        value=generated_sql,
                                        height=150,
                                        key=f"edit_sql_{st.session_state.query_count}"
                                    )
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("💾 수정된 SQL로 학습"):
                                            try:
                                                vn.train(sql=edited_sql)
                                                st.success("✅ 수정된 SQL이 훈련 데이터에 추가되었습니다!")
                                                st.session_state.show_edit_sql = False
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"훈련 데이터 추가 실패: {e}")
                                    
                                    with col2:
                                        if st.button("❌ 취소"):
                                            st.session_state.show_edit_sql = False
                                            st.rerun()
                                
                                # 다운로드 옵션
                                if not result_df.empty:
                                    st.subheader("📥 결과 다운로드")
                                    download_col1, download_col2 = st.columns(2)
                                    
                                    with download_col1:
                                        csv = result_df.to_csv(index=False)
                                        st.download_button(
                                            label="📄 CSV 다운로드",
                                            data=csv,
                                            file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                            mime="text/csv"
                                        )
                                    
                                    with download_col2:
                                        # Excel 다운로드
                                        output = io.BytesIO()
                                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                            result_df.to_excel(writer, index=False, sheet_name='Results')
                                        excel_data = output.getvalue()
                                        
                                        st.download_button(
                                            label="📊 Excel 다운로드",
                                            data=excel_data,
                                            file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                        )
                            else:
                                st.warning("⚠️ LLM 데이터 접근이 비활성화되어 있습니다. SQL만 생성됩니다.")
                                
                        except Exception as e:
                            st.error(f"🔥 SQL 실행 오류: {e}")
            
            except Exception as e:
                st.error(f"🔥 SQL 생성 오류: {e}")
                st.info("💡 다른 방식으로 질문해보세요.")
    
    # 히스토리 세션 상태 초기화
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    # 히스토리 표시
    if st.session_state.query_history:
        st.subheader("📝 질문 히스토리")
        for i, (q, sql) in enumerate(reversed(st.session_state.query_history)):
            with st.expander(f"질문 {len(st.session_state.query_history) - i}: {q[:50]}..."):
                st.text(f"질문: {q}")
                st.code(sql, language="sql")
    
    # 질문과 SQL을 히스토리에 추가
    if execute_query and question:
        if question not in [q for q, _ in st.session_state.query_history]:
            try:
                generated_sql = vn.generate_sql(question)
                st.session_state.query_history.append((question, generated_sql))
                # 히스토리는 최대 10개까지 유지
                if len(st.session_state.query_history) > 10:
                    st.session_state.query_history.pop(0)
            except:
                pass  # 실패시 히스토리에 추가하지 않음

    # 푸터
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        🎯 RAG-MySQL Chat Interface | Powered by Vanna.ai + Ollama + ChromaDB + Streamlit
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()