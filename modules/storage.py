"""
Google Sheets 存檔功能
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from streamlit_gsheets import GSheetsConnection


# 方案表固定欄位（updated_at 是新增欄位，舊資料會自動補上）
SCHEME_COLUMNS = ["id", "name", "created_at", "config", "result_summary", "updated_at"]


def get_conn():
    """取得 Google Sheets 連線"""
    return st.connection("gsheets", type=GSheetsConnection)


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=SCHEME_COLUMNS)


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """補齊缺少的欄位，並把空的 updated_at 填成 created_at"""
    for col in SCHEME_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["updated_at"] = df["updated_at"].fillna("").astype(str).str.strip()
    df.loc[df["updated_at"].isin(["", "None", "nan"]), "updated_at"] = df.loc[
        df["updated_at"].isin(["", "None", "nan"]), "created_at"
    ]
    return df


def load_schemes() -> pd.DataFrame:
    """載入所有已存的方案"""
    try:
        conn = get_conn()
        df = conn.read(ttl="1s")
        if df is None or df.empty:
            return _empty_df()
        # 移除空行
        df = df.dropna(subset=["id"])
        return _normalize(df)
    except Exception as e:
        st.warning(f"讀取雲端方案失敗（可能是首次使用）: {e}")
        return _empty_df()


def save_scheme(name: str, config: dict, result_summary: dict) -> bool:
    """儲存一個新方案到 Google Sheets"""
    try:
        conn = get_conn()
        df = load_schemes()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_row = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "name": name,
            "created_at": now,
            "config": json.dumps(config, ensure_ascii=False),
            "result_summary": json.dumps(result_summary, ensure_ascii=False),
            "updated_at": now,
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(data=df[SCHEME_COLUMNS])
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        return False


def update_scheme(scheme_id: str, name: str, config: dict, result_summary: dict) -> bool:
    """更新既有方案（保留 id 與建立時間），用於「載入並編輯」後存回"""
    try:
        conn = get_conn()
        df = load_schemes()
        if scheme_id not in df["id"].values:
            st.error("找不到要更新的方案，可能已被刪除。")
            return False

        idx = df.index[df["id"] == scheme_id][0]
        df.at[idx, "name"] = name
        df.at[idx, "config"] = json.dumps(config, ensure_ascii=False)
        df.at[idx, "result_summary"] = json.dumps(result_summary, ensure_ascii=False)
        df.at[idx, "updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.update(data=df[SCHEME_COLUMNS])
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"更新失敗: {e}")
        return False


def delete_scheme(scheme_id: str) -> bool:
    """刪除指定方案"""
    try:
        conn = get_conn()
        df = load_schemes()
        df = df[df["id"] != scheme_id]
        conn.update(data=df[SCHEME_COLUMNS])
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
