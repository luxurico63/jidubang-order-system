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
        # 기존의 '주문 확정하기' 버튼 로직 부분을 아래 코드로 교체하세요
# 기존 '주문 확정하기' 버튼 로직 부분 (들여쓰기 주의!)
    if st.button("주문 확정하기"):
        # 1. '주문내역' 시트 불러오기
        try:
            order_sheet = get_sheet().spreadsheet.worksheet("주문내역")
        except:
            order_sheet = get_sheet().spreadsheet.add_worksheet(title="주문내역", rows="100", cols="4")
            order_sheet.append_row(["날짜", "배송지", "상품목록", "총금액"])

        # 2. 주문 정보 가공
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 상품목록을 한 문장으로 만들기
        item_list_str = ", ".join([f"{item['name']} {item['qty']}개" for item in selected_items])
        
        # 3. 한 행에 데이터 합쳐서 저장
        order_sheet.append_row([
            now, 
            address, 
            item_list_str, 
            subtotal_cost
        ])
    
        # 들여쓰기를 if문 안쪽으로 맞춰야 해!
        st.success(f"🎉 주문이 접수되었습니다!")
        st.balloons()


else:
    st.info("👆 주소를 입력하면 상품 목록이 나타납니다.")
