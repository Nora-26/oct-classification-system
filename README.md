
# 眼底 OCT 图像智能分类系统

> 基于 EfficientNet-B0 的视网膜 OCT 图像四分类 Web 系统，准确率 **92.60%**

---

## 项目简介

本项目针对眼底相干光层析（OCT）图像，构建了一套完整的智能辅助诊断系统。系统能够自动识别以下四种视网膜病变：

| 类别 | 说明 |
|------|------|
| **NORMAL** | 正常视网膜 |
| **CNV** | 脉络膜新生血管（湿性黄斑变性） |
| **DME** | 糖尿病性黄斑水肿 |
| **DRUSEN** | 玻璃疣（干性黄斑变性早期） |

---

## 系统架构

```
用户上传图片
    ↓
React 前端界面
    ↓
FastAPI 后端接口（/predict）
    ↓
EfficientNet-B0 模型推理
    ↓
返回分类结果 + 可视化标注图
```

---

## 核心指标

- **分类准确率**：92.60%
- **模型架构**：EfficientNet-B0（单通道适配 + 自定义分类头）
- **训练数据**：2,996 张 OCT 图像（均衡采样）
  - NORMAL: 750 张
  - CNV: 750 张
  - DME: 749 张
  - DRUSEN: 747 张

---

## 技术栈

**后端**
- Python 3.10
- FastAPI
- PyTorch + torchvision
- EfficientNet-B0

**前端**
- React
- Axios

---

## 项目结构

```
├── oct_classifier/          # 模型训练与评估
│   ├── config.py            # 配置（路径、超参数、类别）
│   ├── data_loader.py       # 数据预处理与增强
│   ├── models.py            # EfficientNet-B0 模型定义
│   ├── train.py             # 训练主流程
│   ├── train_utils.py       # 训练/验证/评估工具函数
│   ├── evaluate.py          # 测试集评估（混淆矩阵、ROC曲线）
│   ├── predict.py           # 单张图像推理
│   └── best_model.pth       # 训练最佳权重
│
└── oct_web/                 # Web 系统
    ├── backend/
    │   ├── main.py          # FastAPI 服务入口
    │   ├── model.py         # 模型加载与推理
    │   └── requirements.txt
    └── frontend/
        └── src/
            ├── App.js       # 主界面（上传、结果展示、报告导出）
            ├── api.js       # 后端接口调用
            └── App.css
```

---

## 快速启动

### 1. 克隆仓库

```bash
git clone https://github.com/Nora-26/oct-classification-system.git
cd oct-classification-system
```

### 2. 启动后端

```bash
cd oct_web/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. 启动前端

```bash
cd oct_web/frontend
npm install
npm start
```

### 4. 访问系统

打开浏览器访问 `http://localhost:3000`，上传 OCT 图像即可获得分类结果。

---

## 使用说明

1. 点击上传区域，选择眼底 OCT 图像（支持 JPG / PNG）
2. 系统自动调用模型进行推理
3. 页面展示分类结果及置信度
4. 可导出诊断报告

---

## 环境要求

- Python 3.10+
- Node.js 16+
- CUDA 11.8（可选，有 GPU 推理更快）
- PyTorch（对应 CUDA 版本）
