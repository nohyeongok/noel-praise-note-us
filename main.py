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
    return {"message": "노엘의 찬양노트 미국 서버가 최종 대기 중입니다!"}

APP_AI_KEY = os.getenv("APP_AI_KEY")
client = genai.Client(api_key=APP_AI_KEY)

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # [중요] 로그에서 확인된 'models/'를 포함한 풀네임을 직접 사용합니다.
        # 구글이 목록에 있다고 시인한 바로 그 이름입니다.
        response = client.models.generate_content(
            model='models/gemini-1.5-flash', 
            contents=[img, "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."]
        )
        
        text_response = response.text
        clean_json = text_response.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)

    except Exception as e:
        print(f"Error detail: {str(e)}")
        # 에러가 나더라도 어떤 모델명에서 에러가 났는지 로그에 남깁니다.
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

