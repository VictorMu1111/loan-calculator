"""
單一方案計算區塊
"""
import streamlit as st

from modules.config import RATE_TYPES, REPAYMENT_TYPES
from modules.calculator import calculate_from_config, summarize
from modules.rate_info import describe_rate_plan_text
from modules.session import (
    init_form_state,
    is_editing,
    current_edit_id,
    current_edit_name,
    reset_form,
    K_PRINCIPAL, K_YEARS, K_GRACE, K_REPAYMENT, K_RATE_TYPE,
    K_SINGLE_RATE, K_RATE1, K_STAGE1_YEARS, K_RATE2, K_STAGE2_YEARS, K_RATE3,
    K_EXTRA, K_SCHEME_NAME, K_AUTO_CALC,
)
from modules.storage import save_scheme, update_scheme
from modules.ui_components import (
    render_summary_metrics,
    render_payment_chart,
    render_balance_chart,
    render_schedule_table
)

EXTRA_WIDGET_PREFIXES = ("er_year_", "er_month_", "er_amt_", "er_del_")


def render_extra_repayments():
    """額外還款輸入區（介面輸入萬元，計算時轉為元）"""
    st.markdown("##### 💸 額外提前還款（可多次）")

    if K_EXTRA not in st.session_state:
        st.session_state[K_EXTRA] = []

    # 新增還款按鈕
    if st.button("➕ 新增一筆提前還款", key="add_extra"):
        st.session_state[K_EXTRA].append({"year": 5, "month": 1, "amount": 100.0})
        st.rerun()

    extra_list = []
    to_remove = None

    for i, er in enumerate(st.session_state[K_EXTRA]):
        cols = st.columns([1, 1, 1.5, 0.5])

        # 先補 state 再建立 widget，避免出現「預設值 + session state」警告
        if f"er_year_{i}" not in st.session_state:
            st.session_state[f"er_year_{i}"] = int(er["year"])
        if f"er_month_{i}" not in st.session_state:
            st.session_state[f"er_month_{i}"] = int(er["month"])
        if f"er_amt_{i}" not in st.session_state:
            st.session_state[f"er_amt_{i}"] = float(er["amount"])

        year = cols[0].number_input(f"第幾年", min_value=1, max_value=50, key=f"er_year_{i}")
        month = cols[1].number_input(f"第幾月", min_value=1, max_value=12, key=f"er_month_{i}")
        amount = cols[2].number_input(f"金額 (萬元)", min_value=0.0, step=10.0, key=f"er_amt_{i}")
        if cols[3].button("🗑️", key=f"er_del_{i}"):
            to_remove = i

        # 把使用者改過的值寫回清單，刪除列或存檔時才不會用到舊值
        st.session_state[K_EXTRA][i] = {
            "year": int(year),
            "month": int(month),
            "amount": float(amount),
        }
        extra_list.append({"year": int(year), "month": int(month), "amount": amount * 10000})

    if to_remove is not None:
        st.session_state[K_EXTRA].pop(to_remove)
        for key in list(st.session_state.keys()):
            if str(key).startswith(EXTRA_WIDGET_PREFIXES):
                st.session_state.pop(key, None)
        st.rerun()

    return extra_list


def render_single_calc():
    """單一方案計算"""
    init_form_state()

    st.markdown("### 🧮 單一方案試算")

    # 編輯模式提示（取消編輯要用 callback，才能在 widget 建立前重設 state）
    if is_editing():
        st.info(f"✏️ 正在編輯方案「{current_edit_name()}」：修改下方設定後，按「💾 更新方案」即可覆蓋原本的存檔。")
        st.button("✖️ 取消編輯（回到預設值）", on_click=reset_form, key="cancel_edit")

    # 基本輸入
    col1, col2 = st.columns(2)
    principal = col1.number_input("貸款總額 (萬元)", min_value=0.0, step=50.0, key=K_PRINCIPAL)
    years = col2.number_input("貸款年限 (年)", min_value=1, max_value=50, step=1, key=K_YEARS)

    col3, col4 = st.columns(2)
    grace_years = col3.number_input("寬限期 (年)", min_value=0.0, max_value=10.0, step=0.5, key=K_GRACE)
    repayment_type = col4.selectbox("還款方式", REPAYMENT_TYPES, key=K_REPAYMENT)

    # 利率方案
    rate_type = st.radio("利率方案", RATE_TYPES, horizontal=True, key=K_RATE_TYPE)

    rate_config = {}
    if rate_type == "單一利率":
        rate_config["single_rate"] = st.number_input("年利率 (%)", min_value=0.0, step=0.01,
                                                     format="%.3f", key=K_SINGLE_RATE)
    elif rate_type == "兩階段浮動利率":
        c1, c2 = st.columns(2)
        rate_config["rate1"] = c1.number_input("第一階段利率 (%)", min_value=0.0, step=0.01,
                                               format="%.3f", key=K_RATE1)
        rate_config["stage1_years"] = c2.number_input("第一階段期間 (年)", min_value=1, step=1,
                                                      key=K_STAGE1_YEARS)
        rate_config["rate2"] = st.number_input("第二階段利率 (%)", min_value=0.0, step=0.01,
                                               format="%.3f", key=K_RATE2)
    else:  # 三階段
        c1, c2 = st.columns(2)
        rate_config["rate1"] = c1.number_input("第一階段利率 (%)", min_value=0.0, step=0.01,
                                               format="%.3f", key=K_RATE1)
        rate_config["stage1_years"] = c2.number_input("第一階段期間 (年)", min_value=1, step=1,
                                                      key=K_STAGE1_YEARS)
        c3, c4 = st.columns(2)
        rate_config["rate2"] = c3.number_input("第二階段利率 (%)", min_value=0.0, step=0.01,
                                               format="%.3f", key=K_RATE2)
        rate_config["stage2_years"] = c4.number_input("第二階段期間 (年)", min_value=1, step=1,
                                                      key=K_STAGE2_YEARS)
        rate_config["rate3"] = st.number_input("第三階段利率 (%)", min_value=0.0, step=0.01,
                                               format="%.3f", key=K_RATE3)

    # 額外還款
    extra_repayments = render_extra_repayments()

    config = {
        "principal": float(principal),
        "years": int(years),
        "grace_years": float(grace_years),
        "rate_type": rate_type,
        "rate_config": rate_config,
        "repayment_type": repayment_type,
        "extra_repayments": extra_repayments,
    }

    # 計算按鈕（載入已存方案會自動算一次）
    auto_calc = st.session_state.pop(K_AUTO_CALC, False)
    if st.button("🚀 開始計算", type="primary", use_container_width=True) or auto_calc:
        if grace_years >= years:
            st.error("❌ 寬限期不能大於或等於貸款總年限！")
            return

        result = calculate_from_config(config)
        st.session_state.last_result = result
        st.session_state.last_config = config

    # 顯示結果
    if "last_result" in st.session_state:
        result = st.session_state.last_result
        shown_config = st.session_state.get("last_config", config)

        st.markdown("---")
        st.markdown("### 📊 計算結果")

        render_summary_metrics(result)
        st.caption("利率：" + describe_rate_plan_text(
            shown_config.get("rate_type", ""), shown_config.get("rate_config", {})
        ))

        tab1, tab2, tab3 = st.tabs(["📈 還款組成", "📉 剩餘本金", "📋 攤還明細"])
        with tab1:
            render_payment_chart(result)
        with tab2:
            render_balance_chart(result)
        with tab3:
            render_schedule_table(result)

        # 存檔 / 更新
        st.markdown("---")
        editing_id = current_edit_id()
        scheme_name = st.text_input("方案名稱", key=K_SCHEME_NAME, placeholder="例如：新青安 30年")
        summary = summarize(result)

        # 表單改過但還沒重新計算時，避免把舊的試算結果存進方案
        if st.session_state.get("last_config", config) != config:
            st.warning("⚠️ 上方設定已變更，請先按「🚀 開始計算」再儲存，否則會存到上一次的試算結果。")

        if editing_id:
            b1, b2 = st.columns(2)
            if b1.button("💾 更新方案", type="primary", use_container_width=True):
                if not scheme_name.strip():
                    st.warning("請輸入方案名稱！")
                elif update_scheme(editing_id, scheme_name.strip(),
                                   st.session_state.last_config, summary):
                    st.success(f"✅ 方案「{scheme_name.strip()}」已更新！")
            if b2.button("📄 另存為新方案", use_container_width=True):
                if not scheme_name.strip():
                    st.warning("請輸入方案名稱！")
                elif save_scheme(scheme_name.strip(), st.session_state.last_config, summary):
                    st.success(f"✅ 已另存為新方案「{scheme_name.strip()}」！")
        else:
            if st.button("💾 儲存方案", use_container_width=True):
                if not scheme_name.strip():
                    st.warning("請輸入方案名稱！")
                elif save_scheme(scheme_name.strip(), st.session_state.last_config, summary):
                    st.success(f"✅ 方案「{scheme_name.strip()}」已儲存！")
