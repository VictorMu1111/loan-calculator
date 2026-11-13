"""
多方案比較區塊
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.calculator import calculate_from_config
from modules.rate_info import describe_rate_plan_text
from modules.storage import load_schemes, parse_config


def render_compare():
    """多方案比較"""
    st.markdown("### ⚖️ 方案比較")
    st.caption("勾選下方已儲存的方案進行比較")

    df = load_schemes()
    if df.empty:
        st.info("尚無已儲存的方案，請先到「單一方案」頁面計算並儲存！")
        return

    # 勾選要比較的方案
    options = {f"{row['name']} ({row['created_at']})": row['id'] for _, row in df.iterrows()}
    selected = st.multiselect("選擇要比較的方案", list(options.keys()))

    if len(selected) < 1:
        st.info("請至少選擇 1 個方案")
        return

    # 重新計算每個方案的完整結果
    results = []
    for label in selected:
        scheme_id = options[label]
        row = df[df["id"] == scheme_id].iloc[0]
        config = parse_config(row["config"])

        result = calculate_from_config(config)
        results.append({
            "name": row["name"],
            "config": config,
            "result": result,
        })

    # 比較表格
    st.markdown("#### 📊 方案總覽比較")
    compare_data = []
    for r in results:
        compare_data.append({
            "方案": r["name"],
            "貸款總額 (萬)": f"{r['config']['principal']:,.0f}",
            "年限": f"{r['config']['years']} 年",
            "寬限期": f"{r['config']['grace_years']} 年",
            "利率方案": r["config"]["rate_type"],
            "利率": describe_rate_plan_text(
                r["config"].get("rate_type", ""), r["config"].get("rate_config", {})
            ),
            "還款方式": r["config"].get("repayment_type", "本息均攤"),
            "每月應繳 (元)": f"{r['result'].get('monthly_payment', 0):,.0f}",
            "總利息 (元)": f"{r['result']['total_interest']:,.0f}",
            "總還款 (元)": f"{r['result']['total_payment']:,.0f}",
            "省下利息 (元)": f"{r['result'].get('saved_interest', 0):,.0f}",
        })

    compare_df = pd.DataFrame(compare_data)
    st.dataframe(compare_df, use_container_width=True, hide_index=True)

    # 圖表比較：總利息
    st.markdown("#### 📈 總利息比較")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[r["name"] for r in results],
        y=[r["result"]["total_interest"] for r in results],
        marker_color="#e53e3e",
        text=[f"{r['result']['total_interest']:,.0f}" for r in results],
        textposition="outside"
    ))
    fig.update_layout(
        height=350,
        template="plotly_white",
        yaxis_title="總利息 (元)",
        xaxis_title="方案"
    )
    st.plotly_chart(fig, use_container_width=True, key="compare_interest")

    # 曲線比較：剩餘本金
    st.markdown("#### 📉 剩餘本金比較")
    fig2 = go.Figure()
    colors = ["#2b6cb0", "#e53e3e", "#38a169", "#d69e2e", "#805ad5"]
    for i, r in enumerate(results):
        df_sched = r["result"]["schedule"]
        fig2.add_trace(go.Scatter(
            x=df_sched["期數"],
            y=df_sched["剩餘本金"],
            mode="lines",
            name=r["name"],
            line=dict(color=colors[i % len(colors)], width=2)
        ))
    fig2.update_layout(
        height=400,
        template="plotly_white",
        xaxis_title="期數",
        yaxis_title="剩餘本金 (元)",
        hovermode="x unified"
    )
    st.plotly_chart(fig2, use_container_width=True, key="compare_balance")

    # 每月還款比較
    st.markdown("#### 💰 每月還款金額比較")
    fig3 = go.Figure()
    for i, r in enumerate(results):
        df_sched = r["result"]["schedule"]
        fig3.add_trace(go.Scatter(
            x=df_sched["期數"],
            y=df_sched["當期繳款"],
            mode="lines",
            name=r["name"],
            line=dict(color=colors[i % len(colors)], width=2)
        ))
    fig3.update_layout(
        height=400,
        template="plotly_white",
        xaxis_title="期數",
        yaxis_title="每月繳款 (元)",
        hovermode="x unified"
    )
    st.plotly_chart(fig3, use_container_width=True, key="compare_monthly")
