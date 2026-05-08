# run_collector.py
# 作用：给看板调用，启动你的采集脚本
import sys
import os

# 接收设备ID参数（从看板传过来）
device_id = sys.argv[1] if len(sys.argv) > 1 else None

# 设置环境变量，让uiautomator2连接指定设备
if device_id:
    os.environ["ANDROID_SERIAL"] = device_id

print(f"✅ 启动采集任务 | 设备：{device_id}")

# 这里直接运行你原来的采集主文件！
# 你的采集脚本叫什么，就写什么（默认是 main.py）
import main