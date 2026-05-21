import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

def get_model(num_classes, pretrained=True):
    """
    使用 EfficientNet-B0，修改第一层以接受单通道输入
    """
    model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT if pretrained else None)

    # 定位第一层卷积：model.features[0][0]
    original_conv = model.features[0][0]

    new_conv = nn.Conv2d(1, original_conv.out_channels,
                         kernel_size=original_conv.kernel_size,
                         stride=original_conv.stride,
                         padding=original_conv.padding,
                         bias=False)

    if pretrained:
        with torch.no_grad():
            # 对原权重的通道维度求平均，作为单通道的初始化
            new_conv.weight.data = original_conv.weight.data.mean(dim=1, keepdim=True)

    model.features[0][0] = new_conv

    # 修改分类头
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    return model