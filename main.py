import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from PIL import Image

app = FastAPI()

# 목사님의 UI 지침(중앙 정렬 및 모바일 최적화)을 지원하기 위한 CORS 설정입니다. [cite: 2026-02-11]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 유료 등급 서버 가동 중!"}

# 결제 계정이 연결된 API 키를 사용하여 전용 대역폭을 확보합니다. [cite: 2026-02-11]
client = genai.Client(api_key=os.getenv("APP_AI_KEY"))

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    print(">>> [LOG] 악보 분석 요청 수신 (유료 모드)")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # 429 에러 없이 가장 빠르게 응답하는 2.0-flash 모델을 사용합니다. [cite: 2026-02-11]
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=[
                img, 
                "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."
            ]
        )
        
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        print(">>> [LOG] 분석 성공!")
        return json.loads(clean_json)

    except Exception as e:
        print(f">>> [ERROR] 발생 상세: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
