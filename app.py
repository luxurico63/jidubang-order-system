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

def get_or_create_worksheet(db, title, headers):
    try:
        return db.worksheet(title)
    except:
        ws = db.add_worksheet(title=title, rows="100", cols=len(headers))
        ws.append_row(headers)
        return ws

sheet_products = db.sheet1
sheet_users = get_or_create_worksheet(db, "회원정보", ["이름", "전화번호", "주소"])
sheet_orders = get_or_create_worksheet(db, "주문내역", ["날짜", "배송지", "상품목록", "총금액", "주문유형"])

# 2. 배너 및 탭 구성
st.image("https://via.placeholder.com/1200x200?text=Jidubang+Order+System", use_column_width=True)

tab1, tab2, tab3 = st.tabs(["🏠 홈 딜리버리", "📦 도매 주문", "📝 회원가입"])

# --- 1. 홈 딜리버리 ---
with tab1:
    st.header("🏠 홈 딜리버리 서비스")
    data = sheet_products.get_all_records()
    address = st.text_input("📍 배송지 주소를 입력하세요", key="addr_home")
    
    total_price = 0
    selected_items = []
    
    for row in data:
        name, name_en, price = row['name'], row['name_en'], int(row['price_retail'])
        st.write(f"### {name} ({name_en}) - {price} THB")
        qty = st.number_input(f"{name} 수량", min_value=0, step=1, key=f"retail_{name}")
        if qty > 0:
            selected_items.append({"name": name, "qty": qty, "price": price})
            total_price += price * qty
            
    if total_price > 0:
        st.subheader(f"총 금액: {total_price:,} THB")
        if st.button("홈 딜리버리 주문 확정"):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            item_str = ", ".join([f"{i['name']} {i['qty']}개" for i in selected_items])
            sheet_orders.append_row([now, address, item_str, total_price, "홈딜리버리"])
            st.success("🎉 홈 딜리버리 주문 완료!")

# --- 2. 도매 주문 (로그인 시 주소 자동 로딩) ---
with tab2:
    st.header("📦 도매 상품 발주")
    if 'logged_in' not in st.session_state:
        st.info("도매 주문을 위해 로그인이 필요합니다.")
        login_name = st.text_input("식당 이름")
        login_phone = st.text_input("전화번호 뒤 4자리")
        if st.button("로그인"):
            users = sheet_users.get_all_records()
            # 식당 이름과 전화번호로 회원 확인
            user_info = next((u for u in users if u['이름'] == login_name and u['전화번호'] == login_phone), None)
            if user_info:
                st.session_state['logged_in'] = True
                st.session_state['user'] = login_name
                st.session_state['address'] = user_info['주소']
                st.rerun()
            else:
                st.error("가입된 정보가 없습니다.")
    else:
        st.success(f"환영합니다, **{st.session_state['user']}**님!")
        if st.button("로그아웃"):
            del st.session_state['logged_in']
            st.rerun()
            
        data = sheet_products.get_all_records()
        # 로그인 시 저장된 주소를 기본값으로 설정
        address = st.text_input("📍 배송지 주소", value=st.session_state.get('address', ''))
        
        total_price = 0
        selected_items = []
        for row in data:
            name, name_en, price = row['name'], row['name_en'], int(row['price_wholesale'])
            st.write(f"### {name} ({name_en}) - {price} THB")
            qty = st.number_input(f"{name} 도매 수량", min_value=0, step=1, key=f"wholesale_{name}")
            if qty > 0:
                selected_items.append({"name": name, "qty": qty, "price": price})
                total_price += price * qty
        
        if total_price > 0:
            st.markdown(f"<h1 style='color:red;'>총 금액: {total_price:,} THB</h1>", unsafe_allow_html=True)
            if st.button("도매 주문 확정"):
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                item_str = ", ".join([f"{i['name']} {i['qty']}개" for i in selected_items])
                sheet_orders.append_row([now, address, item_str, total_price, "도매"])
                st.success("🎉 도매 주문 완료!")

# --- 3. 회원가입 ---
with tab3:
    st.header("📝 식당 회원가입")
    rest_name = st.text_input("식당 이름")
    phone = st.text_input("전화번호 뒷번호 (4자리)")
    addr = st.text_input("주소")
    if st.button("가입 신청하기"):
        sheet_users.append_row([rest_name, phone, addr])
        st.success("가입 신청이 완료되었습니다!")
