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
    allow_origins=["*"],  # 테스트를 위해 일시적으로 모든 접속 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 미국 서버가 가동 중입니다!"}

APP_AI_KEY = os.getenv("APP_AI_KEY")
client = genai.Client(api_key=APP_AI_KEY)

# [중요] 서버 시작 시 사용 가능한 모델 목록을 로그에 찍어줍니다.
@app.on_event("startup")
async def list_models():
    print("--- 사용 가능한 모델 목록 ---")
    try:
        for m in client.models.list():
            print(f"Model: {m.name}")
    except Exception as e:
        print(f"모델 목록 확인 실패: {e}")

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))

        prompt = "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON으로만 대답해줘."
        
        # 404 에러를 피하기 위해 가장 표준적인 이름을 사용합니다.
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[img, prompt]
        )
        
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)

    except Exception as e:
        print(f"Error detail: {str(e)}")
        raise HTTPException(status_code=500, detail="악보 분석 중 오류가 발생했습니다.")







