"""
房貸試算工具 - 主程式入口
"""
import streamlit as st

from modules.sections.single_calc import render_single_calc
from modules.sections.compare import render_compare
from modules.sections.saved import render_saved_schemes


# 頁面設定
st.set_page_config(
    page_title="房貸試算工具",
    page_icon="🏠",
    layout="wide"
)


def inject_css():
    st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: rgba(151, 166, 195, 0.15) !important;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(151, 166, 195, 0.2);
    }
    .main-title {
        text-align: center;
        color: #1a365d;
        margin-bottom: 5px;
    }
    .subtitle {
        text-align: center;
        color: gray;
        margin-bottom: 25px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)


def main():
    inject_css()

    st.markdown("<h1 class='main-title'>🏠 房貸試算工具</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>支援寬限期、多階段利率、額外還款、多方案比較</p>", unsafe_allow_html=True)

    # 分頁
    tab1, tab2, tab3 = st.tabs(["🧮 單一方案", "⚖️ 多方案比較", "💾 我的方案"])

    with tab1:
        render_single_calc()
    with tab2:
        render_compare()
    with tab3:
        render_saved_schemes()


if __name__ == "__main__":
    main()
