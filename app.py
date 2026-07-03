# ... (앞부분 동일)

# --- 1. 홈 딜리버리 탭 내 버튼 ---
    if st.session_state['receipt_bytes']:
        st.success("🎉 주문 완료!")
        st.image(st.session_state['receipt_bytes'])
        # 수정: key 추가
        st.download_button("📥 이미지 저장 및 공유하기", data=st.session_state['receipt_bytes'], file_name="주문영수증_홈.jpg", mime="image/jpeg", key="dl_home")

with tab2:
    # ... (생략)
        if st.session_state['receipt_bytes']:
            st.success("🎉 주문 완료!")
            st.image(st.session_state['receipt_bytes'])
            # 수정: key 추가 (홈과 다르게 설정)
            st.download_button("📥 이미지 저장 및 공유하기", data=st.session_state['receipt_bytes'], file_name="주문영수증_도매.jpg", mime="image/jpeg", key="dl_wholesale")

# ... (나머지 동일)

