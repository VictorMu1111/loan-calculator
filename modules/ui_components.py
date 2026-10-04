"""
UI 元件 - 結果卡片、圖表
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def render_summary_metrics(result: dict):
    """顯示總覽指標"""
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("💰 總還款利息", f"{result['total_interest']:,.0f} 元")
    c2.metric("📊 本息還款總額", f"{result['total_payment']:,.0f} 元")
    c3.metric("⏱️ 實際還款月數", f"{result['months_taken']} 期")

    if result.get("saved_interest", 0) > 0:
        c4.metric("🎉 省下利息", f"{result['saved_interest']:,.0f} 元")
    else:
        c4.metric("🎉 省下利息", "—")


def render_payment_chart(result: dict):
    """繪製每月還款組成圖（本金 vs 利息）"""
    df = result["schedule"]
    if df.empty:
        return

    # 取樣，避免圖表太擁擠（超過 120 期就取樣）
    if len(df) > 120:
        sample = df.iloc[::max(1, len(df) // 120)]
    else:
        sample = df

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sample["期數"],
        y=sample["當期本金"],
        name="本金",
        marker_color="#2b6cb0"
    ))
    fig.add_trace(go.Bar(
        x=sample["期數"],
        y=sample["當期利息"],
        name="利息",
        marker_color="#e53e3e"
    ))

    fig.update_layout(
        title="每月還款組成（本金 vs 利息）",
        xaxis_title="期數",
        yaxis_title="金額 (元)",
        barmode="stack",
        height=400,
        hovermode="x unified",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True, key="payment_chart")


def render_balance_chart(result: dict):
    """繪製剩餘本金曲線"""
    df = result["schedule"]
    if df.empty:
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["期數"],
        y=df["剩餘本金"],
        mode="lines",
        name="剩餘本金",
        line=dict(color="#38a169", width=2),
        fill="tozeroy",
        fillcolor="rgba(56,161,105,0.2)"
    ))

    fig.update_layout(
        title="剩餘本金變化",
        xaxis_title="期數",
        yaxis_title="剩餘本金 (元)",
        height=350,
        hovermode="x unified",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True, key="balance_chart")


def render_schedule_table(result: dict, max_rows: int = 100):
    """顯示攤還明細表"""
    df = result["schedule"].copy()
    df["年利率"] = df["年利率"].apply(lambda x: f"{x:.3f}%")
    df["是否寬限期"] = df["是否寬限期"].apply(lambda x: "✅" if x else "")

    df = df[["期數", "年", "月", "年利率", "當期繳款", "當期本金", "當期利息", "額外還款", "剩餘本金", "是否寬限期"]]

    st.dataframe(
        df.head(max_rows).style.format({
            "當期繳款": "{:,.0f}",
            "當期本金": "{:,.0f}",
            "當期利息": "{:,.0f}",
            "額外還款": "{:,.0f}",
            "剩餘本金": "{:,.0f}",
        }),
        use_container_width=True,
        height=400
    )

    if len(df) > max_rows:
        st.caption(f"僅顯示前 {max_rows} 期，共 {len(df)} 期")
