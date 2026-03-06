import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from PIL import Image

app = FastAPI()

# 2월 11일 지침에 따라 PC/모바일 최적화 환경을 위해 CORS를 모두 허용합니다. [cite: 2026-02-11]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 최종 정밀 서버가 가동 중입니다!"}

# API 키 설정 (가장 단순한 기본 설정으로 복구합니다)
client = genai.Client(api_key=os.getenv("APP_AI_KEY"))

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # [핵심] 목록(162847.jpg)에 있는 모델 중 가장 확실한 'gemini-1.5-flash'를 호출합니다.
        # 앞뒤에 다른 설정을 붙이지 않고 이름만 정확히 전달합니다.
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=[
                img, 
                "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."
            ]
        )
        
        # 결과값 정제
        text_response = response.text
        clean_json = text_response.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)

    except Exception as e:
        print(f"Error detail: {str(e)}")
        # 에러가 나더라도 어떤 에러인지 상세히 출력하여 마지막 단서를 찾습니다.
        raise HTTPException(status_code=500, detail=f"분석 시도 실패: {str(e)}")


