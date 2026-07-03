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

# 상품 데이터를 카테고리별로 나누는 함수
def get_products_by_category(data):
    cats = {}
    for row in data:
        cat = row.get('category', '기타')
        if cat not in cats: cats[cat] = []
        cats[cat].append(row)
    return cats

# 2. 배너 및 탭 구성
st.image("https://via.placeholder.com/1200x200?text=Jidubang+Order+System", use_column_width=True)

tab1, tab2, tab3, tab4 = st.tabs(["🏠 홈 딜리버리", "📦 도매 주문", "📝 회원가입", "⚙️ 관리자"])

# --- 공통 주문 UI 함수 ---
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

# --- 1. 홈 딜리버리 ---
with tab1:
    st.header("🏠 홈 딜리버리 서비스")
    address = st.text_input("📍 배송지 주소를 입력하세요", key="addr_home_1")
    items, total = display_order_form(False)
    
    if total > 0:
        st.subheader(f"총 금액: {total:,} THB")
        if st.button("홈 딜리버리 주문 확정", key="btn_home"):
            item_str = ", ".join([f"{i['name']} {i['qty']}개" for i in items])
            sheet_orders.append_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), address, item_str, total, "홈딜리버리"])
            st.success("🎉 주문 완료!")

# --- 2. 도매 주문 ---
with tab2:
    st.header("📦 도매 상품 발주")
    if 'logged_in' not in st.session_state:
        st.info("로그인이 필요합니다.")
        login_name = st.text_input("식당 이름", key="login_name")
        login_phone = st.text_input("전화번호 뒷번호", key="login_phone")
        if st.button("로그인", key="btn_login"):
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
        address = st.text_input("📍 배송지 주소", value=st.session_state.get('address', ''), key="addr_wholesale_1")
        items, total = display_order_form(True)
        if total > 0:
            st.markdown(f"<h1 style='color:red;'>총 금액: {total:,} THB</h1>", unsafe_allow_html=True)
            if st.button("도매 주문 확정", key="btn_wholesale"):
                item_str = ", ".join([f"{i['name']} {i['qty']}개" for i in items])
                sheet_orders.append_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), address, item_str, total, "도매"])
                st.success("🎉 주문 완료!")

# --- 3, 4번 탭 (회원가입, 관리자)은 이전과 동일하므로 생략 (위 코드에 추가해서 완성해) ---
