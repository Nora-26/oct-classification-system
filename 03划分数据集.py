#导入操作系统接口模块，用于处理文件路径。创建目录等
import os
#导入shutil模块，用于复制文件和目录
import shutil
#导入random模块，用于生成随机数
import random
#导入defaultdict模块，用于创建默认字典
from collections import defaultdict

# ============ 配置参数 ============
# 原始数据集路径
SOURCE_DIR = "E:\Graduation project\OCT2017"   # 该目录下包含 train 和 test 两个子文件夹，每个子文件夹内有四个类别文件夹

# 目标目录（采样后的数据集放在这里）
TARGET_DIR = "E:\Graduation project\datasets"

# 目标总图像数（约5000张）
TOTAL_IMAGES = 5000

# 每个类别在训练、验证、测试中的比例（占总样本的比例）
# 训练60%，验证20%，测试20%
TRAIN_RATIO = 0.6
VAL_RATIO = 0.2
TEST_RATIO = 0.2

# 随机种子，保证每次运行结果可重复
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# 类别名称（与原始文件夹名一致）
CLASS_NAMES = ["NORMAL", "CNV", "DME", "DRUSEN"]

# ============ 函数：获取所有图像路径 ============
def get_image_paths(source_dir):
    """遍历源目录下的 train 和 test 子文件夹，收集所有图像路径，按类别组织"""
    # 创建默认字典，用于存储每个类别的图像路径
    class_to_paths = defaultdict(list)
    # 遍历源目录下的 train 和 test 子文件夹
    for subdir in ["train", "test"]:
        # 拼接子文件夹路径
        sub_path = os.path.join(source_dir, subdir)
        # 如果子文件夹不存在，则跳过
        if not os.path.isdir(sub_path):
            continue
        # 遍历每个类别文件夹
        for class_name in CLASS_NAMES:
            # 拼接类别文件夹路径
            class_dir = os.path.join(sub_path, class_name)
            # 如果类别文件夹不存在，则跳过
            if not os.path.isdir(class_dir):
                continue
            # 遍历类别文件夹下的所有文件
            for fname in os.listdir(class_dir):
                # 如果文件名以 jpg、jpeg、png、bmp、tif 结尾，则添加到字典中
                if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tif')):
                    # 拼接文件路径
                    full_path = os.path.join(class_dir, fname)
                    # 将文件路径添加到字典中    
                    class_to_paths[class_name].append(full_path)
    return class_to_paths

# ============ 采样并划分 ============
def sample_and_split(class_to_paths, total_target, train_ratio, val_ratio, test_ratio):
    """为每个类别采样，并划分训练/验证/测试，返回字典"""
    num_classes = len(CLASS_NAMES)
    # 期望每个类别的总样本数（总目标 / 类别数）
    target_per_class = total_target // num_classes
    # 实际可能因为除不尽，最后调整
    remaining = total_target - target_per_class * num_classes

    # 创建字典，用于存储每个类别的训练、验证、测试图像路径
    split_data = {cls: {"train": [], "val": [], "test": []} for cls in CLASS_NAMES}
    
    for i, cls in enumerate(CLASS_NAMES):
        # 该类别可用的总图像数
        available = len(class_to_paths[cls])
        # 目标采样数：基础值 + 额外（前 remaining 个类别各多一张）
        target = target_per_class + (1 if i < remaining else 0)
        if target > available:
            print(f"警告：类别 {cls} 只有 {available} 张图像，但目标采样 {target} 张，将使用全部可用图像。")
            target = available
        
        # 无放回地随机采样 target 张图像，确保同一类别内的图像不会重复出现
        selected = random.sample(class_to_paths[cls], target)
        
        # 按比例划分训练、验证、测试
        n_train = int(target * train_ratio)#训练集图像数
        n_val = int(target * val_ratio)#验证集图像数
        n_test = target - n_train - n_val  #测试集图像数
        
        # 随机打乱顺序后再切分
        random.shuffle(selected)
        split_data[cls]["train"] = selected[:n_train]
        split_data[cls]["val"] = selected[n_train:n_train+n_val]
        split_data[cls]["test"] = selected[n_train+n_val:]
    
    return split_data

# ============ 复制文件到目标目录 ============
def copy_files(split_data, target_dir):
    """将 split_data 中的文件复制到 target_dir/{train,val,test}/{class_name}/ 下"""
    for phase in ["train", "val", "test"]:
        #拼接阶段目录路径
        phase_dir = os.path.join(target_dir, phase)
        #创建阶段目录
        os.makedirs(phase_dir, exist_ok=True)
        #遍历每个类别
        for cls in CLASS_NAMES:
            #拼接类别目录路径
            cls_dir = os.path.join(phase_dir, cls)
            #创建类别目录
            os.makedirs(cls_dir, exist_ok=True)
            #遍历每个图像路径
            for src_path in split_data[cls][phase]:
                #拼接目标路径
                dst_path = os.path.join(cls_dir, os.path.basename(src_path))
                #复制图像到目标路径
                shutil.copy2(src_path, dst_path)
                
                
    print("文件复制完成。")

# ============ 主程序 ============
if __name__ == "__main__":
    print("正在扫描原始图像...")
    class_to_paths = get_image_paths(SOURCE_DIR)
    
    print("各类别图像数量：")
    for cls in CLASS_NAMES:
        print(f"  {cls}: {len(class_to_paths[cls])}")
    
    print(f"目标总图像数：{TOTAL_IMAGES}")
    split_data = sample_and_split(class_to_paths, TOTAL_IMAGES, TRAIN_RATIO, VAL_RATIO, TEST_RATIO)
    
    # 输出划分统计
    print("划分结果：")
    for cls in CLASS_NAMES:
        print(f"  {cls}: 训练 {len(split_data[cls]['train'])}，验证 {len(split_data[cls]['val'])}，测试 {len(split_data[cls]['test'])}")
    
    # 创建目标目录并复制文件
    copy_files(split_data, TARGET_DIR)
    print("全部完成。")