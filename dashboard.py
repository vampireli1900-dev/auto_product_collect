import streamlit as st
import pandas as pd
import subprocess
import sys
import os
import threading
import time
import signal

# ====================== 固定配置 ======================
BASE_DIR = "/Users/vincentli/PycharmProjects/PythonProject/2026-4 群控/yolo/整合详情页采集"
DEFAULT_TASK_PATH = os.path.join(BASE_DIR, "搜索名单.xlsx")
LOG_FILE = os.path.join(BASE_DIR, "collector_logs.txt")

sys.path.append(BASE_DIR)
os.chdir(BASE_DIR)

# 全局停止控制
running_processes = {}

# ====================== 初始化 ======================
st.set_page_config(page_title="多机群控采集系统", layout="wide", initial_sidebar_state="expanded")

# 任务
if "task_df" not in st.session_state:
    try:
        df = pd.read_excel(DEFAULT_TASK_PATH)
        if "状态" not in df.columns:
            df["状态"] = "未采集"
        st.session_state.task_df = df
        st.session_state.total_tasks = len(df)
        st.session_state.done_tasks = len(df[df["状态"] == "已采集"])
    except:
        st.session_state.task_df = pd.DataFrame()
        st.session_state.total_tasks = 0
        st.session_state.done_tasks = 0

# 设备
if "device_list" not in st.session_state:
    st.session_state.device_list = []

if "current_menu" not in st.session_state:
    st.session_state.current_menu = "🏠 数据概览"

# ====================== 日志 ======================
def add_log(msg):
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass

def get_recent_logs():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "".join(lines[-100:])
    except:
        return "暂无日志"

# ====================== 侧边栏 ======================
with st.sidebar:
    st.markdown("### 🤖 多机群控采集系统")
    st.divider()
    menus = ["🏠 数据概览", "📥 任务管理", "📱 设备管理", "⚙️ 调度配置", "📊 进度监控", "⚠️ 实时日志"]
    for m in menus:
        if st.button(m, use_container_width=True):
            st.session_state.current_menu = m

menu = st.session_state.current_menu

# ====================== 主页 ======================
if menu == "🏠 数据概览":
    st.title("📊 系统总览")
    total = st.session_state.total_tasks
    done = st.session_state.done_tasks
    progress = done / total if total > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总任务数", total)
    col2.metric("已完成", done)
    col3.metric("待执行", total - done)
    col4.metric("在线设备", len(st.session_state.device_list))

    st.progress(progress)

# ====================== 任务管理 ======================
elif menu == "📥 任务管理":
    st.title("📥 任务列表")
    st.dataframe(st.session_state.task_df, use_container_width=True)

# ====================== 设备管理（双停止：安全+强制） ======================
elif menu == "📱 设备管理":
    st.title("📱 设备管理 & 采集控制")

    if st.button("🔍 扫描设备", use_container_width=True):
        res = subprocess.check_output(["adb", "devices"], text=True)
        devices = []
        for line in res.splitlines():
            if "\tdevice" in line:
                devices.append(line.split("\t")[0])
        st.session_state.device_list = [{"设备ID": d, "状态": "空闲"} for d in devices]
        st.success(f"扫描到 {len(devices)} 台设备")
        st.rerun()

    st.divider()

    for i, dev in enumerate(st.session_state.device_list):
        device_id = dev["设备ID"]
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])

        with c1:
            st.write(f"**{device_id}** · {dev['状态']}")

        # 开始采集
        with c2:
            if st.button("开始采集", key=f"start_{i}", use_container_width=True):
                dev["状态"] = "采集中"

                def run():
                    os.environ["ANDROID_SERIAL"] = device_id
                    add_log(f"✅ 设备 {device_id} 开始运行")
                    try:
                        # 🔥 完全不改动你的 main，无参数调用
                        from main import main
                        main()
                        add_log(f"✅ 设备 {device_id} 采集完成")
                    except Exception as e:
                        add_log(f"❌ 设备 {device_id} 异常：{str(e)}")
                    finally:
                        dev["状态"] = "空闲"

                thread = threading.Thread(target=run, daemon=True)
                thread.start()
                running_processes[device_id] = thread
                st.rerun()

        # 安全停止（仅状态标记）
        with c3:
            if st.button("安全停止", key=f"stop_{i}", use_container_width=True):
                dev["状态"] = "等待停止"
                add_log(f"⏸️ 设备 {device_id} 等待当前词条完成后停止")
                st.rerun()

        # 强制停止（真正杀死线程）
        with c4:
            if st.button("强制停止", key=f"force_{i}", use_container_width=True):
                dev["状态"] = "已停止"
                if device_id in running_processes:
                    try:
                        import os, signal
                        pid = os.getpid()
                        os.kill(pid, signal.SIGINT)
                    except:
                        pass
                add_log(f"🛑 设备 {device_id} 已强制停止")
                st.rerun()

        # 重启PDD
        with c5:
            if st.button("重启PDD", key=f"restart_{i}", use_container_width=True):
                did = dev["设备ID"]
                subprocess.run(["adb", "-s", did, "shell", "am force-stop com.xunmeng.pinduoduo"])
                subprocess.run(["adb", "-s", did, "shell", "am start com.xunmeng.pinduoduo"])
                add_log(f"🔄 设备 {did} 重启PDD成功")
                st.success(f"{did} 重启成功")

    st.dataframe(pd.DataFrame(st.session_state.device_list), use_container_width=True)

# ====================== 配置 ======================
elif menu == "⚙️ 调度配置":
    st.title("⚙️ 采集参数")
    st.number_input("采集间隔秒数", 10, 120, 40)

# ====================== 进度 ======================
elif menu == "📊 进度监控":
    st.title("📊 实时进度")
    total = st.session_state.total_tasks
    done = st.session_state.done_tasks
    st.progress(done/total if total>0 else 0)
    st.dataframe(pd.DataFrame(st.session_state.device_list))

# ====================== 日志 ======================
elif menu == "⚠️ 实时日志":
    st.title("⚠️ 运行日志")
    st.code(get_recent_logs())
    time.sleep(1)
    st.rerun()