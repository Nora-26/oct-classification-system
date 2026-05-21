import torch
import cv2
import config
from models import get_model
from data_loader import preprocess_image, get_transform

class OCTPredictor:
    def __init__(self, model_path, class_names, device=config.DEVICE):
        self.device = device
        self.class_names = class_names
        self.model = get_model(len(class_names), pretrained=False).to(device)
        self.model.load_state_dict(torch.load(model_path, map_location=device))
        self.model.eval()
        self.preprocess_func = preprocess_image
        self.transform = get_transform('val')  # 仅 resize + scale

    def predict(self, image_path):
        """输入图像路径，返回预测类别和置信度"""
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Can't read image: {image_path}")
        img = self.preprocess_func(img)
        img_tensor = torch.from_numpy(img).float().unsqueeze(0).unsqueeze(0)  # (1,1,H,W)
        with torch.no_grad():
            img_tensor = self.transform(img_tensor).to(self.device)
            outputs = self.model(img_tensor)
            probs = torch.softmax(outputs, dim=1)
            conf, pred = torch.max(probs, dim=1)
        class_name = self.class_names[pred.item()]
        confidence = conf.item()
        return class_name, confidence