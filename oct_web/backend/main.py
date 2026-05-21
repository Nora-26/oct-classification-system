from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from model import OCTPredictor, DISEASE_INFO, CLASS_NAMES
import base64

app = FastAPI(title="OCT Classification API")

# 允许跨域（前端 React 通常运行在 3000 端口）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加载模型（全局单例）
predictor = OCTPredictor("best_model.pth", CLASS_NAMES)

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise HTTPException(status_code=400, detail="无法解析图像")

        cls, conf, probs = predictor.predict_from_array(img)

        # ---------- 低置信度处理逻辑 ----------
        sorted_probs = sorted(probs, reverse=True)
        highest = sorted_probs[0]
        second = sorted_probs[1]

        if conf < 0.8:
            if (highest - second) < 0.1:
                final_class = "UNCERTAIN"
                final_class_name = "结果不确定"
                final_icon = "❓"
                final_recommendation = "建议结合其他检查（如OCT血管成像、荧光血管造影等）进一步确认。"
                final_description = "模型预测结果置信度较低，且各类别概率接近，无法明确区分。"
            else:
                final_class = cls
                final_class_name = f"疑似 {DISEASE_INFO[cls]['name']}"
                final_icon = DISEASE_INFO[cls]["icon"]
                final_recommendation = f"模型对于此结果置信度较低，建议由专业医生复核。{DISEASE_INFO[cls]['recommendation']}"
                final_description = f"{DISEASE_INFO[cls]['description']} 但模型对此判断信心不足。"
        else:
            final_class = cls
            final_class_name = DISEASE_INFO[cls]["name"]
            final_icon = DISEASE_INFO[cls]["icon"]
            final_recommendation = DISEASE_INFO[cls]["recommendation"]
            final_description = DISEASE_INFO[cls]["description"]

        # 生成标注图
        overlay_bgr = predictor.generate_overlay(img, cls)
        overlay_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)
        _, encoded = cv2.imencode('.png', overlay_rgb)
        overlay_base64 = base64.b64encode(encoded).decode('utf-8')

        result = {
            "class": final_class,
            "class_name": final_class_name,
            "icon": final_icon,
            "confidence": conf,
            "probabilities": {CLASS_NAMES[i]: float(probs[i]) for i in range(len(CLASS_NAMES))},
            "recommendation": final_recommendation,
            "description": final_description,
            "overlay_image": overlay_base64,
            # 可选：原始预测信息
            "original_class": cls,
            "original_confidence": conf,
        }
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))