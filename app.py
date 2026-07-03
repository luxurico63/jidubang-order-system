import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# [핵심 수정] Secrets를 사용하여 구글 시트 연결
def get_sheet():
    # Streamlit Cloud의 Secrets에 저장된 정보를 딕셔너리로 가져옴
    creds_dict = st.secrets["gcp"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 딕셔너리 형태로 인증 (파일을 열지 않음!)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # 여기서 "jidubang_db"는 네가 만든 구글 시트 파일 이름
    return client.open("jidubang_db").sheet1 

sheet = get_sheet()

st.set_page_config(page_title="지두방 발주 시스템", layout="centered")

st.title("📦 지두방 구글 시트 연동 시스템")

# 데이터 불러오기
data = sheet.get_all_records()

# 주문 페이지 구현
address = st.text_input("배송지 주소")

selected_items = []
subtotal_cost = 0

for row in data:
    name = row['name']
    price = row['price_delivery']
    
    st.write(f"### {name} ({price} THB)")
    col1, col2 = st.columns([1, 1])
    with col1:
        qty = st.number_input(f"{name} 수량", min_value=0, value=0, step=1, key=name)
    
    if qty > 0:
        selected_items.append({"name": name, "price": price, "qty": qty})
        subtotal_cost += price * qty
    st.divider()

if subtotal_cost > 0:
    st.write(f"## 총 금액: {subtotal_cost:,} THB")
    if st.button("주문 확정하기"):
        st.success(f"{address}로 {subtotal_cost} THB 주문 완료!")
