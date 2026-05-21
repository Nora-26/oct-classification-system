import os
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
import cv2
import monai
from monai.transforms import Compose, Resize, ScaleIntensity, RandGaussianNoise
import config

# -------------------- 图像预处理函数 --------------------
def anisotropic_diffusion(img, iterations=5, k=50, gamma=0.1):
    """
    各向异性扩散滤波 (Perona-Malik)，支持灰度图输入
    img: numpy array, shape (H,W), dtype float32, 范围 [0,1]
    返回滤波后的图像
    """
    try:
        # 转换为 8UC1 (0-255)
        img_uint8 = (img * 255).astype(np.uint8)
        # 复制为三通道（OpenCV 要求）
        img_3ch = cv2.cvtColor(img_uint8, cv2.COLOR_GRAY2BGR)
        # 各向异性扩散
        diffused_3ch = cv2.ximgproc.anisotropicDiffusion(img_3ch, gamma, k, iterations)
        # 转回灰度图
        diffused = cv2.cvtColor(diffused_3ch, cv2.COLOR_BGR2GRAY)
        return diffused.astype(np.float32) / 255.0
    except ImportError:
        print("Warning: opencv-contrib-python not installed, skipping anisotropic diffusion.")
        return img
    except cv2.error as e:
        print(f"Anisotropic diffusion error: {e}, skipping.")
        return img

def gaussian_blur(img, kernel_size=3):
    """小核高斯滤波"""
    if kernel_size % 2 == 0:
        kernel_size += 1
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

def preprocess_image(image_np):
    """
    完整的预处理流水线:
    1. 高斯滤波 (核大小3)
    2. 各向异性扩散 (边缘保持)
    （尺寸调整和归一化由 MONAI transform 完成）
    """
    if image_np.max() > 1.0:
        image_np = image_np / 255.0
    blurred = gaussian_blur(image_np, kernel_size=3)
    diffused = anisotropic_diffusion(blurred)
    return diffused

# -------------------- 自定义 Dataset --------------------
class OCTDataset(Dataset):
    def __init__(self, root_dir, class_names, transform=None, preprocess_func=None):
        self.samples = []
        self.class_to_idx = {cls: idx for idx, cls in enumerate(class_names)}
        for cls_name in class_names:
            cls_path = os.path.join(root_dir, cls_name)
            if not os.path.isdir(cls_path):
                continue
            for fname in os.listdir(cls_path):
                if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    self.samples.append((os.path.join(cls_path, fname), self.class_to_idx[cls_name]))
        self.transform = transform
        self.preprocess_func = preprocess_func

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            # 尝试用 MONAI 加载
            img = monai.transforms.LoadImage()(img_path)
            if len(img.shape) == 3:
                img = img[0]
        if self.preprocess_func:
            img = self.preprocess_func(img)
        img_tensor = torch.from_numpy(img).float().unsqueeze(0)  # (1,H,W)
        if self.transform:
            img_tensor = self.transform(img_tensor)
        return img_tensor, label

# -------------------- 构建数据流水线 --------------------
def get_transform(mode='train'):
    """返回 MONAI 复合变换"""
    if mode == 'train':
        transform = Compose([
            Resize(config.IMG_SIZE),
            ScaleIntensity(minv=0.0, maxv=1.0),
            RandGaussianNoise(prob=0.5, mean=0.0, std=0.05)
        ])
    else:
        transform = Compose([
            Resize(config.IMG_SIZE),
            ScaleIntensity(minv=0.0, maxv=1.0)
        ])
    return transform

def create_dataloaders(data_root, batch_size):
    """创建训练、验证、测试数据加载器"""
    train_dir = os.path.join(data_root, 'train')
    val_dir = os.path.join(data_root, 'val')
    test_dir = os.path.join(data_root, 'test')

    train_dataset = OCTDataset(train_dir, config.CLASS_NAMES,
                               transform=get_transform('train'),
                               preprocess_func=preprocess_image)
    val_dataset = OCTDataset(val_dir, config.CLASS_NAMES,
                             transform=get_transform('val'),
                             preprocess_func=preprocess_image)
    test_dataset = OCTDataset(test_dir, config.CLASS_NAMES,
                              transform=get_transform('val'),
                              preprocess_func=preprocess_image)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    return train_loader, val_loader, test_loader