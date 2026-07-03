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
sheet_users = get_or_create_worksheet(db, "회원정보", ["이름", "전화번호", "주소", "승인여부"])
sheet_orders = get_or_create_worksheet(db, "주문내역", ["날짜", "배송지", "상품목록", "총금액", "주문유형"])

# 카테고리 분리 함수
def get_products_by_category(data):
    cats = {}
    for row in data:
        cat = row.get('category', '기타')
        if cat not in cats: cats[cat] = []
        cats[cat].append(row)
    return cats

# 상품 주문 UI 함수
def display_order_form(is_wholesale):
    data = sheet_products.get_all_records()
    cats = get_products_by_category(data)
    cat_tabs = st.tabs(list(cats.keys()))
    
    total_price = 0
    selected_items = []
    
    for i, cat in enumerate(cats.keys()):
        with cat_tabs[i]:
            for row in cats[cat]:
                name, name_en = row['name'], row['name_en']
                price = int(row['price_wholesale']) if is_wholesale else int(row['price_retail'])
                
                st.write(f"### {name} ({name_en}) - {price} THB")
                qty = st.number_input(f"{name} 수량", min_value=0, step=1, key=f"{'w_' if is_wholesale else 'r_'}{name}")
                if qty > 0:
                    selected_items.append({"name": name, "qty": qty, "price": price})
                    total_price += price * qty
    return selected_items, total_price

# 2. 배너 및 탭 구성
st.image("https://via.placeholder.com/1200x200?text=Jidubang+Order+System", use_column_width=True)

tab1, tab2, tab3, tab4 = st.tabs(["🏠 홈 딜리버리", "📦 도매 주문", "📝 회원가입", "⚙️ 관리자"])

# --- 1. 홈 딜리버리 ---
with tab1:
    st.header("🏠 홈 딜리버리 서비스")
    address = st.text_input("📍 배송지 주소를 입력하세요", key="addr_home_1")
    items, total = display_order_form(False)
    
    if total > 0:
        st.subheader(f"총 금액: {total:,} THB")
        if st.button("홈 딜리버리 주문 확정", key="btn_home"):
            sheet_orders.append_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), address, ", ".join([f"{i['name']} {i['qty']}개" for i in items]), total, "홈딜리버리"])
            st.success("🎉 주문 완료!")

# --- 2. 도매 주문 ---
with tab2:
    st.header("📦 도매 상품 발주")
    if 'logged_in' not in st.session_state:
        st.info("도매 주문을 위해 로그인이 필요합니다.")
        # [수정] 폼으로 감싸서 엔터 키 작동하게 함
        with st.form("login_form"):
            login_name = st.text_input("식당 이름")
            login_phone = st.text_input("전화번호 뒷번호")
            submit_button = st.form_submit_button("로그인")
            
            if submit_button:
                all_users = sheet_users.get_all_values()[1:]
                user_info = next((u for u in all_users if u[0].strip() == login_name.strip() and u[1].strip() == login_phone.strip()), None)
                if user_info and len(user_info) >= 4 and user_info[3] == "승인":
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = login_name
                    st.session_state['address'] = user_info[2]
                    st.rerun()
                else:
                    st.error("가입 정보가 없거나 승인 대기 중입니다.")
    else:
        st.success(f"환영합니다, **{st.session_state['user']}**님!")
        if st.button("로그아웃", key="btn_logout"):
            del st.session_state['logged_in']
            st.rerun()
        address = st.text_input("📍 배송지 주소", value=st.session_state.get('address', ''), key="addr_wholesale_1")
        items, total = display_order_form(True)
        if total > 0:
            st.markdown(f"<h1 style='color:red;'>총 금액: {total:,} THB</h1>", unsafe_allow_html=True)
            if st.button("도매 주문 확정", key="btn_wholesale"):
                sheet_orders.append_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), address, ", ".join([f"{i['name']} {i['qty']}개" for i in items]), total, "도매"])
                st.success("🎉 주문 완료!")

# --- 3, 4번 탭 (회원가입, 관리자) ---
with tab3:
    st.header("📝 식당 회원가입")
    rest_name = st.text_input("식당 이름", key="signup_name")
    phone = st.text_input("전화번호 뒷번호", key="signup_phone")
    addr = st.text_input("주소", key="signup_addr")
    if st.button("가입 신청하기", key="btn_signup"):
        sheet_users.append_row([rest_name, phone, addr, "대기"])
        st.success("가입 신청 완료!")

with tab4:
    st.header("⚙️ 관리자 승인")
    admin_pw = st.text_input("관리자 비밀번호", type="password", key="admin_pw")
    if admin_pw == "4419":
        users_data = sheet_users.get_all_values()
        for i, row in enumerate(users_data[1:], start=2):
            col1, col2, col3, col4 = st.columns(4)
            col1.write(row[0]); col2.write(row[1])
            if col3.button(f"승인하기", key=f"approve_{i}"):
                sheet_users.update_cell(i, 4, "승인")
                st.rerun()
            col4.write(row[3] if len(row) > 3 else "대기")
