"""
已存方案管理區塊
"""
import streamlit as st
import pandas as pd
from modules.storage import load_schemes, delete_scheme, parse_config, parse_summary


def render_saved_schemes():
    """已儲存的方案管理"""
    st.markdown("### 💾 我的方案")

    df = load_schemes()
    if df.empty:
        st.info("尚無已儲存的方案。到「單一方案」頁面計算後，即可儲存到雲端！")
        return

    st.caption(f"共 {len(df)} 個方案")

    for _, row in df.iterrows():
        with st.expander(f"📌 {row['name']}　—　{row['created_at']}", expanded=False):
            config = parse_config(row["config"])
            summary = parse_summary(row["result_summary"])

            c1, c2, c3 = st.columns(3)
            c1.metric("總利息", f"{summary.get('total_interest', 0):,.0f} 元")
            c2.metric("總還款", f"{summary.get('total_payment', 0):,.0f} 元")
            c3.metric("還款期數", f"{summary.get('months_taken', 0)} 期")

            st.markdown("**方案設定：**")
            st.markdown(f"""
            - 貸款總額：**{config.get('principal', 0):,.0f} 萬元**
            - 貸款年限：**{config.get('years', 0)} 年**
            - 寬限期：**{config.get('grace_years', 0)} 年**
            - 利率方案：**{config.get('rate_type', '-')}**
            - 還款方式：**{config.get('repayment_type', '本息均攤')}**
            """)

            extra = config.get("extra_repayments", [])
            if extra:
                st.markdown("**額外還款：**")
                for er in extra:
                    st.markdown(f"- 第 {er['year']} 年第 {er.get('month', 1)} 個月：**{er['amount']/10000:,.1f} 萬元**")

            if summary.get("saved_interest", 0) > 0:
                st.success(f"🎉 因提前還款省下利息：**{summary['saved_interest']:,.0f} 元**")

            if st.button("🗑️ 刪除此方案", key=f"del_{row['id']}"):
                if delete_scheme(row["id"]):
                    st.success("已刪除！")
                    st.rerun()
