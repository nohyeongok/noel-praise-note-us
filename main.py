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
    return {"message": "노엘의 찬양노트 미국 서버가 가동 중입니다!"}

APP_AI_KEY = os.getenv("APP_AI_KEY")
client = genai.Client(api_key=APP_AI_KEY)

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    # 구글이 허락한 모델 이름을 순서대로 시도합니다.
    # 404나 429 에러를 피하기 위한 '필승 목록'입니다.
    candidate_models = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-8b',
        'gemini-1.5-pro'
    ]
    
    content = await file.read()
    img = Image.open(io.BytesIO(content))
    prompt = "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON으로만 대답해줘."

    last_error = ""
    for model_name in candidate_models:
        try:
            print(f"Trying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=[img, prompt]
            )
            # 성공하면 즉시 결과 반환
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except Exception as e:
            last_error = str(e)
            print(f"Model {model_name} failed: {last_error}")
            continue # 다음 모델로 넘어감

    # 모든 모델이 실패했을 경우
    raise HTTPException(status_code=500, detail=f"모든 모델 접속 실패: {last_error}")
