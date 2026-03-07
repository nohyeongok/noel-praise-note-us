import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from PIL import Image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 통합 안정화 서버 가동 중!"}

# 가장 표준적인 설정으로 시작합니다. [cite: 2026-02-11]
client = genai.Client(api_key=os.getenv("APP_AI_KEY"))

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    print(">>> [LOG] 악보 분석 요청을 받았습니다.")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # 404 에러가 없는 gemini-2.0-flash를 사용합니다.
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=[img, "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."]
        )
        
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        print(">>> [LOG] 분석 성공!")
        return json.loads(clean_json)

    except Exception as e:
        error_msg = str(e)
        # 한도 초과(429) 발생 시 목사님께 알림
        if "429" in error_msg:
            print(">>> [ERROR] 구글 한도 초과 (429)")
            raise HTTPException(status_code=429, detail="구글 AI 한도가 일시적으로 초과되었습니다. 1분만 기다려주세요.")
        
        print(f">>> [ERROR] 상세 발생: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
