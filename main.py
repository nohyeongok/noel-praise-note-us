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
    return {"message": "노엘의 찬양노트 정식 서버 가동 중!"}

# [핵심] 최신 라이브러리로 정식 채널(v1)만 사용합니다.
client = genai.Client(
    api_key=os.getenv("APP_AI_KEY"),
    http_options={'api_version': 'v1'}
)

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    print(">>> [LOG] 악보 분석 요청 수신!")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # 가장 안정적인 모델명을 사용합니다.
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=[img, "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."]
        )
        
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        print(">>> [LOG] 분석 성공!")
        return json.loads(clean_json)

    except Exception as e:
        print(f">>> [ERROR] 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



