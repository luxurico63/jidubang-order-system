import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. 연결 설정
def get_sheet():
    creds_dict = dict(st.secrets["gcp"])
    if 'private_key' in creds_dict:
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("jidubang_db").sheet1

# 2. 메인 로직
st.title("📦 지두방 구글 시트 연동 시스템")

# 데이터 불러오기 (캐싱을 사용하여 매번 시트를 열지 않게 최적화)
@st.cache_data(ttl=60)
# [수정] ttl=0으로 설정해서, 새로고침할 때마다 구글 시트를 다시 읽게 함
@st.cache_data(ttl=0) 
def load_data():
    sheet = get_sheet()
    return sheet.get_all_records()

data = load_data()

# 3. 화면 구현
address = st.text_input("📍 배송지 주소를 입력하고 엔터를 누르세요")

# 주소가 입력되었을 때만 상품 목록 표시
if address:
    st.success(f"배송지 확인: {address}")
    
    subtotal_cost = 0
    selected_items = []
    
    for row in data:
        name = row.get('name', '상품')
        # [수정] price를 숫자로 강제 변환 (문자라면 숫자로 바꿔줌)
        price_str = row.get('price_delivery', 0)
        price = int(price_str) if str(price_str).isdigit() else 0
        
        st.write(f"### {name} ({price} THB)")
        qty = st.number_input(f"{name} 수량", min_value=0, value=0, step=1, key=f"qty_{name}")
        
        if qty > 0:
            selected_items.append({"name": name, "price": price, "qty": qty})
            subtotal_cost += price * qty
        st.divider()
    
    if subtotal_cost > 0:
        st.write(f"## 총 금액: {subtotal_cost:,} THB")
        if st.button("주문 확정하기"):
            st.success(f"{address}로 {subtotal_cost} THB 주문 완료!")
else:
    st.info("👆 주소를 입력하면 상품 목록이 나타납니다.")
