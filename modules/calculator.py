"""
房貸核心計算邏輯
"""
from typing import Dict, List, Any
import pandas as pd


def get_monthly_rate(annual_rate: float) -> float:
    """年利率轉月利率"""
    return (annual_rate / 100) / 12


def get_rate_for_month(m: int, rate_type: str, rate_config: Dict) -> float:
    """取得第 m 個月的年利率"""
    if rate_type == "單一利率":
        return rate_config.get("single_rate", 2.0)

    elif rate_type == "兩階段浮動利率":
        stage1_months = rate_config.get("stage1_years", 3) * 12
        return rate_config.get("rate1", 1.775) if m <= stage1_months else rate_config.get("rate2", 2.275)

    elif rate_type == "三階段浮動利率":
        stage1_months = rate_config.get("stage1_years", 3) * 12
        stage2_months = stage1_months + rate_config.get("stage2_years", 3) * 12
        if m <= stage1_months:
            return rate_config.get("rate1", 1.775)
        elif m <= stage2_months:
            return rate_config.get("rate2", 2.0)
        else:
            return rate_config.get("rate3", 2.275)

    return 2.0


def calculate_loan(
    principal: float,
    years: int,
    grace_years: float,
    rate_type: str,
    rate_config: Dict,
    repayment_type: str = "本息均攤",
    extra_repayments: List[Dict] = None
) -> Dict[str, Any]:
    """
    計算房貸還款明細

    參數:
        principal: 貸款總額（元）
        years: 貸款年限
        grace_years: 寬限期（年）
        rate_type: 利率方案類型
        rate_config: 利率設定
        repayment_type: 還款方式
        extra_repayments: 額外還款列表 [{"year": 5, "month": 1, "amount": 1000000}, ...]

    回傳:
        包含明細、總利息、總還款等資訊的 dict
    """
    if extra_repayments is None:
        extra_repayments = []

    total_months = years * 12
    grace_months = int(grace_years * 12)

    schedule = []
    remaining = principal
    total_interest = 0.0

    # 建立額外還款的查詢表 {月數: 金額}
    extra_map = {}
    for er in extra_repayments:
        month = (int(er["year"]) - 1) * 12 + int(er.get("month", 1))
        extra_map[month] = extra_map.get(month, 0) + er["amount"]

    for m in range(1, total_months + 1):
        # 額外還款（繳款前先扣本金）
        extra_this_month = 0.0
        if m in extra_map:
            extra_this_month = min(extra_map[m], remaining)
            remaining -= extra_this_month

        if remaining <= 0:
            break

        annual_rate = get_rate_for_month(m, rate_type, rate_config)
        monthly_rate = get_monthly_rate(annual_rate)
        interest = remaining * monthly_rate
        total_interest += interest

        if m <= grace_months:
            # 寬限期：只繳利息
            payment = interest
            principal_paid = 0.0
        else:
            remaining_months = total_months - m + 1

            if repayment_type == "本金均攤":
                # 本金均攤：每月固定還本金
                principal_paid = remaining / remaining_months
                payment = principal_paid + interest
            else:
                # 本息均攤
                if monthly_rate > 0:
                    power = (1 + monthly_rate) ** remaining_months
                    payment = remaining * (monthly_rate * power) / (power - 1)
                else:
                    payment = remaining / remaining_months
                principal_paid = payment - interest

        remaining -= principal_paid
        if remaining < 0:
            remaining = 0

        schedule.append({
            "期數": m,
            "年": (m - 1) // 12 + 1,
            "月": (m - 1) % 12 + 1,
            "年利率": annual_rate,
            "當期利息": round(interest, 2),
            "當期本金": round(principal_paid, 2),
            "當期繳款": round(payment, 2),
            "額外還款": round(extra_this_month, 2),
            "剩餘本金": round(remaining, 2),
            "是否寬限期": m <= grace_months,
        })

    total_payment = principal + total_interest
    df = pd.DataFrame(schedule)

    # 每月應繳金額：取「寬限期結束後第一期」的金額
    if df.empty:
        monthly_payment = 0.0
        max_monthly_payment = 0.0
        grace_monthly_payment = 0.0
    else:
        grace_df = df[df["是否寬限期"]]
        normal_df = df[~df["是否寬限期"]]
        if normal_df.empty:
            normal_df = df
        monthly_payment = float(normal_df.iloc[0]["當期繳款"])
        max_monthly_payment = float(normal_df["當期繳款"].max())
        grace_monthly_payment = float(grace_df.iloc[0]["當期繳款"]) if not grace_df.empty else 0.0

    return {
        "schedule": df,
        "total_interest": total_interest,
        "total_payment": total_payment,
        "principal": principal,
        "months_taken": len(schedule),
        "monthly_payment": monthly_payment,
        "max_monthly_payment": max_monthly_payment,
        "grace_monthly_payment": grace_monthly_payment,
        "saved_interest": _calc_saved_interest(principal, years, grace_years, rate_type, rate_config, repayment_type, total_interest),
    }


def calculate_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """依照存檔的 config（貸款總額單位：萬元）重新計算"""
    config = config or {}
    return calculate_loan(
        principal=float(config.get("principal", 0)) * 10000,
        years=int(config.get("years", 0)),
        grace_years=float(config.get("grace_years", 0)),
        rate_type=config.get("rate_type", "單一利率"),
        rate_config=config.get("rate_config", {}),
        repayment_type=config.get("repayment_type", "本息均攤"),
        extra_repayments=config.get("extra_repayments", []),
    )


def summarize(result: Dict[str, Any]) -> Dict[str, Any]:
    """把計算結果濃縮成可存進 Google Sheets 的摘要"""
    return {
        "total_interest": result.get("total_interest", 0),
        "total_payment": result.get("total_payment", 0),
        "months_taken": result.get("months_taken", 0),
        "saved_interest": result.get("saved_interest", 0),
        "monthly_payment": result.get("monthly_payment", 0),
        "grace_monthly_payment": result.get("grace_monthly_payment", 0),
    }


def _calc_saved_interest(principal, years, grace_years, rate_type, rate_config, repayment_type, actual_interest):
    """計算因為提前還款省下的利息"""
    baseline = _calc_base_interest(principal, years, grace_years, rate_type, rate_config, repayment_type)
    return max(0, baseline - actual_interest)


def _calc_base_interest(principal, years, grace_years, rate_type, rate_config, repayment_type):
    """計算沒有額外還款時的總利息（基準）"""
    total_months = years * 12
    grace_months = int(grace_years * 12)
    remaining = principal
    total_interest = 0.0

    for m in range(1, total_months + 1):
        if remaining <= 0:
            break
        annual_rate = get_rate_for_month(m, rate_type, rate_config)
        monthly_rate = get_monthly_rate(annual_rate)
        interest = remaining * monthly_rate
        total_interest += interest

        if m <= grace_months:
            principal_paid = 0.0
        else:
            remaining_months = total_months - m + 1
            if repayment_type == "本金均攤":
                principal_paid = remaining / remaining_months
            else:
                if monthly_rate > 0:
                    power = (1 + monthly_rate) ** remaining_months
                    payment = remaining * (monthly_rate * power) / (power - 1)
                    principal_paid = payment - interest
                else:
                    principal_paid = remaining / remaining_months
        remaining -= principal_paid

    return total_interest
