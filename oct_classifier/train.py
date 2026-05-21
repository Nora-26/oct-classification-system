import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from sklearn.preprocessing import label_binarize
from sklearn.metrics import roc_curve
import config
from data_loader import create_dataloaders
from models import get_model
from train_utils import train_one_epoch, validate, compute_metrics, hyperparameter_search

def main(use_hp_search=False):
    # 使用全局配置作为默认值
    batch_size = config.BATCH_SIZE
    lr = config.LEARNING_RATE
    wd = config.WEIGHT_DECAY

    if use_hp_search:
        print("开始超参数搜索...")
        best_params = hyperparameter_search(config.DATA_ROOT, num_trials=5)
        print(f"最佳参数: {best_params}")
        batch_size = best_params['batch_size']
        lr = best_params['lr']
        wd = best_params['weight_decay']

    # 创建数据加载器
    train_loader, val_loader, test_loader = create_dataloaders(config.DATA_ROOT, batch_size)

    # 模型、损失、优化器
    model = get_model(config.NUM_CLASSES, pretrained=True).to(config.DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)

    # 训练循环
    best_val_acc = 0
    best_model_state = None
    for epoch in range(1, config.EPOCHS + 1):
        print(f"\nEpoch {epoch}/{config.EPOCHS}")
        train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, criterion, config.DEVICE)
        val_loss, val_acc, val_labels, val_preds, val_probs = validate(model, val_loader, criterion, config.DEVICE)
        scheduler.step(val_loss)
        print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
        print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_state = model.state_dict()
            torch.save(best_model_state, "best_model.pth")
            print("Saved best model.")

    # 加载最佳模型并在测试集上评估
    print("\nTesting best model...")
    model.load_state_dict(torch.load("best_model.pth"))
    test_loss, test_acc, test_labels, test_preds, test_probs = validate(model, test_loader, criterion, config.DEVICE)
    metrics = compute_metrics(test_labels, test_preds, test_probs, config.CLASS_NAMES)
    print("Test Results:")
    for k, v in metrics.items():
        if k not in ['confusion_matrix', 'sensitivities', 'specificities']:
            print(f"{k}: {v:.4f}")
    print("Confusion Matrix:\n", metrics['confusion_matrix'])
    for i, cls in enumerate(config.CLASS_NAMES):
        print(f"{cls} - Sensitivity: {metrics['sensitivities'][i]:.4f}, Specificity: {metrics['specificities'][i]:.4f}")

    # 绘制 ROC 曲线
    if config.NUM_CLASSES == 2:
        fpr, tpr, _ = roc_curve(test_labels, np.array(test_probs)[:, 1])
        plt.plot(fpr, tpr, label=f"AUC = {metrics['auc']:.3f}")
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend()
        plt.show()
    else:
        test_labels_onehot = label_binarize(test_labels, classes=range(config.NUM_CLASSES))
        for i in range(config.NUM_CLASSES):
            fpr, tpr, _ = roc_curve(test_labels_onehot[:, i], np.array(test_probs)[:, i])
            plt.plot(fpr, tpr, label=f"{config.CLASS_NAMES[i]} (AUC={metrics['auc']:.3f})")
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Multiclass ROC Curves')
        plt.legend()
        plt.show()

if __name__ == "__main__":
    main(use_hp_search=False)   # 设为 True 启用超参数搜索