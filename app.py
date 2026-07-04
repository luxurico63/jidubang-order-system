import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
from PIL import Image, ImageDraw, ImageFont
import io

# 1. 설정 및 탭 사이즈 대폭 확대 CSS
st.set_page_config(page_title="지두방 발주 시스템", layout="centered")

st.markdown("""
    <style>
    /* 탭 헤더 영역 크기 강제 확대 */
    button[data-baseweb="tab"] {
        height: 100px !important;
        padding: 0 40px !important;
    }
    
    /* 탭 내부 텍스트 크기 강제 확대 */
    button[data-baseweb="tab"] div p {
        font-size: 35px !important;
        font-weight: bold !important;
    }
    
    /* 선택된 탭 텍스트 색상 변경 (옵션) */
    button[data-baseweb="tab"][aria-selected="true"] div p {
        color: #FF4B4B !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

# 2. 영수증 생성 및 유틸리티 함수들
def create_receipt_image(restaurant_name, items, total_amount):
    width, height = 500, 400 + (len(items) * 80)
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    font_path = os.path.join(os.path.dirname(__file__), "NanumGothic.ttf")
    try:
        font_title = ImageFont.truetype(font_path, 40)
        font_date = ImageFont.truetype(font_path,
