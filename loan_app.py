"""
房貸試算工具 - 主程式入口
"""
import streamlit as st

from modules.config import PAGES
from modules.session import init_form_state, K_NAV
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
    /* 頁面導覽（radio）看起來更像頁籤 */
    div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 10px;
        margin-bottom: 10px;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        font-size: 15px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)


def main():
    inject_css()
    init_form_state()

    st.markdown("<h1 class='main-title'>🏠 房貸試算工具</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>支援寬限期、多階段利率、額外還款、多方案比較</p>", unsafe_allow_html=True)

    # 導覽（用 radio 才能用程式切換頁面，例如從「我的方案」載入編輯後跳回試算頁）
    page = st.radio("頁面導覽", PAGES, horizontal=True, key=K_NAV, label_visibility="collapsed")

    if page == PAGES[0]:
        render_single_calc()
    elif page == PAGES[1]:
        render_compare()
    else:
        render_saved_schemes()


if __name__ == "__main__":
    main()
