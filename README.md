🛒 电商商品自动化采集系统（PDD）
基于 Python + UIAutomator2 + YOLOv8 + EasyOCR 构建的电商商品数据自动化采集与分析系统，专为拼多多平台设计，实现了从搜索、识别、采集到结构化存储的全流程自动化。

✨ 项目亮点
● 全流程自动化：自动搜索商品、识别标签、采集详情、写入 Excel，无需人工干预
● 多模型融合识别：
  ○ YOLOv8：识别列表页商品标签（百亿补贴/品牌/全球购）
  ○ EasyOCR：商品详情页文本提取
  ○ LLM 语义匹配：基于 GLM-4/本地Qwen-4B 进行商品标题匹配校验
● 数据结构化输出：自动生成标准化 Excel 报表，包含价格、规格、补贴状态、生产日期等字段
● 高优先级策略：优先采集「百亿补贴+品牌」商品，数据更具业务参考价值

🛠️ 技术栈
模块	技术/工具
自动化控制	uiautomator2
目标检测	YOLOv8
OCR识别	easyocr
语义匹配	GLM-4.7-Flash / Qwen-4B
数据处理	pandas / openpyxl
开发语言	Python 3.8+

📦 项目结构
整合详情页采集/
├── main.py              # 主程序入口
├── runs/
│   └── detect/          # YOLOv8 训练模型权重
│       ├── pdd_logo_train-2/
│       ├── subsidy_train/
│       └── product_detail_train/
├── list_screen.jpg      # 列表页截图（调试用）
├── debug_detection.jpg  # YOLO 检测结果（调试用）
├── 商品采集汇总.xlsx    # 采集结果输出文件
└── README.md            # 项目说明文档
📌 使用说明
电脑 USB 连接安卓手机
手机开启【开发者选项】+【USB 调试】
本地部署 Python3.8 及全部第三方依赖库
直接运行采集脚本，全自动执行商品搜索、识别、数据抓取与导出

📷 运行效果展示
<img width="1080" height="2400" alt="image" src="https://github.com/user-attachments/assets/59886c1c-ef89-4324-972a18af"><img width="624" height="1415" alt="image" src="https://github.com/user-attachments/assets/8f94a235-db6c-4933-86e7-2ff969632b7e">```
🛒 电商商品自动化采集系统（PDD）
基于 Python + UIAutomator2 + YOLOv8 + EasyOCR 构建的电商商品数据自动化采集与分析系统，专为拼多多平台设计，实现了从搜索、识别、采集到结构化存储的全流程自动化。

✨ 项目亮点
● 全流程自动化：自动搜索商品、识别标签、采集详情、写入 Excel，无需人工干预
● 多模型融合识别：
  ○ YOLOv8：识别列表页商品标签（百亿补贴/品牌/全球购）
  ○ EasyOCR：商品详情页文本提取
  ○ LLM 语义匹配：基于 GLM-4/本地Qwen-4B 进行商品标题匹配校验
● 数据结构化输出：自动生成标准化 Excel 报表，包含价格、规格、补贴状态、生产日期等字段
● 高优先级策略：优先采集「百亿补贴+品牌」商品，数据更具业务参考价值

🛠️ 技术栈
模块	技术/工具
自动化控制	uiautomator2
目标检测	YOLOv8
OCR识别	easyocr
语义匹配	GLM-4.7-Flash / Qwen-4B
数据处理	pandas / openpyxl
开发语言	Python 3.8+

📦 项目结构
整合详情页采集/
├── main.py              # 主程序入口
├── runs/
│   └── detect/          # YOLOv8 训练模型权重
│       ├── pdd_logo_train-2/
│       ├── subsidy_train/
│       └── product_detail_train/
├── list_screen.jpg      # 列表页截图（调试用）
├── debug_detection.jpg  # YOLO 检测结果（调试用）
├── 商品采集汇总.xlsx    # 采集结果输出文件
└── README.md            # 项目说明文档
📌 使用说明
电脑 USB 连接安卓手机
手机开启【开发者选项】+【USB 调试】
本地部署 Python3.8 及全部第三方依赖库
直接运行采集脚本，全自动执行商品搜索、识别、数据抓取与导出

📷 运行效果展示

<img width="500" alt="image" src="https://github.com/user-attachments/assets/032a32e7-4602-400c-a185-4d3b9119ace4" />
<img width="500" alt="image" src="https://github.com/user-attachments/assets/29d56d94-bf64-46c9-bb18-e220ed82d5ed" />
