import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
from PIL import Image, ImageDraw, ImageFont
import io

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

# 2. 영수증 생성 함수
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

# 3. 주문 폼 함수 (텍스트 크기 확대)
def display_order_form(is_wholesale):
    data = sheet_products.get_all_records()
    cats = {}
    for row in data:
        cat = row.get('category', '기타')
        if cat not in cats: cats[cat] = []
        cats[cat].append(row)
    
    cat_tabs = st.tabs(list(cats.keys()))
    total_price = 0
    selected_items = []
    
    for i, cat in enumerate(cats.keys()):
        with cat_tabs[i]:
            for row in cats[cat]:
                name, name_en, img_path = row['name'], row['name_en'], row.get('image_path', '')
                price = int(row['price_wholesale']) if is_wholesale else int(row['price_retail'])
                
                # 가독성을 위해 크기 확대
                if img_path: st.image(img_path, use_column_width=True)
                st.markdown(f"### {name}")
                st.markdown(f"#### {name_en} / {price} THB")
                
                qty = st.number_input(f"수량 입력", min_value=0, step=1, value=0, key=f"{'w_' if is_wholesale else 'r_'}{name}")
                
                if qty > 0:
                    selected_items.append({"name": name, "name_en": name_en, "qty": int(qty), "price": price})
                    total_price += price * int(qty)
                st.divider()
    return selected_items, total_price

# 4. 메인 UI
st.image("https://via.placeholder.com/1200x200?text=Jidubang+Order+System", use_column_width=True)
tab1, tab2, tab3, tab4 = st.tabs(["🏠 홈 딜리버리", "📦 도매 주문", "📝 회원가입", "⚙️ 관리자"])

if 'receipt_bytes' not in st.session_state: st.session_state['receipt_bytes'] = None
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

with tab1:
    st.markdown("# 🏠 홈 딜리버리 서비스")
    address = st.text_input("📍 배송지 주소", key="addr_home_1")
    if address:
        items, total = display_order_form(False)
        if total > 0:
            delivery_fee = 100 if total < 800 else (50 if total < 1500 else 0)
            final_total = total + delivery_fee
            st.markdown(f"## **총 결제 금액: {final_total:,} THB**")
            if st.button("홈 딜리버리 주문 확정", key="btn_home"):
                sheet_orders.append_row([get_current_time(), address, ", ".join([f"{i['name']} {i['qty']}개" for i in items]), final_total, "홈딜리버리"])
                st.session_state['receipt_bytes'] = create_receipt_image("홈 딜리버리", items, final_total)
                st.rerun()
    if st.session_state['receipt_bytes']:
        st.success("🎉 주문 완료!")
        st.image(st.session_state['receipt_bytes'])
        st.download_button("📥 이미지 저장 및 공유하기", data=st.session_state['receipt_bytes'], file_name="주문영수증_홈.jpg", mime="image/jpeg", key="dl_home")

with tab2:
    st.markdown("# 📦 도매 주문")
    if not st.session_state['logged_in']:
        with st.form("login_form"):
            login_name = st.text_input("식당 이름")
            login_phone = st.text_input("전화번호 뒷번호")
            if st.form_submit_button("로그인"):
                all_users = sheet_users.get_all_values()[1:]
                user_info = next((u for u in all_users if u[0].strip() == login_name.strip() and u[1].strip() == login_phone.strip()), None)
                if user_info and user_info[3] == "승인":
                    st.session_state['logged_in'] = True; st.session_state['user'] = login_name
                    st.rerun()
                else: st.error("정보 불일치 혹은 승인 대기 중")
    else:
        st.write(f"## 환영합니다, **{st.session_state['user']}**님!")
        if st.button("로그아웃"): st.session_state['logged_in'] = False; st.rerun()
        items, total = display_order_form(True)
        if total > 0:
            st.markdown(f"## **총 금액: {total:,} THB**")
            if st.button("도매 주문 확정", key="btn_wholesale"):
                sheet_orders.append_row([get_current_time(), st.session_state['user'], ", ".join([f"{i['name']} {i['qty']}개" for i in items]), total, "도매"])
                st.session_state['receipt_bytes'] = create_receipt_image(st.session_state['user'], items, total)
                st.rerun()
        if st.session_state['receipt_bytes']:
            st.image(st.session_state['receipt_bytes'])
            st.download_button("📥 이미지 저장 및 공유하기", data=st.session_state['receipt_bytes'], file_name="주문영수증_도매.jpg", mime="image/jpeg", key="dl_wholesale")

# ... (tab3, 4 동일)
