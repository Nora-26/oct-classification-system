# 眼底 OCT 图像分类系统项目文档

## 1. 项目概述

本项目是一个基于深度学习的眼底 OCT 图像分类系统，提供 Web 页面上传与实时推理能力。系统面向医学影像辅助分析场景，实现了从图像上传、模型推理、结果可视化到报告导出的完整链路。

- 前端：React 单页应用，负责图像上传、结果展示和报告生成
- 后端：FastAPI 推理服务，负责图像解码、模型预测、结果封装
- 模型：EfficientNet-B0 改造版（单通道输入），支持 4 类分类

当前分类类别：
- `NORMAL`：正常
- `CNV`：脉络膜新生血管
- `DME`：糖尿病黄斑水肿
- `DRUSEN`：玻璃膜疣

---

## 2. 技术栈

### 2.1 前端
- React 18
- react-scripts (CRA)
- axios
- react-dropzone

### 2.2 后端
- FastAPI
- Uvicorn
- python-multipart
- OpenCV
- PyTorch + TorchVision
- MONAI
- NumPy
- Pillow

---

## 3. 项目结构

```text
oct_web/
├── backend/
│   ├── main.py               # FastAPI 服务入口与接口
│   ├── model.py              # 模型定义、预处理、推理、疾病信息
│   ├── requirements.txt      # Python 依赖
│   └── best_model.pth        # 模型权重文件
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js            # 前端主界面与交互逻辑
│   │   ├── App.css           # 样式
│   │   ├── api.js            # 接口请求封装
│   │   └── index.js          # 前端入口
│   ├── package.json          # Node 依赖与脚本
│   └── package-lock.json
├── README.md                 # 原始运行说明
└── docker-compose.yml        # 当前为空
```

---

## 4. 系统架构与流程

### 4.1 架构说明
- 前端运行在 `http://localhost:3000`
- 后端运行在 `http://localhost:8000`
- 前端通过 HTTP `POST /predict` 上传图像到后端
- 后端返回分类结果、概率分布、病情说明、建议与标注图（Base64）

### 4.2 业务流程
1. 用户在前端上传 OCT 图像（拖拽或选择文件）
2. 前端将文件封装为 `multipart/form-data` 调用后端
3. 后端读取图像并执行预处理与模型推理
4. 后端生成可视化标注图并构造 JSON 返回
5. 前端展示诊断结果，支持导出 HTML 诊断报告

---

## 5. 环境准备与本地运行

## 5.1 前置条件
- Windows/macOS/Linux
- Node.js LTS
- Python 3.9+

### 5.2 启动后端

在 `oct_web/backend` 目录执行：

```bash
python -m venv venv
venv\scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

注意：
- 确保 `best_model.pth` 位于 `backend` 目录
- 首次安装 PyTorch 可能较慢

### 5.3 启动前端

在 `oct_web/frontend` 目录执行：

```bash
npm install
npm start
```

浏览器访问：`http://localhost:3000`

---

## 6. 前端设计说明

核心文件：`frontend/src/App.js`

主要功能：
- 图像拖拽上传（`react-dropzone`）
- 原图 / AI 标注图切换预览
- 分类结果与置信度显示
- 各类别概率分布可视化
- 病情说明与医疗建议展示
- 一键导出 HTML 报告（浏览器打印/保存）

接口调用封装：
- 文件：`frontend/src/api.js`
- 默认后端地址硬编码为 `http://localhost:8000`
- 当前仅使用一个接口：`predictImage(file)`

---

## 7. 后端设计说明

### 7.1 服务入口
文件：`backend/main.py`

实现要点：
- 创建 FastAPI 应用
- 配置 CORS（允许 `http://localhost:3000`）
- 全局加载模型实例：`OCTPredictor("best_model.pth", CLASS_NAMES)`
- 提供 `POST /predict` 推理接口

### 7.2 模型与推理
文件：`backend/model.py`

实现要点：
- 基于 `efficientnet_b0` 改造输入层为单通道
- 分类头修改为 4 分类输出
- 图像预处理：
  - 高斯滤波
  - 各向异性扩散（`cv2.ximgproc`，失败时自动回退）
  - Resize 到 `512x512`（MONAI Transform）
  - 强度归一化
- 推理输出：
  - 预测类别
  - 置信度
  - 全类别概率
- 根据类别返回中文疾病说明与建议

### 7.3 结果可视化
- `CNV`：中心红色半透明圆形叠加
- `DME`：中心区域橙色矩形叠加
- `DRUSEN`：多点黄色斑点叠加
- `NORMAL`：保持原图

---

## 8. API 接口文档

### 8.1 预测接口
- **Method**: `POST`
- **Path**: `/predict`
- **Content-Type**: `multipart/form-data`
- **参数**:
  - `file`：图像文件（必填）

#### 请求示例（curl）
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.png"
```

#### 返回示例
```json
{
  "class": "CNV",
  "class_name": "脉络膜新生血管",
  "icon": "⚠️",
  "confidence": 0.9731,
  "probabilities": {
    "NORMAL": 0.0123,
    "CNV": 0.9731,
    "DME": 0.0102,
    "DRUSEN": 0.0044
  },
  "recommendation": "建议尽快就医，可能需要抗VEGF治疗。",
  "description": "脉络膜异常血管生长，常见于湿性年龄相关性黄斑变性。",
  "overlay_image": "<base64_png>"
}
```

### 8.2 自动 API 文档
- Swagger UI：`http://localhost:8000/docs`
- OpenAPI JSON：`http://localhost:8000/openapi.json`

---

## 9. 配置与依赖

### 9.1 当前配置方式
当前项目主要使用硬编码配置：
- 前端 API 地址：`frontend/src/api.js`
- 后端 CORS 白名单：`backend/main.py`
- 模型路径：`backend/main.py`

### 9.2 建议改造为环境变量
建议新增：
- `API_BASE_URL`（前端）
- `CORS_ORIGINS`（后端）
- `MODEL_PATH`（后端）

---

## 10. 已实现功能清单

- Web 端图像上传与拖拽交互
- 后端单图推理接口
- 4 类 OCT 分类
- 分类概率输出与前端可视化
- AI 标注图生成与展示
- 病情描述与医疗建议展示
- HTML 诊断报告导出

---

## 11. 当前局限与风险

- 工程化不足：`docker-compose.yml` 为空，缺少容器部署能力
- 缺少测试：尚无系统化单元测试与接口测试
- 可配置性不足：关键配置硬编码，不利于多环境部署
- 错误处理可优化：`/predict` 使用宽泛异常捕获，可能掩盖具体错误类型
- 医疗风险提示：当前结果仅适用于辅助分析，不可替代医生诊断

---

## 12. 测试与验证建议

建议补充以下验证流程：

- 接口可用性测试：上传正常图、损坏图、非图像文件
- 模型输出稳定性：同图多次推理一致性验证
- 前端交互测试：上传、切换预览、报告导出
- 端到端测试：前后端联调自动化脚本
- 异常场景测试：后端未启动、模型文件缺失、跨域错误

---

## 13. 部署建议

短期建议：
- 增加 `backend/Dockerfile` 与 `frontend/Dockerfile`
- 完善 `docker-compose.yml`（前后端一键启动）
- 增加基础健康检查接口（如 `/healthz`）

中期建议：
- 引入 CI（如 GitHub Actions）执行安装、构建、测试
- 配置 Nginx 反向代理前端静态资源与后端 API
- 规范日志输出和错误监控

---

## 14. 后续迭代路线（建议）

1. 配置解耦（环境变量与多环境）
2. 增加自动化测试与接口契约
3. 细化异常处理和错误码设计
4. 增加批量推理与历史记录（可选数据库）
5. 提供模型性能指标展示（准确率、召回率、混淆矩阵）

---

## 15. 免责声明

本系统用于医学影像智能分析研究与教学演示，输出结果仅供参考，不构成临床诊断依据。任何诊断与治疗决策应由具备资质的专业医生基于完整临床信息做出。
