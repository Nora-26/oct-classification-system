import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import (
    accuracy_score, recall_score, precision_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve
)
from tqdm import tqdm
import config
from data_loader import create_dataloaders
from models import get_model

def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    for inputs, labels in tqdm(loader, desc="Training"):
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * inputs.size(0)
        preds = torch.argmax(outputs, dim=1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
    avg_loss = total_loss / len(loader.dataset)
    acc = accuracy_score(all_labels, all_preds)
    return avg_loss, acc

def validate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []
    all_probs = []
    with torch.no_grad():
        for inputs, labels in tqdm(loader, desc="Validating"):
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * inputs.size(0)
            probs = torch.softmax(outputs, dim=1)
            preds = torch.argmax(probs, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
    avg_loss = total_loss / len(loader.dataset)
    acc = accuracy_score(all_labels, all_preds)
    return avg_loss, acc, all_labels, all_preds, all_probs

def compute_metrics(labels, preds, probs, class_names):
    """计算多分类指标：准确率、召回率、精确率、F1、AUC、敏感度、特异度"""
    acc = accuracy_score(labels, preds)
    recall = recall_score(labels, preds, average='macro')
    precision = precision_score(labels, preds, average='macro')
    f1 = f1_score(labels, preds, average='macro')
    cm = confusion_matrix(labels, preds)
    sensitivities = []
    specificities = []
    for i in range(len(class_names)):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        tn = cm.sum() - (tp + fn + fp)
        sens = tp / (tp + fn) if (tp + fn) > 0 else 0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        sensitivities.append(sens)
        specificities.append(spec)
    if len(class_names) == 2:
        auc = roc_auc_score(labels, np.array(probs)[:, 1])
    else:
        auc = roc_auc_score(labels, np.array(probs), multi_class='ovr')
    return {
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'auc': auc,
        'sensitivities': sensitivities,
        'specificities': specificities,
        'confusion_matrix': cm
    }

def hyperparameter_search(data_root, num_trials=5):
    """简单的随机搜索，返回最佳参数字典"""
    best_acc = 0
    best_params = None
    for trial in range(num_trials):
        lr = np.random.choice(config.HPARAMS['learning_rate'])
        bs = np.random.choice(config.HPARAMS['batch_size'])
        wd = np.random.choice(config.HPARAMS['weight_decay'])
        print(f"\nTrial {trial+1}: lr={lr}, batch_size={bs}, weight_decay={wd}")
        train_loader, val_loader, _ = create_dataloaders(data_root, batch_size=bs)
        model = get_model(config.NUM_CLASSES, pretrained=True).to(config.DEVICE)
        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
        criterion = nn.CrossEntropyLoss()
        best_val_acc = 0
        for epoch in range(config.EPOCHS):
            train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, criterion, config.DEVICE)
            val_loss, val_acc, _, _, _ = validate(model, val_loader, criterion, config.DEVICE)
            if val_acc > best_val_acc:
                best_val_acc = val_acc
        print(f"Best val acc: {best_val_acc:.4f}")
        if best_val_acc > best_acc:
            best_acc = best_val_acc
            best_params = {'lr': lr, 'batch_size': bs, 'weight_decay': wd}
    return best_params