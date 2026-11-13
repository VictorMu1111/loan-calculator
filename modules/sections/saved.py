"""
已存方案管理區塊
"""
import streamlit as st
import pandas as pd

from modules.calculator import calculate_from_config, summarize
from modules.rate_info import describe_rate_plan
from modules.session import apply_config_to_state, current_edit_id
from modules.storage import load_schemes, delete_scheme, parse_config, parse_summary


def _clean(value, fallback: str = "") -> str:
    """把可能是 NaN / None 的欄位轉成字串"""
    if value is None:
        return fallback
    if isinstance(value, float) and pd.isna(value):
        return fallback
    text = str(value).strip()
    return text if text and text.lower() != "nan" else fallback


def _ensure_summary(config: dict, summary: dict) -> dict:
    """舊版存檔沒有每月應繳欄位，缺欄位時用方案設定重新計算補上"""
    if "monthly_payment" in summary:
        return summary
    try:
        merged = summarize(calculate_from_config(config))
    except Exception:
        merged = {}
    merged.update(summary)  # 以存檔內容為主
    merged.setdefault("monthly_payment", 0)
    merged.setdefault("grace_monthly_payment", 0)
    return merged


def _load_for_edit(config: dict, scheme_id: str, scheme_name: str):
    """button callback：把方案載入到「單一方案」頁面並自動重算"""
    apply_config_to_state(config, scheme_id, scheme_name)
    st.toast(f"已載入「{scheme_name}」，可直接修改後更新", icon="✏️")


def render_saved_schemes():
    """已儲存的方案管理"""
    st.markdown("### 💾 我的方案")
    st.caption("方案含完整設定與利率資訊；按「✏️ 載入並編輯」即可回到試算頁繼續修改並存回。")

    df = load_schemes()
    if df.empty:
        st.info("尚無已儲存的方案。到「單一方案」頁面計算後，即可儲存到雲端！")
        return

    st.caption(f"共 {len(df)} 個方案")

    editing_id = current_edit_id()

    for _, row in df.iterrows():
        scheme_id = row["id"]
        created_at = _clean(row.get("created_at"))
        updated_at = _clean(row.get("updated_at"), created_at)

        title = f"📌 {row['name']}　—　{created_at}"
        if updated_at and updated_at != created_at:
            title += f"（更新於 {updated_at}）"
        if scheme_id == editing_id:
            title += "　✏️ 編輯中"

        with st.expander(title, expanded=(scheme_id == editing_id)):
            config = parse_config(row["config"])
            summary = _ensure_summary(config, parse_summary(row["result_summary"]))

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("每月應繳", f"{summary.get('monthly_payment', 0):,.0f} 元")
            c2.metric("總利息", f"{summary.get('total_interest', 0):,.0f} 元")
            c3.metric("總還款", f"{summary.get('total_payment', 0):,.0f} 元")
            c4.metric("還款期數", f"{summary.get('months_taken', 0)} 期")

            if summary.get("grace_monthly_payment", 0):
                st.caption(f"寬限期月付：{summary['grace_monthly_payment']:,.0f} 元（只繳利息）")

            st.markdown("**方案設定：**")
            st.markdown(f"""
            - 貸款總額：**{config.get('principal', 0):,.0f} 萬元**
            - 貸款年限：**{config.get('years', 0)} 年**
            - 寬限期：**{config.get('grace_years', 0)} 年**
            - 利率方案：**{config.get('rate_type', '-')}**
            - 還款方式：**{config.get('repayment_type', '本息均攤')}**
            """)

            st.markdown("**利率資訊：**")
            for line in describe_rate_plan(config.get("rate_type", ""), config.get("rate_config", {})):
                st.markdown(f"- {line}")

            extra = config.get("extra_repayments", [])
            if extra:
                st.markdown("**額外還款：**")
                for er in extra:
                    st.markdown(
                        f"- 第 {er['year']} 年第 {er.get('month', 1)} 個月："
                        f"**{er['amount'] / 10000:,.1f} 萬元**"
                    )

            if summary.get("saved_interest", 0) > 0:
                st.success(f"🎉 因提前還款省下利息：**{summary['saved_interest']:,.0f} 元**")

            b1, b2 = st.columns(2)
            b1.button(
                "✏️ 載入並編輯",
                key=f"edit_{scheme_id}",
                use_container_width=True,
                on_click=_load_for_edit,
                args=(config, scheme_id, row["name"]),
            )
            if b2.button("🗑️ 刪除此方案", key=f"del_{scheme_id}", use_container_width=True):
                if delete_scheme(scheme_id):
                    st.toast(f"已刪除「{row['name']}」", icon="🗑️")
                    st.rerun()

