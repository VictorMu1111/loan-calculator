"""
利率方案的文字描述工具

把 rate_type + rate_config 轉成給人看的說明，例如：
- 單一利率：全程 2.200%
- 兩階段：第一階段 1.775%（第 1–3 年）、第二階段 2.275%（第 4 年起）
"""
from typing import Dict, List


def describe_rate_plan(rate_type: str, rate_config: Dict) -> List[str]:
    """回傳每個階段的利率說明（Markdown 粗體，適合在 expander 內條列）"""
    rc = rate_config or {}

    if rate_type == "兩階段浮動利率":
        stage1 = int(rc.get("stage1_years", 3))
        return [
            f"第一階段：**{rc.get('rate1', 0):.3f}%**（第 1–{stage1} 年）",
            f"第二階段：**{rc.get('rate2', 0):.3f}%**（第 {stage1 + 1} 年起）",
        ]

    if rate_type == "三階段浮動利率":
        stage1 = int(rc.get("stage1_years", 3))
        stage2 = int(rc.get("stage2_years", 3))
        return [
            f"第一階段：**{rc.get('rate1', 0):.3f}%**（第 1–{stage1} 年）",
            f"第二階段：**{rc.get('rate2', 0):.3f}%**（第 {stage1 + 1}–{stage1 + stage2} 年）",
            f"第三階段：**{rc.get('rate3', 0):.3f}%**（第 {stage1 + stage2 + 1} 年起）",
        ]

    return [f"全程單一利率：**{rc.get('single_rate', 0):.3f}%**"]


def describe_rate_plan_text(rate_type: str, rate_config: Dict) -> str:
    """回傳單行利率說明（純文字，適合表格或 caption）"""
    rc = rate_config or {}

    if rate_type == "兩階段浮動利率":
        stage1 = int(rc.get("stage1_years", 3))
        return (f"{rc.get('rate1', 0):.3f}%（第 1–{stage1} 年） → "
                f"{rc.get('rate2', 0):.3f}%（第 {stage1 + 1} 年起）")

    if rate_type == "三階段浮動利率":
        stage1 = int(rc.get("stage1_years", 3))
        stage2 = int(rc.get("stage2_years", 3))
        return (f"{rc.get('rate1', 0):.3f}%（第 1–{stage1} 年） → "
                f"{rc.get('rate2', 0):.3f}%（第 {stage1 + 1}–{stage1 + stage2} 年） → "
                f"{rc.get('rate3', 0):.3f}%（第 {stage1 + stage2 + 1} 年起）")

    return f"{rc.get('single_rate', 0):.3f}%（全程固定）"


def rate_plan_from_config(config: Dict) -> List[str]:
    """從存檔的 config 取得利率說明"""
    config = config or {}
    return describe_rate_plan(config.get("rate_type", ""), config.get("rate_config", {}))


def rate_plan_text_from_config(config: Dict) -> str:
    """從存檔的 config 取得單行利率說明"""
    config = config or {}
    return describe_rate_plan_text(config.get("rate_type", ""), config.get("rate_config", {}))
