import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from PIL import Image

app = FastAPI()

# 목사님의 디자인 가이드라인을 준수하며 모든 접속을 허용합니다. [cite: 2026-02-11]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 최종 안정화 서버 가동 중!"}

# [수정] 404 에러를 방지하기 위해 정식 v1 채널로 고정합니다. [cite: 2026-02-11]
client = genai.Client(
    api_key=os.getenv("APP_AI_KEY"),
    http_options={'api_version': 'v1'}
)

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    print(">>> [LOG] 악보 분석 시도 중 (1.5-Flash 표준형)...")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # [수정] v1 채널에서 가장 안정적으로 작동하는 모델명입니다.
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=[
                img, 
                "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘. 다른 설명은 생략해."
            ]
        )
        
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        print(">>> [LOG] 분석 성공!")
        return json.loads(clean_json)

    except Exception as e:
        error_msg = str(e)
        # 구글 한도 초과 시 목사님이 알아보기 쉽게 메시지를 바꿉니다.
        if "429" in error_msg:
            error_msg = "구글 AI가 잠시 바쁩니다. 1분만 기다렸다가 다시 시도해 주세요."
        print(f">>> [ERROR] 발생: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
