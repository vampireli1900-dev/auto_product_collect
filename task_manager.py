import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import pandas as pd


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _parse_ts(s: Any) -> Optional[float]:
    try:
        txt = str(s or "").strip()
        if not txt:
            return None
        dt = datetime.strptime(txt, "%Y-%m-%d %H:%M:%S")
        return dt.timestamp()
    except Exception:
        return None

def _format_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


class _FileLock:
    def __init__(self, lock_path: str, timeout_s: float = 30.0, poll_s: float = 0.1):
        self.lock_path = lock_path
        self.timeout_s = timeout_s
        self.poll_s = poll_s
        self._fd: Optional[int] = None

    def __enter__(self):
        deadline = time.time() + self.timeout_s
        while True:
            try:
                self._fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self._fd, f"pid={os.getpid()} ts={_now_str()}\n".encode("utf-8"))
                return self
            except FileExistsError:
                if time.time() >= deadline:
                    raise TimeoutError(f"获取锁超时：{self.lock_path}")
                time.sleep(self.poll_s)

    def __exit__(self, exc_type, exc, tb):
        try:
            if self._fd is not None:
                os.close(self._fd)
        finally:
            self._fd = None
            try:
                os.unlink(self.lock_path)
            except FileNotFoundError:
                pass


@dataclass(frozen=True)
class ClaimedTask:
    index_num: int
    keyword: str
    row: Dict[str, Any]


class ExcelTaskManager:
    """
    用 Excel 做任务源与最终结果存档。
    通过 lockfile 保障多线程/多进程对同一个 Excel 的并发读写安全。
    """

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.lock_path = f"{excel_path}.lock"

    def _read_df(self) -> pd.DataFrame:
        if not os.path.exists(self.excel_path):
            raise FileNotFoundError(f"任务文件不存在：{self.excel_path}")
        return pd.read_excel(self.excel_path)

    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if "序号" not in df.columns:
            df["序号"] = range(1, len(df) + 1)
        if "状态" not in df.columns:
            df["状态"] = "未采集"

        defaults = {
            "领取设备": "",
            "开始时间": "",
            "结束时间": "",
            "重试次数": 0,
            "下次可重试时间": "",
            "备注": "",
            "失败原因": "",
        }
        for k, v in defaults.items():
            if k not in df.columns:
                df[k] = v
        return df

    def get_summary(self) -> Dict[str, Any]:
        with _FileLock(self.lock_path):
            df = self._ensure_columns(self._read_df())
            total = len(df)
            sta = df["状态"].astype(str).str.strip()
            done_strict = int((sta == "已采集").sum())
            review = int((sta == "待复核").sum())
            doing = int((sta == "采集中").sum())
            todo = int(((sta == "未采集") | sta.eq("") | sta.eq("nan")).sum())
            finished = done_strict + review
            success_den = total if total else 1
            return {
                "total": total,
                "done": done_strict,
                "review": review,
                "finished": finished,
                "doing": doing,
                "todo": todo,
                "success_rate_pct": round(100.0 * done_strict / success_den, 2),
            }

    def load_df(self) -> pd.DataFrame:
        with _FileLock(self.lock_path):
            df = self._ensure_columns(self._read_df())
            df.to_excel(self.excel_path, index=False)
            return df

    def claim_next(self, device_id: str) -> Optional[ClaimedTask]:
        with _FileLock(self.lock_path):
            df = self._ensure_columns(self._read_df())

            # 回收长期卡在“采集中”的任务，避免永远跳过（例如进程崩溃没回写）。
            reclaim_after_s = float(os.environ.get("COLLECT_RECLAIM_SECONDS", "900"))
            now_ts = time.time()
            doing_mask = df["状态"] == "采集中"
            if doing_mask.any():
                for ridx in df[doing_mask].index.tolist():
                    started_ts = _parse_ts(df.at[ridx, "开始时间"])
                    if started_ts is None:
                        continue
                    if now_ts - started_ts >= reclaim_after_s:
                        old_dev = str(df.at[ridx, "领取设备"] or "").strip()
                        df.at[ridx, "状态"] = "未采集"
                        df.at[ridx, "领取设备"] = ""
                        df.at[ridx, "开始时间"] = ""
                        old_remark = str(df.at[ridx, "备注"] or "").strip()
                        extra = f"采集中超时回收（原设备 {old_dev}）"
                        df.at[ridx, "备注"] = extra if not old_remark else f"{old_remark}；{extra}"

            # 领取策略：
            # 1) 只领取“未采集”
            # 2) 如果设置了“下次可重试时间”，未到时间则跳过，避免一直重试同一条超时任务
            candidates = df[df["状态"] == "未采集"].copy()
            if not candidates.empty and "下次可重试时间" in candidates.columns:
                allowed_rows = []
                for ridx in candidates.index.tolist():
                    next_ts = _parse_ts(candidates.at[ridx, "下次可重试时间"])
                    if next_ts is None or next_ts <= now_ts:
                        allowed_rows.append(ridx)
                candidates = candidates.loc[allowed_rows] if allowed_rows else candidates.iloc[0:0]

            if candidates.empty:
                df.to_excel(self.excel_path, index=False)
                return None

            # 优先领取重试次数更少的，避免卡死在某个顽固词条
            try:
                df_try = df.loc[candidates.index].copy()
                df_try["重试次数"] = pd.to_numeric(df_try["重试次数"], errors="coerce").fillna(0).astype(int)
                row_idx = int(df_try.sort_values(by=["重试次数", "序号"], ascending=[True, True]).index[0])
            except Exception:
                row_idx = int(candidates.index[0])

            index_num = int(df.at[row_idx, "序号"])
            keyword = str(df.at[row_idx, "货品名称"]).strip()

            df.at[row_idx, "状态"] = "采集中"
            df.at[row_idx, "领取设备"] = device_id
            df.at[row_idx, "开始时间"] = _now_str()
            df.at[row_idx, "下次可重试时间"] = ""
            try:
                df.at[row_idx, "重试次数"] = int(df.at[row_idx, "重试次数"] or 0)
            except Exception:
                df.at[row_idx, "重试次数"] = 0

            df.to_excel(self.excel_path, index=False)
            return ClaimedTask(index_num=index_num, keyword=keyword, row=df.loc[row_idx].to_dict())

    def finish(
        self,
        index_num: int,
        device_id: str,
        final_status: str,
        remark: str = "",
        retry_inc: int = 0,
        fail_reason: str = "",
    ) -> None:
        if final_status not in {"已采集", "未采集", "待复核"}:
            raise ValueError(f"不支持的状态：{final_status}")

        with _FileLock(self.lock_path):
            df = self._ensure_columns(self._read_df())
            mask = df["序号"] == index_num
            if not mask.any():
                return

            row_idx = int(df[mask].index[0])
            df.at[row_idx, "状态"] = final_status
            df.at[row_idx, "结束时间"] = _now_str()

            if final_status == "未采集" and fail_reason:
                df.at[row_idx, "失败原因"] = str(fail_reason)
            elif final_status in {"已采集", "待复核"}:
                df.at[row_idx, "失败原因"] = ""

            if str(df.at[row_idx, "领取设备"] or "") == "":
                df.at[row_idx, "领取设备"] = device_id
            if retry_inc:
                try:
                    df.at[row_idx, "重试次数"] = int(df.at[row_idx, "重试次数"] or 0) + int(retry_inc)
                except Exception:
                    df.at[row_idx, "重试次数"] = int(retry_inc)
            # 失败回写时给一个短冷却，避免设备立刻又领回同一条导致“卡死”
            if final_status == "未采集" and retry_inc:
                cooldown_s = 120
                df.at[row_idx, "下次可重试时间"] = _format_ts(time.time() + cooldown_s)
            if remark:
                old = str(df.at[row_idx, "备注"] or "").strip()
                df.at[row_idx, "备注"] = remark if not old else f"{old}；{remark}"

            df.to_excel(self.excel_path, index=False)
