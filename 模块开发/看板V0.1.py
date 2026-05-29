import streamlit as st
import pandas as pd
import subprocess
import os

# -------------------------- 全局配置 & 默认任务路径 --------------------------
st.set_page_config(page_title="多机群控采集系统", layout="wide", initial_sidebar_state="expanded")
DEFAULT_TASK_PATH = "/2026-4 群控/yolo/整合详情页采集/测试用例.xlsx"

# 初始化全局状态
if "task_df" not in st.session_state:
    st.session_state.task_df = pd.DataFrame()
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "use_custom_file" not in st.session_state:
    st.session_state.use_custom_file = False
# 设备列表：设备ID、状态 空闲/采集中/下线
if "device_list" not in st.session_state:
    st.session_state.device_list = []

# 首次自动加载默认任务文件
if not st.session_state.use_custom_file and os.path.exists(DEFAULT_TASK_PATH):
    try:
        df = pd.read_excel(DEFAULT_TASK_PATH)
        st.session_state.task_df = df
        st.session_state.tasks = df.iloc[:, 0].dropna().tolist()
    except:
        pass

# -------------------------- 侧边栏菜单 --------------------------
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "🏠 数据概览"

with st.sidebar:
    st.markdown("### 🤖 多机群控采集系统")
    st.divider()

    menus = [
        "🏠 数据概览",
        "📥 任务管理",
        "📱 设备管理",
        "⚙️ 调度配置",
        "📊 进度监控",
        "⚠️ 异常日志"
    ]
    for m in menus:
        if st.button(m, use_container_width=True):
            st.session_state.current_menu = m

menu = st.session_state.current_menu

# ===================== 1. 数据概览 =====================
if menu == "🏠 数据概览":
    st.title("📊 系统运行总览")
    device_count = len(st.session_state.device_list)
    task_count = len(st.session_state.tasks)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("在线设备", device_count)
    c2.metric("总任务数", task_count)
    c3.metric("已完成", 0)
    c4.metric("待采集", task_count)

    st.divider()
    st.subheader("📋 当前任务预览")
    if not st.session_state.task_df.empty:
        st.dataframe(st.session_state.task_df.head(10), use_container_width=True)
    else:
        st.warning("未加载任何任务文件")

# ===================== 2. 任务管理 =====================
elif menu == "📥 任务管理":
    st.title("📥 任务导入管理")
    st.info(f"默认任务路径：\n{DEFAULT_TASK_PATH}")

    if st.button("🔄 恢复使用默认任务文件", use_container_width=True):
        st.session_state.use_custom_file = False
        if os.path.exists(DEFAULT_TASK_PATH):
            df = pd.read_excel(DEFAULT_TASK_PATH)
            st.session_state.task_df = df
            st.session_state.tasks = df.iloc[:, 0].dropna().tolist()
            st.success("已切回默认搜索名单.xlsx")

    st.divider()
    st.subheader("手动上传其他Excel")
    uploaded_file = st.file_uploader("上传自定义任务Excel", type=["xlsx", "csv"])
    if uploaded_file is not None:
        st.session_state.use_custom_file = True
        df = pd.read_excel(uploaded_file)
        st.session_state.task_df = df
        st.session_state.tasks = df.iloc[:, 0].dropna().tolist()
        st.success(f"✅ 已加载 {len(st.session_state.tasks)} 条任务")

    st.divider()
    st.subheader("当前任务列表")
    st.dataframe(st.session_state.task_df, use_container_width=True)

# ===================== 3. 设备管理：表格 + 右侧操作按钮 =====================
elif menu == "📱 设备管理":
    st.title("📱 设备管理 & 状态控制")

    # 扫描设备按钮
    if st.button("🔍 重新扫描ADB设备", use_container_width=True):
        try:
            result = subprocess.check_output(["adb", "devices"], text=True)
            online_devs = []
            for line in result.strip().splitlines()[1:]:
                if line.strip() and "\tdevice" in line:
                    online_devs.append(line.split("\t")[0])
            # 初始化设备状态：默认空闲
            dev_list = []
            for dev in online_devs:
                dev_list.append({"设备ID": dev, "当前状态": "空闲"})
            st.session_state.device_list = dev_list
            st.success(f"✅ 扫描到 {len(online_devs)} 台在线设备")
        except Exception as e:
            st.error(f"ADB异常：{e}")

    st.divider()
    st.subheader("设备列表 & 操作")

    dev_list = st.session_state.device_list
    if dev_list:
        # 遍历每一台设备，一行：信息 + 四个操作按钮
        for idx, item in enumerate(dev_list):
            dev_id = item["设备ID"]
            status = item["当前状态"]

            # 分栏：左边信息，右边按钮组
            col_info, col1, col2, col3, col4 = st.columns([3,1,1,1,1])
            with col_info:
                st.markdown(f"**{dev_id}** ｜ 状态：`{status}`")

            # 设为空闲
            with col1:
                if st.button("空闲", key=f"idle_{idx}", use_container_width=True):
                    st.session_state.device_list[idx]["当前状态"] = "空闲"
                    st.rerun()
            # 开始采集
            with col2:
                if st.button("采集", key=f"run_{idx}", use_container_width=True):
                    st.session_state.device_list[idx]["当前状态"] = "采集中"
                    st.rerun()
            # 设为下线
            with col3:
                if st.button("下线", key=f"off_{idx}", use_container_width=True):
                    st.session_state.device_list[idx]["当前状态"] = "下线"
                    st.rerun()
            # 重启PDD
            with col4:
                if st.button("重启PDD", key=f"restart_{idx}", use_container_width=True):
                    try:
                        subprocess.run(["adb", "-s", dev_id, "shell", "am force-stop com.xunmeng.pinduoduo"], timeout=5)
                        subprocess.run(["adb", "-s", dev_id, "shell", "am start com.xunmeng.pinduoduo"], timeout=5)
                        st.success(f"{dev_id} 已重启拼多多")
                    except:
                        st.error(f"{dev_id} 重启失败")

        st.divider()
        # 汇总设备表格
        st.subheader("设备状态总表")
        df_dev = pd.DataFrame(st.session_state.device_list)
        st.dataframe(df_dev, use_container_width=True)

    else:
        st.info("请先点击【重新扫描ADB设备】")

# ===================== 4. 调度配置 =====================
elif menu == "⚙️ 调度配置":
    st.title("⚙️ 采集调度配置")
    st.number_input("采集间隔（秒）", 3, 120, 10)
    st.checkbox("异常自动重试", True)
    st.checkbox("多设备并发采集", True)

# ===================== 5. 进度监控 =====================
elif menu == "📊 进度监控":
    st.title("📊 任务进度监控")
    st.progress(0)
    st.info("等待采集任务启动...")

# ===================== 6. 异常日志 =====================
elif menu == "⚠️ 异常日志":
    st.title("⚠️ 系统异常日志")
    log_txt = """
2026-05-08 11:30:10  设备  元素定位超时
2026-05-08 11:31:22  设备  触发风控，进入休息
2026-05-08 11:32:05  关键词  校验不通过，标记待复核
"""
    st.code(log_txt, language="text")
    if st.button("🗑️ 清空日志"):
        st.info("日志已清空")