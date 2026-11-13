"""
表單狀態管理

集中管理輸入欄位在 st.session_state 中的 key，並提供：
- init_form_state(): 第一次進入頁面時填入預設值
- apply_config_to_state(): 將已儲存的方案載入回輸入欄位（繼續編輯用）
- reset_form(): 回到預設值（取消編輯）
- is_editing() / current_edit_id() / current_edit_name()

注意：
apply_config_to_state() 與 reset_form() 會修改 widget 的 session_state，
必須放在 widget 的 on_click callback 中呼叫（callback 會在下一輪 script
執行前先跑），否則會遇到 Streamlit 的
"cannot be modified after the widget is instantiated" 錯誤。
"""
import streamlit as st

from modules.config import DEFAULTS, PAGES, RATE_TYPES, REPAYMENT_TYPES

# ============================================================
# 輸入欄位的 session_state key
# ============================================================
K_PRINCIPAL = "in_principal"
K_YEARS = "in_years"
K_GRACE = "in_grace"
K_REPAYMENT = "in_repayment"
K_RATE_TYPE = "in_rate_type"
K_SINGLE_RATE = "in_single_rate"
K_RATE1 = "in_rate1"
K_STAGE1_YEARS = "in_stage1_years"
K_RATE2 = "in_rate2"
K_STAGE2_YEARS = "in_stage2_years"
K_RATE3 = "in_rate3"
K_EXTRA = "extra_repayments"
K_SCHEME_NAME = "scheme_name_input"

# ============================================================
# 導覽 / 編輯狀態
# ============================================================
K_NAV = "nav"
K_EDIT_ID = "edit_scheme_id"
K_EDIT_NAME = "edit_scheme_name"
K_AUTO_CALC = "auto_calc_flag"

# 額外還款列專用的 widget key 前綴（載入新方案時要清掉舊值）
_EXTRA_WIDGET_PREFIXES = ("er_year_", "er_month_", "er_amt_", "er_del_")


def _defaults() -> dict:
    """所有輸入欄位的預設值"""
    return {
        K_PRINCIPAL: float(DEFAULTS["principal"]),
        K_YEARS: int(DEFAULTS["years"]),
        K_GRACE: float(DEFAULTS["grace_years"]),
        K_REPAYMENT: REPAYMENT_TYPES[0],
        K_RATE_TYPE: RATE_TYPES[0],
        K_SINGLE_RATE: float(DEFAULTS["single_rate"]),
        K_RATE1: float(DEFAULTS["rate1"]),
        K_STAGE1_YEARS: int(DEFAULTS["stage1_years"]),
        K_RATE2: float(DEFAULTS["rate2"]),
        K_STAGE2_YEARS: 3,
        K_RATE3: float(DEFAULTS["rate2"]),
        K_SCHEME_NAME: "",
    }


def _clear_extra_widget_keys():
    """清掉額外還款列上殘留的 widget state"""
    for key in list(st.session_state.keys()):
        if str(key).startswith(_EXTRA_WIDGET_PREFIXES):
            st.session_state.pop(key, None)


def _clear_result():
    """清掉上一次的計算結果，避免顯示到別的方案的數字"""
    st.session_state.pop("last_result", None)
    st.session_state.pop("last_config", None)


def init_form_state():
    """確保所有輸入欄位都有初始值（只補缺的，不覆蓋使用者輸入）"""
    for key, value in _defaults().items():
        if key not in st.session_state:
            st.session_state[key] = value

    if K_EXTRA not in st.session_state:
        st.session_state[K_EXTRA] = []
    if K_NAV not in st.session_state:
        st.session_state[K_NAV] = PAGES[0]


def apply_config_to_state(config: dict, scheme_id: str = None, scheme_name: str = None):
    """把已儲存的方案設定載入到輸入欄位（請在 button callback 中呼叫）"""
    config = config or {}
    rate_config = config.get("rate_config") or {}

    rate_type = config.get("rate_type", RATE_TYPES[0])
    if rate_type not in RATE_TYPES:
        rate_type = RATE_TYPES[0]

    repayment_type = config.get("repayment_type", REPAYMENT_TYPES[0])
    if repayment_type not in REPAYMENT_TYPES:
        repayment_type = REPAYMENT_TYPES[0]

    # 基本設定
    st.session_state[K_PRINCIPAL] = float(config.get("principal", DEFAULTS["principal"]))
    st.session_state[K_YEARS] = int(config.get("years", DEFAULTS["years"]))
    st.session_state[K_GRACE] = float(config.get("grace_years", DEFAULTS["grace_years"]))
    st.session_state[K_REPAYMENT] = repayment_type
    st.session_state[K_RATE_TYPE] = rate_type

    # 利率設定（三種方案的欄位都先填好，切換利率方案時才不會漏值）
    st.session_state[K_SINGLE_RATE] = float(rate_config.get("single_rate", DEFAULTS["single_rate"]))
    st.session_state[K_RATE1] = float(rate_config.get("rate1", DEFAULTS["rate1"]))
    st.session_state[K_STAGE1_YEARS] = int(rate_config.get("stage1_years", DEFAULTS["stage1_years"]))
    st.session_state[K_RATE2] = float(rate_config.get("rate2", DEFAULTS["rate2"]))
    st.session_state[K_STAGE2_YEARS] = int(rate_config.get("stage2_years", 3))
    st.session_state[K_RATE3] = float(rate_config.get("rate3", DEFAULTS["rate2"]))

    # 額外還款：存檔時金額單位是「元」，介面輸入是「萬元」
    extras = []
    for er in config.get("extra_repayments") or []:
        try:
            extras.append({
                "year": int(er.get("year", 1)),
                "month": int(er.get("month", 1)),
                "amount": float(er.get("amount", 0)) / 10000,
            })
        except (TypeError, ValueError):
            continue
    st.session_state[K_EXTRA] = extras
    _clear_extra_widget_keys()

    # 進入編輯模式
    st.session_state[K_SCHEME_NAME] = scheme_name or ""
    st.session_state[K_EDIT_ID] = scheme_id
    st.session_state[K_EDIT_NAME] = scheme_name or ""
    st.session_state[K_AUTO_CALC] = True

    _clear_result()
    st.session_state[K_NAV] = PAGES[0]


def reset_form():
    """回到預設值並離開編輯模式（請在 button callback 中呼叫）"""
    for key, value in _defaults().items():
        st.session_state[key] = value

    st.session_state[K_EXTRA] = []
    _clear_extra_widget_keys()
    st.session_state[K_AUTO_CALC] = False

    st.session_state.pop(K_EDIT_ID, None)
    st.session_state.pop(K_EDIT_NAME, None)
    _clear_result()


def is_editing() -> bool:
    """目前是否在編輯既有方案"""
    return bool(st.session_state.get(K_EDIT_ID))


def current_edit_id():
    return st.session_state.get(K_EDIT_ID)


def current_edit_name() -> str:
    return st.session_state.get(K_EDIT_NAME, "")
