import streamlit as st
import sqlite3
import os
from PIL import Image, ImageDraw, ImageFont

# 1. 화면 설정
st.set_page_config(page_title="지두방 발주 시스템", layout="centered")

# CSS 스타일 정의
st.markdown("""
    <style>
    img {
        border-radius: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .receipt-box {
        background-color: #ffffff;
        padding: 25px;
        border: 2px dashed #111111;
        border-radius: 5px;
        color: #111111;
        font-family: 'Courier New', Courier, monospace;
        margin-bottom: 20px;
    }
    .receipt-title {
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        margin-top: 5px;
        margin-bottom: 5px;
        color: #000000;
    }
    .receipt-total {
        font-size: 26px;
        font-weight: bold;
        text-align: right;
        color: #FF4B4B;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# DB 및 폴더 설정
DB_FILE = "orders_app.db"
IMG_DIR = "saved_images"
BANNER_DIR = "saved_banner"

for folder in [IMG_DIR, BANNER_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_en TEXT,
            price_normal INTEGER NOT NULL,
            price_delivery INTEGER DEFAULT 0,
            image_path TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_name TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            address TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_products():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 도매 가격(price_normal)과 소매 가격(price_delivery)을 둘 다 가져옴
    cursor.execute("SELECT id, name, name_en, price_normal, price_delivery, image_path FROM products")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "name_en": r[2] if r[2] else "", "price_normal": r[3], "price_delivery": r[4], "image_path": r[5]} for r in rows]

# 배송비가 포함된 영수증 이미지 생성 함수
# [개선] 품목이 아무리 많아도 절대 잘리지 않고 아래로 길어지는 영수증 생성 함수
# [개선] 상·하단에 넉넉한 여백을 추가하여 짤림을 방지하고 디자인을 개선한 영수증 함수
def create_receipt_image(title, address, items, subtotal, delivery_fee, total):
    img_w = 500
    # 기본 세로 길이에 상하단 여백 버퍼를 더 늘려줍니다 (340px -> 400px)
    img_h = 400 + (len(items) * 55)
    
    img = Image.new('RGB', (img_w, img_h), color='#FFFFFF')
    d = ImageDraw.Draw(img)
    
    font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
    try:
        title_font = ImageFont.truetype(font_path, 24)
        subtitle_font = ImageFont.truetype(font_path, 14)
        body_font = ImageFont.truetype(font_path, 16)
        total_font = ImageFont.truetype(font_path, 22)
    except IOError:
        title_font = subtitle_font = body_font = total_font = ImageFont.load_default()
    
    # 테두리 박스 (외곽선)
    d.rectangle([(10, 10), (img_w-10, img_h-10)], outline='#111111', width=3)
    
    # [변경] 상단 여백 확보: y좌표를 기존 45에서 70으로 내려서 시작
    d.text((img_w//2, 70), title, fill='#000000', font=title_font, anchor="mm")
    d.text((img_w//2, 105), "JiDuBang Order System", fill='#777777', font=subtitle_font, anchor="mm")
    
    # 구분선 및 주소 위치도 상단 여백에 맞춰 아래로 이동
    d.line([(20, 130), (img_w-20, 130)], fill='#111111', width=2)
    d.text((25, 140), f"배송 주소: {address}", fill='#111111', font=body_font)
    d.line([(20, 170), (img_w-20, 170)], fill='#111111', width=2)
    
    # 상품 내역 시작 위치 조정
    current_y = 195
    for item in items:
        item_text = f"- {item['name']} ({item['qty']}개)"
        price_text = f"{item['price']*item['qty']:,} THB"
        d.text((25, current_y), item_text, fill='#111111', font=body_font)
        d.text((img_w-25, current_y), price_text, fill='#111111', font=body_font, anchor="ra")
        current_y += 55
        
    d.line([(20, current_y), (img_w-20, current_y)], fill='#111111', width=1)
    
    # 정산 내역 배치
    current_y += 25
    d.text((25, current_y), "주문 상품 금액:", fill='#555555', font=body_font)
    d.text((img_w-25, current_y), f"{subtotal:,} THB", fill='#555555', font=body_font, anchor="ra")
    
    current_y += 35
    d.text((25, current_y), "배송비:", fill='#555555', font=body_font)
    delivery_text = f"+{delivery_fee:,} THB" if delivery_fee > 0 else "무료"
    d.text((img_w-25, current_y), delivery_text, fill='#555555', font=body_font, anchor="ra")
    
    current_y += 35
    d.line([(20, current_y), (img_w-20, current_y)], fill='#111111', width=2)
    
    # [변경] 하단 결제 금액 출력 후 아래쪽에 충분한 바닥 여백이 남도록 조절됨
    d.text((img_w-25, current_y + 25), f"최종 결제 금액: {total:,} THB", fill='#FF4B4B', font=total_font, anchor="ra")
    
    temp_path = "temp_receipt.png"
    img.save(temp_path)
    return temp_path

if "current_page" not in st.session_state:
    st.session_state.current_page = "main"
if "receipt_data" not in st.session_state:
    st.session_state.receipt_data = None
if "logged_in_restaurant" not in st.session_state:
    st.session_state.logged_in_restaurant = None

def get_main_banner():
    banner_file = os.path.join(BANNER_DIR, "main_banner.png")
    return banner_file if os.path.exists(banner_file) else None

if st.session_state.current_page != "main":
    if st.button("⬅️ 메인 화면으로 돌아가기"):
        st.session_state.current_page = "main"
        st.session_state.receipt_data = None
        st.rerun()
    st.divider()

# [1] 메인 선택 화면
if st.session_state.current_page == "main":
    banner_path = get_main_banner()
    if banner_path:
        st.image(banner_path, use_container_width=True)
    st.title("💻 지두방 발주 시스템")
    st.subheader("원하시는 서비스를 선택해 주세요")
    
    if st.button("🔐 도매 매장 / 관리자 로그인", use_container_width=True):
        st.session_state.current_page = "login"
        st.rerun()
    if st.button("📝 신규 도매 회원가입", use_container_width=True):
        st.session_state.current_page = "register"
        st.rerun()
    if st.button("🛵 홈 딜리버리 주문 (치앙마이 한정)", use_container_width=True):
        st.session_state.current_page = "delivery_page"
        st.rerun()

# [2] 도매 회원가입 화면
elif st.session_state.current_page == "register":
    st.title("📝 도매 회원가입")
    reg_name = st.text_input("업체명 / 식당 이름")
    reg_pw = st.text_input("비밀번호 설정", type="password")
    reg_pw_confirm = st.text_input("비밀번호 확인", type="password")
    reg_address = st.text_area("배송지 상세 주소")
    
    if st.button("도매 회원가입 완료하기", use_container_width=True):
        if reg_name and reg_pw and reg_pw_confirm and reg_address:
            if reg_pw != reg_pw_confirm:
                st.error("⚠️ 비밀번호가 일치하지 않습니다.")
            else:
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (restaurant_name, password, address) VALUES (?, ?, ?)", (reg_name, reg_pw, reg_address))
                    conn.commit()
                    conn.close()
                    st.success("🎉 가입 완료! 로그인해 주세요.")
                    st.session_state.current_page = "login"
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("⚠️ 이미 존재하는 업체명입니다.")

# [3] 로그인 화면
elif st.session_state.current_page == "login":
    st.title("🔐 로그인")
    user_id = st.text_input("업체명 (또는 admin)")
    user_pw = st.text_input("비밀번호", type="password")
    
    if st.button("로그인", use_container_width=True):
        if user_id == "admin" and user_pw == "1234":
            st.session_state.current_page = "admin_page"
            st.rerun()
        elif user_id and user_pw:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT restaurant_name, address FROM users WHERE restaurant_name = ? AND password = ?", (user_id, user_pw))
            user_match = cursor.fetchone()
            conn.close()
            if user_match:
                st.session_state.logged_in_restaurant = {"name": user_match[0], "address": user_match[1]}
                st.session_state.current_page = "user_page"
                st.rerun()
            else:
                st.error("❌ 정보가 올바르지 않습니다.")

# [4] 관리자 모드 (도매가 / 소매가 별도 입력 구조 복구)
elif st.session_state.current_page == "admin_page":
    st.title("🛠️ 지두방 관리자 모드")
    with st.expander("🖼️ 메인 화면 대문 배너 이미지 관리", expanded=True):
        current_banner = get_main_banner()
        if current_banner:
            st.image(current_banner, caption="현재 배너", use_container_width=True)
            if st.button("🗑️ 배너 삭제하기", use_container_width=True):
                os.remove(current_banner)
                st.rerun()
        uploaded_banner = st.file_uploader("새 배너 업로드", type=["jpg", "jpeg", "png"])
        if st.button("💾 메인 배너로 지정하기", use_container_width=True) and uploaded_banner:
            Image.open(uploaded_banner).save(os.path.join(BANNER_DIR, "main_banner.png"))
            st.rerun()

    st.subheader("🆕 새 상품 등록하기")
    new_name = st.text_input("상품 이름 (한글)")
    new_name_en = st.text_input("상품 이름 (영어)")
    new_price_n = st.number_input("📦 도매 매장용 가격 (THB)", min_value=0, step=10)
    new_price_d = st.number_input("🛵 일반 소매(홈딜리버리)용 가격 (THB)", min_value=0, step=10)
    uploaded_file = st.file_uploader("상품 사진 업로드", type=["jpg", "jpeg", "png"])
    
    if st.button("➕ 상품 등록하기", use_container_width=True) and new_name and uploaded_file:
        img_path = os.path.join(IMG_DIR, f"{new_name}_{uploaded_file.name}")
        Image.open(uploaded_file).save(img_path)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, name_en, price_normal, price_delivery, image_path) VALUES (?, ?, ?, ?, ?)", (new_name, new_name_en, new_price_n, new_price_d, img_path))
        conn.commit()
        conn.close()
        st.success("상품 등록 성공!")
        st.rerun()

# [5] 도매 회원 전용 발주 페이지 (도매가 적용)
elif st.session_state.current_page == "user_page":
    rest_info = st.session_state.logged_in_restaurant
    st.title(f"📦 {rest_info['name']} 도매 발주")
    
    db_products = get_products()
    selected_items = []
    total_cost = 0
    
    for p in db_products:
        if p["image_path"] and os.path.exists(p["image_path"]):
            st.image(p["image_path"], use_container_width=True)
        st.markdown(f"### 🛍️ {p['name']} ({p['name_en']})")
        st.markdown(f"#### 💰 도매 가격: **{p['price_normal']:,} THB**")
        checked = st.checkbox("선택", key=f"check_n_{p['id']}")
        quantity = st.number_input("수량", min_value=1, value=1, key=f"qty_n_{p['id']}")
        if checked:
            selected_items.append({"name": p["name"], "price": p["price_normal"], "qty": quantity})
            total_cost += p["price_normal"] * quantity
        st.divider()
        
    st.markdown(f"## 💵 총 금액: **{total_cost:,} THB**")
    
    if st.button("발주 완료 및 영수증 발행", use_container_width=True) and selected_items:
        qr_file = create_receipt_image(rest_info['name'], rest_info['address'], selected_items, total_cost, 0, total_cost)
        st.session_state.receipt_data = qr_file
        
    if st.session_state.receipt_data:
        st.success("🎉 영수증 이미지가 성공적으로 발행되었습니다!")
        st.info("💡 아래 이미지를 꾹~ 누르면 [사진 저장] 또는 [카카오톡 전송]을 바로 하실 수 있습니다.")
        st.image(st.session_state.receipt_data, use_container_width=True)

# [6] 🛵 홈 딜리버리 전용 페이지 (소매가 적용 + 금액별 배송비 차등 로직 결합)
# [6] 🛵 홈 딜리버리 전용 페이지 (상시 배송비 안내 박스 추가!)
elif st.session_state.current_page == "delivery_page":
    st.title("🛵 치앙마이 홈 딜리버리 (소매 주문)")
    
    # --- [추가] 상시 배송비 안내 가이드 박스 ---
    st.markdown("""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #FF4B4B; margin-bottom: 20px;">
            <h4 style="margin-top:0; color:#111111;">🚚 지두방 홈 딜리버리 배송비 안내</h4>
            <p style="margin: 4px 0; font-size: 14px; color:#333333;">• <b>800 THB 미만 구매 시:</b> 배송비 100 THB</p>
            <p style="margin: 4px 0; font-size: 14px; color:#333333;">• <b>800 THB 이상 구매 시:</b> 배송비 50 THB <span style="color:#FF4B4B; font-weight:bold;">(🛒 추천)</span></p>
            <p style="margin: 4px 0; font-size: 14px; color:#333333;">• <b>1,500 THB 이상 구매 시:</b> <span style="color:green; font-weight:bold;">배송비 무료 🔥</span></p>
        </div>
    """, unsafe_allow_html=True)
    
    address = st.text_input("📍 배송받으실 치앙마이 상세 주소를 입력하세요")
    
    if address:
        db_products = get_products()
        selected_items = []
        subtotal_cost = 0  # 소매가 기준의 상품 순수 합계 금액
        
        for p in db_products:
            if p["image_path"] and os.path.exists(p["image_path"]):
                st.image(p["image_path"], use_container_width=True)
            st.markdown(f"### 🛍️ {p['name']} ({p['name_en']})")
            st.markdown(f"#### 💰 판매 가격: **{p['price_delivery']:,} THB**")
            checked = st.checkbox("선택", key=f"check_d_{p['id']}")
            quantity = st.number_input("수량", min_value=1, value=1, key=f"qty_d_{p['id']}")
            if checked:
                selected_items.append({"name": p["name"], "price": p["price_delivery"], "qty": quantity})
                subtotal_cost += p["price_delivery"] * quantity
            st.divider()
            
        if subtotal_cost > 0:
            # --- 금액별 배송비 계산 로직 ---
            if subtotal_cost >= 1500:
                delivery_fee = 0
                status_msg = "🎉 **1,500 THB 이상 구매로 배송비 무료 적용!**"
            elif subtotal_cost >= 800:
                delivery_fee = 50
                remains = 1500 - subtotal_cost
                status_msg = f"💡 **배송비 50 THB 적용** ({remains:,} THB 더 담으면 무료 배송!)"
            else:
                delivery_fee = 100
                remains = 800 - subtotal_cost
                status_msg = f"⚠️ **배송비 100 THB 적용** ({remains:,} THB 더 담으면 배송비 50 THB로 할인!)"
                
            final_total = subtotal_cost + delivery_fee
            
            st.markdown(f"### 📦 상품 금액: {subtotal_cost:,} THB")
            st.markdown(f"### 🚚 배송비: {'무료' if delivery_fee == 0 else f'{delivery_fee} THB'}")
            st.info(status_msg)
            st.markdown(f"## 💵 최종 결제 금액: **{final_total:,} THB**")
            
            if st.button("딜리버리 주문 완료 및 영수증 발행", use_container_width=True) and selected_items:
                qr_file = create_receipt_image("HOME DELIVERY", address, selected_items, subtotal_cost, delivery_fee, final_total)
                st.session_state.receipt_data = qr_file
                
            if st.session_state.receipt_data:
                st.success("🎉 영수증 이미지가 성공적으로 발행되었습니다!")
                st.info("💡 아래 이미지를 꾹~ 누르면 [사진 저장] 또는 [카카오톡 전송]을 바로 하실 수 있습니다.")
                st.image(st.session_state.receipt_data, use_container_width=True)


            
# [7] 자동 QR코드 생성기
import socket
def get_internal_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

mac_ip = get_internal_ip()
st.divider()
st.subheader("📱 스마트폰 테스트용 QR코드")
st.caption(f"현재 맥북의 접속 주소: http://{mac_ip}:8501")
qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=http://{mac_ip}:8501"
st.image(qr_api_url, width=250)

