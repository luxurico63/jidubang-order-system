import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
from PIL import Image, ImageDraw, ImageFont
import io

# 1. 설정
st.set_page_config(page_title="지두방 발주 시스템", layout="centered")

# 탭 안의 글자만 키우는 CSS
big_text_css = """
    <style>
    .big-font {
        font-size: 60px !important;
        font-weight: bold !important;
    }
    .big-label {
        font-size: 30px !important;
    }
    </style>
"""

# ... (중략: get_sheet, create_receipt_image, display_order_form 함수 동일)

# 4. 메인 UI
st.image("https://via.placeholder.com/1200x200?text=Jidubang+Order+System", use_column_width=True)
tab1, tab2, tab3, tab4 = st.tabs(["🏠 홈 딜리버리", "📦 도매 주문", "📝 회원가입", "⚙️ 관리자"])

with tab1:
    st.markdown(big_text_css, unsafe_allow_html=True)
    st.markdown('<p class="big-font">🏠 홈 딜리버리 서비스</p>', unsafe_allow_html=True)
    
    # 입력창 라벨을 크게 표시하기 위해 label_visibility를 사용하거나 커스텀 텍스트 사용
    address = st.text_input("배송지 주소", key="addr_home_1")
    # ... 나머지 로직 동일

with tab2:
    st.markdown(big_text_css, unsafe_allow_html=True)
    st.markdown('<p class="big-font">📦 도매 주문</p>', unsafe_allow_html=True)
    # ... 나머지 로직 동일
