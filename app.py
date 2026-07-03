import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# 1. 설정
st.set_page_config(page_title="지두방 발주 시스템", layout="centered")

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

# 영수증 생성 함수 (JPG)
def create_receipt_image(restaurant_name, items, total_amount):
    width, height = 500, 350 + (len(items) * 80)
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    font_path = os.path.join(os.path.dirname(__file__), "NanumGothic.ttf")
    
    try:
        font_title = ImageFont.truetype(font_path, 40)
        font_item = ImageFont.truetype(font_path, 25)
        font_total = ImageFont.truetype(font_path, 45)
        font_thanks = ImageFont.truetype(font_path, 20)
    except:
        font_title = font_item = font_total = font_thanks = ImageFont.load_default()

    draw.text((50, 50), restaurant_name, fill="black", font=font_title)
    y = 150
    for item in items:
        draw.text((50, y), f"{item['name']} x {item['qty']}", fill="black", font=font_item)
        draw.text((50, y + 30), f"({item['name_en']})", fill="gray", font=font_item)
        y += 80
    
    draw.text((50, y + 20), "항상 이용해 주셔서 감사합니다.", fill="blue", font=font_thanks)
    draw.text((50, y + 50), f"총 금액: {total_amount:,} THB", fill="red", font=font_total)
    
    buf = io.BytesIO()
    image.save(buf, format='JPEG', quality=95)
    return buf.getvalue()

# 공유 링크 생성 함수
def get_share_links(image_bytes):
    b64_img = base64.b64encode(image_bytes).decode()
    # 주의: 카카오/라인은 웹상에서 직접 파일 전송이 어려워 텍스트나 간편 공유 링크를 활용함
    kakao_link = "https://pf.kakao.com/" # 카카오 채널 등으로 연결 유도
    line_link = "https://line.me/R/"
    return kakao_link, line_link

# 2. 메인 UI
st.image("https://via.placeholder.com/1200x200?text=Jidubang+Order+System", use_column_width=True)
tab1, tab2, tab3, tab4 = st.tabs(["🏠 홈 딜리버리", "📦 도매 주문", "📝 회원가입", "⚙️ 관리자"])

if 'receipt_bytes' not in st.session_state: st.session_state['receipt_bytes'] = None

with tab1:
    st.header("🏠 홈 딜리버리 서비스")
    address = st.text_input("📍 배송지 주소를 먼저 입력하세요", key="addr_home_1")
    if address:
        # (생략: 기존 주문 로직과 동일)
        if st.button("홈 딜리버리 주문 확정", key="btn_home"):
            # ... (주문 저장 로직)
            st.session_state['receipt_bytes'] = create_receipt_image("홈 딜리버리", [], 0) # 예시
            st.rerun()

    if st.session_state['receipt_bytes']:
        st.success("🎉 주문 완료!")
        st.image(st.session_state['receipt_bytes'])
        
        # 공유 버튼
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("💬 카카오톡 공유", "https://pf.kakao.com/")
        with col2:
            st.link_button("📱 라인(LINE) 공유", "https://line.me/R/")

with tab2:
    st.header("📦 도매 주문")
    # ... (로그인 및 주문 로직)
    if st.session_state['receipt_bytes']:
        st.image(st.session_state['receipt_bytes'])
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("💬 카카오톡 공유", "https://pf.kakao.com/")
        with col2:
            st.link_button("📱 라인(LINE) 공유", "https://line.me/R/")

