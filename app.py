import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
from PIL import Image, ImageDraw, ImageFont
import io

# 1. 설정 및 탭별 맞춤 사이즈 CSS
st.set_page_config(page_title="지두방 발주 시스템", layout="centered")

st.markdown("""
    <style>
    /* 1번(홈 딜리버리), 2번(도매 주문) 탭 크기 및 글씨 조정 (30% 축소) */
    button[data-baseweb="tab"]:nth-child(1),
    button[data-baseweb="tab"]:nth-child(2) {
        height: 70px !important;
        padding: 0 20px !important;
    }
    
    button[data-baseweb="tab"]:nth-child(1) div p,
    button[data-baseweb="tab"]:nth-child(2) div p {
        font-size: 25px !important;
        font-weight: bold !important;
    }
    
    /* 선택된 탭 텍스트 색상 포인트 */
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
        font_date = ImageFont.truetype(font_path, 25)
        font_item = ImageFont.truetype(font_path, 25)
        font_total = ImageFont.truetype(font_path, 45)
        font_thanks = ImageFont.truetype(font_path, 20)
    except:
        font_title = font_date = font_item = font_total = font_thanks = ImageFont.load_default()
        
    draw.text((50, 50), restaurant_name, fill="black", font=font_title)
    draw.text((50, 100), datetime.datetime.now().strftime("%y/%m/%d"), fill="gray", font=font_date)
    
    y = 180
    for item in items:
        draw.text((50, y), f"{item['name']} x {item['qty']}", fill="black", font=font_item)
        draw.text((50, y + 30), f"({item['name_en']})", fill="gray", font=font_item)
        y += 80
        
    draw.text((50, y + 20), "항상 이용해 주셔서 감사합니다.", fill="blue", font=font_thanks)
    draw.text((50, y + 50), f"총 금액: {total_amount:,} THB", fill="red", font=font_total)
    
    buf = io.BytesIO()
    image.save(buf, format='JPEG', quality=95)
    return buf.getvalue()

def get_current_time(): 
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def display_order_form(is_wholesale):
    data = sheet_products.get_all_records()
    cats = {}
    for row in data:
        cat = row.get('category', '기타')
        if cat not in cats: cats[cat] = []
        cats[cat].append(row)
        
    cat_tabs = st.tabs(list(cats.keys()))
    selected_items = []
    total_price = 0
    
    for i, cat in enumerate(cats.keys()):
        with cat_tabs[i]:
            for row in cats[cat]:
                name = row['name']
                name_en = row['name_en']
                img_path = row.get('image_path', '')
                price = int(row['price_wholesale']) if is_wholesale else int(row['price_retail'])
                
                if img_path: 
                    st.image(img_path, use_column_width=True)
                    
                qty = st.number_input(f"{name} 수량", min_value=0, step=1, value=0, key=f"{'w_' if is_wholesale else 'r_'}{name}")
                if qty > 0:
                    selected_items.append({"name": name, "name_en": name_en, "qty": int(qty), "price": price})
                    total_price += price * int(qty)
                st.divider()
                
    return selected_items, total_price

# 3. 메인 UI
st.image("https://via.placeholder.com/1200x200?text=Jidubang+Order+System", use_column_width=True)
tab1, tab2, tab3, tab4 = st.tabs(["🏠 홈 딜리버리", "📦 도매 주문", "📝 회원가입", "⚙️ 관리자"])

if 'receipt_bytes' not in st.session_state: 
    st.session_state['receipt_bytes'] = None
if 'logged_in' not in st.session_state: 
    st.session_state['logged_in'] = False

with tab1:
    address = st.text_input("📍 배송지 주소", key="addr_home_1")
    if address:
        items, total = display_order_form(False)
        if total > 0 and st.button("홈 딜리버리 주문 확정", key="btn_home"):
            item_str = ", ".join([f"{i['name']} {i['qty']}개" for i in items])
            sheet_orders.append_row([get_current_time(), address, item_str, total, "홈딜리버리"])
            st.session_state['receipt_bytes'] = create_receipt_image("홈 딜리버리", items, total)
            st.rerun()
            
    if st.session_state['receipt_bytes']:
        st.image(st.session_state['receipt_bytes'])
        st.download_button(
            label="📥 이미지 저장", 
            data=st.session_state['receipt_bytes'], 
            file_name="주문.jpg", 
            mime="image/jpeg", 
            key="dl_home"
        )

with tab2:
    if not st.session_state['logged_in']:
        with st.form("login_form"):
            login_name = st.text_input("식당 이름")
            login_phone = st.text_input("전화번호 뒷번호")
            if st.form_submit_button("로그인"):
                all_users = sheet_users.get_all_values()[1:]
                user_info = next((u for u in all_users if u[0].strip() == login_name.strip() and u[1].strip() == login_phone.strip()), None)
                if user_info and user_info[3] == "승인":
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = login_name
                    st.rerun()
    else:
