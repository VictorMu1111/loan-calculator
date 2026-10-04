"""
單一方案計算區塊
"""
import streamlit as st
from modules.config import DEFAULTS, RATE_TYPES, REPAYMENT_TYPES
from modules.calculator import calculate_loan
from modules.storage import save_scheme
from modules.ui_components import (
    render_summary_metrics,
    render_payment_chart,
    render_balance_chart,
    render_schedule_table
)


def render_extra_repayments():
    """額外還款輸入區"""
    st.markdown("##### 💸 額外提前還款（可多次）")

    if "extra_repayments" not in st.session_state:
        st.session_state.extra_repayments = []

    # 新增還款按鈕
    if st.button("➕ 新增一筆提前還款", key="add_extra"):
        st.session_state.extra_repayments.append({"year": 5, "month": 1, "amount": 100})
        st.rerun()

    extra_list = []
    to_remove = None

    for i, er in enumerate(st.session_state.extra_repayments):
        cols = st.columns([1, 1, 1.5, 0.5])
        year = cols[0].number_input(f"第幾年", min_value=1, max_value=50,
                                     value=er["year"], key=f"er_year_{i}")
        month = cols[1].number_input(f"第幾月", min_value=1, max_value=12,
                                      value=er["month"], key=f"er_month_{i}")
        amount = cols[2].number_input(f"金額 (萬元)", min_value=0.0,
                                       value=float(er["amount"]), step=10.0, key=f"er_amt_{i}")
        if cols[3].button("🗑️", key=f"er_del_{i}"):
            to_remove = i

        extra_list.append({"year": year, "month": month, "amount": amount * 10000})

    if to_remove is not None:
        st.session_state.extra_repayments.pop(to_remove)
        st.rerun()

    return extra_list


def render_single_calc():
    """單一方案計算"""
    st.markdown("### 🧮 單一方案試算")

    # 基本輸入
    col1, col2 = st.columns(2)
    principal = col1.number_input("貸款總額 (萬元)", min_value=0.0,
                                   value=float(DEFAULTS["principal"]), step=50.0)
    years = col2.number_input("貸款年限 (年)", min_value=1, max_value=50,
                               value=DEFAULTS["years"], step=1)

    col3, col4 = st.columns(2)
    grace_years = col3.number_input("寬限期 (年)", min_value=0.0, max_value=10.0,
                                     value=float(DEFAULTS["grace_years"]), step=0.5)
    repayment_type = col4.selectbox("還款方式", REPAYMENT_TYPES)

    # 利率方案
    rate_type = st.radio("利率方案", RATE_TYPES, horizontal=True)

    rate_config = {}
    if rate_type == "單一利率":
        rate_config["single_rate"] = st.number_input("年利率 (%)", min_value=0.0,
                                                       value=DEFAULTS["single_rate"], step=0.01, format="%.3f")
    elif rate_type == "兩階段浮動利率":
        c1, c2 = st.columns(2)
        rate_config["rate1"] = c1.number_input("第一階段利率 (%)", min_value=0.0,
                                                 value=DEFAULTS["rate1"], step=0.01, format="%.3f")
        rate_config["stage1_years"] = c2.number_input("第一階段期間 (年)", min_value=1,
                                                        value=DEFAULTS["stage1_years"], step=1)
        rate_config["rate2"] = st.number_input("第二階段利率 (%)", min_value=0.0,
                                                 value=DEFAULTS["rate2"], step=0.01, format="%.3f")
    else:  # 三階段
        c1, c2 = st.columns(2)
        rate_config["rate1"] = c1.number_input("第一階段利率 (%)", min_value=0.0,
                                                 value=DEFAULTS["rate1"], step=0.01, format="%.3f")
        rate_config["stage1_years"] = c2.number_input("第一階段期間 (年)", min_value=1, value=3, step=1)
        c3, c4 = st.columns(2)
        rate_config["rate2"] = c3.number_input("第二階段利率 (%)", min_value=0.0, value=2.0, step=0.01, format="%.3f")
        rate_config["stage2_years"] = c4.number_input("第二階段期間 (年)", min_value=1, value=3, step=1)
        rate_config["rate3"] = st.number_input("第三階段利率 (%)", min_value=0.0,
                                                 value=DEFAULTS["rate2"], step=0.01, format="%.3f")

    # 額外還款
    extra_repayments = render_extra_repayments()

    # 計算按鈕
    if st.button("🚀 開始計算", type="primary", use_container_width=True):
        if grace_years >= years:
            st.error("❌ 寬限期不能大於或等於貸款總年限！")
            return

        result = calculate_loan(
            principal=principal * 10000,
            years=int(years),
            grace_years=grace_years,
            rate_type=rate_type,
            rate_config=rate_config,
            repayment_type=repayment_type,
            extra_repayments=extra_repayments
        )

        st.session_state.last_result = result
        st.session_state.last_config = {
            "principal": principal,
            "years": int(years),
            "grace_years": grace_years,
            "rate_type": rate_type,
            "rate_config": rate_config,
            "repayment_type": repayment_type,
            "extra_repayments": extra_repayments,
        }

    # 顯示結果
    if "last_result" in st.session_state:
        result = st.session_state.last_result
        st.markdown("---")
        st.markdown("### 📊 計算結果")

        render_summary_metrics(result)

        tab1, tab2, tab3 = st.tabs(["📈 還款組成", "📉 剩餘本金", "📋 攤還明細"])
        with tab1:
            render_payment_chart(result)
        with tab2:
            render_balance_chart(result)
        with tab3:
            render_schedule_table(result)

        # 存檔
        st.markdown("---")
        c1, c2 = st.columns([3, 1])
        scheme_name = c1.text_input("方案名稱", placeholder="例如：新青安 30年")
        if c2.button("💾 儲存方案", use_container_width=True):
            if not scheme_name.strip():
                st.warning("請輸入方案名稱！")
            else:
                summary = {
                    "total_interest": result["total_interest"],
                    "total_payment": result["total_payment"],
                    "months_taken": result["months_taken"],
                    "saved_interest": result.get("saved_interest", 0),
                }
                if save_scheme(scheme_name, st.session_state.last_config, summary):
                    st.success(f"✅ 方案「{scheme_name}」已儲存！")
