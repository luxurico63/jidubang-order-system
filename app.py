import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# 구글 시트 연결 설정
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    return client.open("jidubang_db").sheet1  # 시트 이름이 jidubang_db인 파일의 첫 번째 시트

sheet = get_sheet()

st.set_page_config(page_title="지두방 발주 시스템", layout="centered")

st.title("📦 지두방 구글 시트 연동 시스템")

# 1. 데이터 불러오기 (상품 목록)
data = sheet.get_all_records()
# 데이터 예시: [{"name": "김치", "price_delivery": 200}, ...]

# 2. 주문 페이지 구현
address = st.text_input("배송지 주소")

selected_items = []
subtotal_cost = 0 # 에러 방지를 위해 초기화

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
        # 여기서 주문 내역을 구글 시트의 다른 시트에 저장하거나 메일로 발송 가능
        st.success(f"{address}로 {subtotal_cost} THB 주문 완료!")
