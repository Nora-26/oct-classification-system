# 眼底 OCT 图像分类系统网页设计

### 文件目录

```
oct_web/
├── backend/
│   ├── main.py
│   ├── model.py
│   ├── requirements.txt
│   └── best_model.pth          # 请将您的模型文件放在此处
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── api.js
│   │   └── index.js
│   ├── package.json
│   └── README.md
```

安装Node.js

访问[Node.js — 下载 Node.js®](https://nodejs.org/zh-cn/download)官网下载LTS版本（长期支持版）

选择Windows安装包（.msi文件）

安装Node.js

教程：[【2026 最新版】Node.js安装及环境配置超详细教程（以win11为例子）_nodejs安装-CSDN博客](https://blog.csdn.net/little_carter/article/details/157698232?ops_request_misc=elastic_search_misc&request_id=101f8834f544e202125b6b5eeee3e976&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~top_positive~default-1-157698232-null-null.nonlogin&utm_term=nodejs安装及环境配置&spm=1018.2226.3001.4187)

## 运行说明

### 首次运行

#### 后端

```
E:
cd \graduation project\oct_web\backend #切换目录
#创建虚拟环境
python -m venv venv
venv\scripts\activate                  #激活虚拟环境
#安装依赖
pip install -r requirements.txt
#将best_model.pth放入backend目录
uvicorn main:app --reload --port 8000  #启动
```

#### 前端

```
E:
cd \graduation project\oct_web\frontend #切换目录
#安装依赖
npm install
npm start                               #启动开发服务器
```



#### 后端（Fast API）使用虚拟环境(cmd)

```python
E:
cd \graduation project\oct_web\backend #切换目录
venv\scripts\activate                  #激活虚拟环境
uvicorn main:app --reload --port 8000  #启动
```

#### 前端（React）不依赖Python虚拟python虚拟环境(另一个cmd)

```python
E:
cd \graduation project\oct_web\frontend #切换目录
npm start                               #启动开发服务器
```

