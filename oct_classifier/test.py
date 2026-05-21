from predict import OCTPredictor
import config

predictor = OCTPredictor("best_model.pth", config.CLASS_NAMES)
cls, conf = predictor.predict(""E:\Graduation project\OCT2017\train\DME\DME-15307-1.jpeg"")   # 替换为实际图像路径
print(cls, conf)