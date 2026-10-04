"""
Google Sheets 存檔功能
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from streamlit_gsheets import GSheetsConnection


def get_conn():
    """取得 Google Sheets 連線"""
    return st.connection("gsheets", type=GSheetsConnection)


def load_schemes() -> pd.DataFrame:
    """載入所有已存的方案"""
    try:
        conn = get_conn()
        df = conn.read(ttl="1s")
        if df is None or df.empty:
            return pd.DataFrame(columns=["id", "name", "created_at", "config", "result_summary"])
        # 移除空行
        df = df.dropna(subset=["id"])
        return df
    except Exception as e:
        st.warning(f"讀取雲端方案失敗（可能是首次使用）: {e}")
        return pd.DataFrame(columns=["id", "name", "created_at", "config", "result_summary"])


def save_scheme(name: str, config: dict, result_summary: dict) -> bool:
    """儲存一個方案到 Google Sheets"""
    try:
        conn = get_conn()
        df = load_schemes()

        new_row = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "name": name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": json.dumps(config, ensure_ascii=False),
            "result_summary": json.dumps(result_summary, ensure_ascii=False),
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        return False


def delete_scheme(scheme_id: str) -> bool:
    """刪除指定方案"""
    try:
        conn = get_conn()
        df = load_schemes()
        df = df[df["id"] != scheme_id]
        conn.update(data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"刪除失敗: {e}")
        return False


def parse_config(config_str: str) -> dict:
    """解析 config JSON"""
    try:
        return json.loads(config_str)
    except:
        return {}


def parse_summary(summary_str: str) -> dict:
    """解析 summary JSON"""
    try:
        return json.loads(summary_str)
    except:
        return {}
