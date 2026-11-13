"""
房貸試算工具 - 主程式入口
"""
import sys

import streamlit as st


def _reload_local_modules():
    """清掉本專案 modules/* 的匯入快取

    Streamlit（含 Community Cloud）重新部署時只會重跑主程式，
    先前 import 過的 modules/* 還留在 sys.modules，裡面是舊版程式碼，
    於是新增的常數/函式會找不到，例如：
        ImportError: cannot import name 'PAGES' from 'modules.config'
    清掉快取後重新 import，就能拿到最新程式碼（不必手動 Reboot app）。
    """
    for name in [m for m in list(sys.modules) if m == "modules" or m.startswith("modules.")]:
        del sys.modules[name]


def _import_app_modules():
    """匯入頁面需要的模組（集中一處，方便失敗時整批重載）"""
    from modules.config import PAGES
    from modules.session import init_form_state, K_NAV
    from modules.sections.single_calc import render_single_calc
    from modules.sections.compare import render_compare
    from modules.sections.saved import render_saved_schemes

    return PAGES, init_form_state, K_NAV, render_single_calc, render_compare, render_saved_schemes


try:
    PAGES, init_form_state, K_NAV, render_single_calc, render_compare, render_saved_schemes = _import_app_modules()
except ImportError:
    # 拿到舊的模組快取（部署後常見），清掉後重新載入一次
    _reload_local_modules()
    PAGES, init_form_state, K_NAV, render_single_calc, render_compare, render_saved_schemes = _import_app_modules()



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
