import torch
import torch.nn as nn
import cv2
import numpy as np
from torchvision.models import efficientnet_b0
from monai.transforms import Compose, Resize, ScaleIntensity

CLASS_NAMES = ["NORMAL", "CNV", "DME", "DRUSEN"]
NUM_CLASSES = len(CLASS_NAMES)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DISEASE_INFO = {
    "NORMAL": {
        "name": "正常",
        "icon": "✅",
        "description": "眼底视网膜结构正常，未见明显病变。",
        "recommendation": "建议定期进行眼科检查，保持良好的用眼习惯。"
    },
    "CNV": {
        "name": "脉络膜新生血管",
        "icon": "🩸",
        "description": "脉络膜异常血管生长，常见于湿性年龄相关性黄斑变性。",
        "recommendation": "建议尽快就医，可能需要抗VEGF治疗。"
    },
    "DME": {
        "name": "糖尿病黄斑水肿",
        "icon": "🔴",
        "description": "糖尿病引起的黄斑区视网膜增厚和液体渗漏。",
        "recommendation": "建议内分泌科和眼科联合治疗，严格控制血糖。"
    },
    "DRUSEN": {
        "name": "玻璃膜疣",
        "icon": "🟡",
        "description": "视网膜下黄色沉积物，是年龄相关性黄斑变性早期表现。",
        "recommendation": "建议定期复查，监测黄斑变性进展。"
    }
}

def get_model(num_classes, pretrained=False):
    model = efficientnet_b0(weights=None)
    original_conv = model.features[0][0]
    new_conv = nn.Conv2d(1, original_conv.out_channels,
                         kernel_size=original_conv.kernel_size,
                         stride=original_conv.stride,
                         padding=original_conv.padding,
                         bias=False)
    model.features[0][0] = new_conv
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model

def anisotropic_diffusion(img, iterations=5, k=50, gamma=0.1):
    try:
        img_uint8 = (img * 255).astype(np.uint8)
        img_3ch = cv2.cvtColor(img_uint8, cv2.COLOR_GRAY2BGR)
        diffused_3ch = cv2.ximgproc.anisotropicDiffusion(img_3ch, gamma, k, iterations)
        diffused = cv2.cvtColor(diffused_3ch, cv2.COLOR_BGR2GRAY)
        return diffused.astype(np.float32) / 255.0
    except Exception:
        return img

def gaussian_blur(img, kernel_size=3):
    if kernel_size % 2 == 0:
        kernel_size += 1
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

def preprocess_image(image_np):
    if image_np.max() > 1.0:
        image_np = image_np / 255.0
    blurred = gaussian_blur(image_np, kernel_size=3)
    diffused = anisotropic_diffusion(blurred)
    return diffused

class OCTPredictor:
    def __init__(self, model_path, class_names, device=DEVICE):
        self.device = device
        self.class_names = class_names
        self.model = get_model(len(class_names), pretrained=False).to(device)
        self.model.load_state_dict(torch.load(model_path, map_location=device))
        self.model.eval()
        self.transform = Compose([
            Resize((512, 512)),
            ScaleIntensity(minv=0.0, maxv=1.0)
        ])
        self.preprocess_func = preprocess_image

    def predict_from_array(self, img_gray: np.ndarray):
        """直接传入灰度 numpy 数组进行预测"""
        img = self.preprocess_func(img_gray)
        img_tensor = torch.from_numpy(img).float().unsqueeze(0)
        with torch.no_grad():
            img_tensor = self.transform(img_tensor)
            img_batch = img_tensor.unsqueeze(0).to(self.device)
            outputs = self.model(img_batch)
            probs = torch.softmax(outputs, dim=1)
            conf, pred = torch.max(probs, dim=1)
            class_name = self.class_names[pred.item()]
            confidence = conf.item()
            all_probs = probs.cpu().numpy()[0]
        return class_name, confidence, all_probs

    def generate_overlay(self, img_gray: np.ndarray, class_name: str):
        """直接接收灰度数组，返回叠加标注的彩色图像（RGB）"""
        color_img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
        h, w = img_gray.shape
        if class_name == "CNV":
            overlay = color_img.copy()
            cv2.circle(overlay, (w//2, h//2), 100, (0,0,255), -1)
            alpha = 0.4
            color_img = cv2.addWeighted(overlay, alpha, color_img, 1-alpha, 0)
        elif class_name == "DME":
            overlay = color_img.copy()
            cv2.rectangle(overlay, (w//3, h//3), (2*w//3, 2*h//3), (0,165,255), -1)
            alpha = 0.4
            color_img = cv2.addWeighted(overlay, alpha, color_img, 1-alpha, 0)
        elif class_name == "DRUSEN":
            overlay = color_img.copy()
            for _ in range(10):
                x = np.random.randint(w//4, 3*w//4)
                y = np.random.randint(h//4, 3*h//4)
                cv2.circle(overlay, (x, y), 5, (0,255,255), -1)
            alpha = 0.3
            color_img = cv2.addWeighted(overlay, alpha, color_img, 1-alpha, 0)
        return color_img
