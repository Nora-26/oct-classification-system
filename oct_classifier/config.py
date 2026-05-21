import torch

# ========== 数据集路径 ==========
# 注意：此处应为划分好的数据集根目录，内部应有 train/val/test 三个子文件夹，
# 每个子文件夹下包含四个类别子文件夹：NORMAL, CNV, DME, DRUSEN
DATA_ROOT = "E:/Graduation project/datasets"   #划分好的数据集根目录

# ========== 类别名称 ==========
CLASS_NAMES = ["NORMAL", "CNV", "DME", "DRUSEN"]
NUM_CLASSES = len(CLASS_NAMES)

# ========== 图像预处理 ==========
IMG_SIZE = (512, 512)

# ========== 训练超参数 ==========
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4

# ========== 设备 ==========
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ========== 随机种子 ==========
SEED = 42

# ========== 超参数搜索空间（可选） ==========
HPARAMS = {
    "learning_rate": [1e-4, 5e-4, 1e-3],
    "batch_size": [16, 32],
    "weight_decay": [1e-4, 1e-5]
}