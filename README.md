# 眼底 OCT 图像分类系统

基于 EfficientNet-B0 的 OCT 图像四分类系统，支持训练、验证、测试及实时预测。

## 环境配置

1. 确认GPU及驱动

   ```python
   nvidia-smi
   ```

2. 安装python及创建虚拟环境（可选）

   ```
   #安装python版本：Python 3.10.11
   #切换正确的驱动器和目录中
   E：
   cd Graduation project
   cd oct_classifier
   python -m venv 你想要的名字
   #在项目目录下执行
   venv\scripts\activate.bat
   ```

3. 安装Pytorch

   ```
   #访问PyTorch官网选择对应的CUDA版本
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

4. 安装依赖：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

5. 修改 `config.py` 中的 `DATA_ROOT` 为已划分好的数据集根目录（结构见下文）

## 数据集结构

数据集需事先划分为 train/val/test 三个子文件夹，每个子文件夹下包含四个类别文件夹：![{679AA26B-B605-46AD-B31E-3A02B1FB8127}](C:\Users\32720\AppData\Local\Packages\MicrosoftWindows.Client.CBS_cw5n1h2txyewy\TempState\ScreenClip\{679AA26B-B605-46AD-B31E-3A02B1FB8127}.png)

使用00划分数据集.py文件

## 运行训练

```python
python train.py
```

## 运行预测（训练完生成best_model.pth)

