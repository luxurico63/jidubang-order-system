import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# 1. 설정 및 구글 시트 연결
st.set_page_config(page_title="지두방 발주 시스템", layout="wide")

def get_sheet():
    creds_dict = dict(st.secrets["gcp"])
    if 'private_key' in creds_dict:
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("jidubang_db")

db = get_sheet()
sheet_products = db.sheet1
sheet_users = db.worksheet("회원정보")
sheet_orders = db.worksheet("주문내역")

# 2. 탭 구성
tab1, tab2, tab3 = st.tabs(["🏠 홈 딜리버리", "📦 도매 주문", "📝 회원가입"])

with tab2:
    st.header("📦 도매 상품 발주")
    if 'logged_in' not in st.session_state:
        st.info("도매 주문을 위해 로그인이 필요합니다.")
        login_name = st.text_input("식당 이름", key="login_name")
        login_phone = st.text_input("전화번호 뒷번호", key="login_phone")
        
        if st.button("로그인", key="btn_login"):
            users = sheet_users.get_all_records()
            # 디버깅: 현재 시트에 저장된 데이터 출력
            st.write("시트에 저장된 회원 목록:", users) 
            
            # 입력값과 시트 값 비교 (strip()을 써서 공백 제거)
            user_info = next((u for u in users if u['이름'].strip() == login_name.strip() and str(u['전화번호']).strip() == login_phone.strip()), None)
            
            if user_info:
                st.session_state['logged_in'] = True
                st.session_state['user'] = login_name
                st.session_state['address'] = user_info['주소']
                st.rerun()
            else:
                st.error("입력한 정보와 일치하는 가입자가 없습니다.")
    else:
        st.success(f"환영합니다, **{st.session_state['user']}**님!")
        if st.button("로그아웃", key="btn_logout"):
            del st.session_state['logged_in']
            st.rerun()
