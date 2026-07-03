import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# 1. 모바일 최적화 설정
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

def get_products_by_category(data):
    cats = {}
    for row in data:
        cat = row.get('category', '기타')
        if cat not in cats: cats[cat] = []
        cats[cat].append(row)
    return cats

def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# 모바일 대응: 상품을 세로로 쌓아서 보여주는 UI
def display_order_form(is_wholesale):
    data = sheet_products.get_all_records()
    cats = get_products_by_category(data)
    cat_tabs = st.tabs(list(cats.keys()))
    
    total_price = 0
    selected_items = []
    
    for i, cat in enumerate(cats.keys()):
        with cat_tabs[i]:
            for row in cats[cat]:
                name, name_en, img_path = row['name'], row['name_en'], row.get('image_path', '')
                price = int(row['price_wholesale']) if is_wholesale else int(row['price_retail'])
                
                # 모바일에서는 세로로 쌓이도록 컬럼 분할 제거 또는 조정
                if img_path: st.image(img_path, use_column_width=True)
                st.write(f"### {name}")
                st.write(f"{name_en} / {price} THB")
                
                qty_input = st.text_input(f"{name} 수량", value="", key=f"{'w_' if is_wholesale else 'r_'}{name}")
                try:
                    qty = int(qty_input) if qty_input else 0
                except:
                    qty = 0
                
                if qty > 0:
                    selected_items.append({"name": name, "qty": qty, "price": price})
                    total_price += price * qty
                st.divider() # 상품 간 구분선 추가
    return selected_items, total_price

# 2. 배너 및 탭
st.image("https://via.placeholder.com/1200x200?text=Jidubang+Order+System", use_column_width=True)
tab1, tab2, tab3, tab4 = st.tabs(["🏠 홈", "📦 도매", "📝 가입", "⚙️ 관리"])

with tab1:
    st.header("🏠 홈 딜리버리")
    address = st.text_input("📍 배송지 주소", key="addr_home_1")
    if address:
        items, total = display_order_form(False)
        if total > 0:
            delivery_fee = 100 if total < 800 else (50 if total < 1500 else 0)
            st.markdown(f"**총 결제: {total + delivery_fee:,} THB**")
            if st.button("주문 확정", key="btn_home"):
                sheet_orders.append_row([get_current_time(), address, ", ".join([f"{i['name']} {i['qty']}개" for i in items]), total + delivery_fee, "홈딜리버리"])
                st.success("완료!")
    else:
        st.info("주소를 입력하면 상품이 나타납니다.")

with tab2:
    st.header("📦 도매 주문")
    if 'logged_in' not in st.session_state:
        with st.form("login_form"):
            login_name = st.text_input("식당 이름")
            login_phone = st.text_input("전화번호 뒷번호")
            if st.form_submit_button("로그인"):
                all_users = sheet_users.get_all_values()[1:]
                user_info = next((u for u in all_users if u[0].strip() == login_name.strip() and u[1].strip() == login_phone.strip()), None)
                if user_info and len(user_info) >= 4 and user_info[3] == "승인":
                    st.session_state['logged_in'] = True; st.session_state['user'] = login_name
                    st.session_state['address'] = user_info[2]; st.rerun()
                else: st.error("승인 대기 중이거나 정보가 일치하지 않습니다.")
    else:
        st.write(f"환영합니다, **{st.session_state['user']}**님!")
        items, total = display_order_form(True)
        if total > 0:
            st.markdown(f"**총 결제: {total:,} THB**")
            if st.button("주문 확정", key="btn_wholesale"):
                sheet_orders.append_row([get_current_time(), st.session_state['user'], ", ".join([f"{i['name']} {i['qty']}개" for i in items]), total, "도매"])
                st.success("완료!")

with tab3:
    st.header("📝 가입 신청")
    rest_name = st.text_input("식당 이름"); phone = st.text_input("전화번호 뒷번호"); addr = st.text_input("주소")
    if st.button("가입 신청"):
        sheet_users.append_row([rest_name, phone, addr, "대기"]); st.success("신청 완료!")

with tab4:
    st.header("⚙️ 관리자")
    admin_pw = st.text_input("비밀번호", type="password")
    if admin_pw == "4419":
        for i, row in enumerate(sheet_users.get_all_values()[1:], start=2):
            if st.button(f"{row[0]} 승인", key=f"app_{i}"): sheet_users.update_cell(i, 4, "승인"); st.rerun()

            
