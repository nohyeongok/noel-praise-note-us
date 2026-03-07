import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from PIL import Image

app = FastAPI()

# 목사님의 디자인 지침(중앙 정렬 및 모바일 최적화 지원)을 위해 모든 접속을 허용합니다. [cite: 2026-02-11]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 2026 표준 서버 가동 중!"}

# [수정] 2026년 표준 설정으로 변경합니다.
client = genai.Client(api_key=os.getenv("APP_AI_KEY"))

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    print(">>> [LOG] 악보 분석을 시작합니다!") 
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # 2026년 가장 성능이 좋은 최신 모델 이름을 사용합니다.
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=[
                img, 
                "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘. 다른 설명은 하지 말고 JSON만 출력해."
            ]
        )
        
        # 결과값 정제
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        print(">>> [LOG] 분석 성공!")
        return json.loads(clean_json)

    except Exception as e:
        print(f">>> [ERROR] 발생 상세: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 시도 중 오류: {str(e)}")


