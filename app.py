import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# 1. 설정 및 구글 시트 연결 함수
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
sheet_products = db.sheet1  # 상품 시트 (name, name_en, price_wholesale, price_retail 순서)
sheet_users = db.worksheet("회원정보")
sheet_orders = db.worksheet("주문내역")

# 2. 배너 및 탭 구성
st.image("https://via.placeholder.com/1200x200?text=Jidubang+Order+System", use_column_width=True)

tab1, tab2 = st.tabs(["🏠 홈 딜리버리", "🔑 회원가입/로그인"])

# 3. 회원가입/로그인 탭
with tab2:
    mode = st.radio("모드 선택", ["로그인", "회원가입"])
    if mode == "회원가입":
        st.subheader("식당 회원가입")
        rest_name = st.text_input("식당 이름")
        phone_last = st.text_input("대표전화 뒷번호 4자리")
        address = st.text_input("식당 주소")
        if st.button("가입 완료"):
            sheet_users.append_row([rest_name, phone_last, address])
            st.success(f"{rest_name}님 가입 완료!")
    else:
        st.subheader("로그인")
        login_name = st.text_input("식당 이름")
        login_phone = st.text_input("전화번호 뒷번호")
        if st.button("로그인"):
            st.session_state['logged_in'] = True
            st.session_state['user'] = login_name
            st.success("로그인 성공!")

# 4. 홈 딜리버리 탭 (주문 로직)
with tab1:
    st.header("도매 상품 발주")
    if 'logged_in' not in st.session_state:
        st.warning("로그인 후 이용 가능합니다.")
    else:
        data = sheet_products.get_all_records()
        address = st.text_input("📍 배송지 주소")
        
        selected_items = []
        total_price = 0
        
        for row in data:
            name = row['name']
            name_en = row['name_en'] # 영문 이름 불러오기
            price = int(row['price_wholesale'])
            
            # 상품명 옆에 영문 이름도 같이 표시
            st.write(f"### {name} ({name_en}) - {price} THB")
            qty = st.number_input(f"{name} 수량", min_value=0, step=1, key=name)
            
            if qty > 0:
                selected_items.append({"name": name, "qty": qty, "price": price})
                total_price += price * qty
        
        if total_price > 0:
            st.markdown(f"<h1 style='color:red;'>총 금액: {total_price:,} THB</h1>", unsafe_allow_html=True)
            if st.button("주문 확정하기"):
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                item_str = ", ".join([f"{i['name']} {i['qty']}개" for i in selected_items])
                sheet_orders.append_row([now, address, item_str, total_price])
                st.success("🎉 주문이 완료되었습니다!")
