# 汽车档案系统

名下汽车的全生命周期管理系统：车辆档案、保养维修（OCR/手工录入）、加油油耗、保险、年检、违章、提醒、AI 保养分析。手机端优先，前后端分离。

## 目录结构

```
E:\car\
├── backend/                 # FastAPI 后端（Python 3.12+，venv 在 .venv）
│   ├── app/
│   │   ├── main.py          # 入口 + 定时提醒扫描
│   │   ├── models.py        # 数据模型（14 张表）
│   │   ├── routers/         # 业务路由
│   │   └── services/        # AI/OCR/提醒/油耗服务
│   ├── init_db.py           # 初始化数据库（本机已执行）
│   ├── seed_data.py         # 沃尔沃保养基准等种子数据（随启动自动写入）
│   ├── cleanup_test_data.py # 清理测试数据（已执行）
│   ├── test_api.py          # 后端接口冒烟测试脚本
│   └── start_backend.bat    # 启动后端（端口 8002）
├── frontend/                # Vue3 + Vant4 前端
│   ├── src/views/           # 全部页面
│   └── start_frontend.bat   # 启动前端开发服（端口 5173）
├── start_all.bat            # 一键启动前后端
├── 需求草稿.md
├── 汽车档案系统方案.md        # 方案 v0.2（已评审确认）
└── 部署文档.md               # 腾讯云 8090 部署步骤
```

## 快速开始（本机）

1. 双击 `start_all.bat`（或分别启动 backend / frontend）。
2. 浏览器打开 `http://127.0.0.1:5173`，注册账号。
3. 添加车辆 → 录入保养/加油/保险 → 查看 AI 分析。

## 关键说明

- 数据库：MySQL `car_system`（本机 root/123456，服务器部署见部署文档）。
- AI：规则引擎为底座（保养预测/过度保养/价格估算均有依据）；「设置」中填入 DeepSeek API Key 并启用后，额外生成 AI 自然语言解读；支持添加任意 OpenAI 兼容模型（含视觉模型，用于拍照读单）。
- OCR：支持视觉的模型可拍照识别保养单；DeepSeek 为文本模型，用「粘贴单据文字 → AI 提取字段」通道；原图始终留存。
