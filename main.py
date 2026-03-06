import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from PIL import Image

app = FastAPI()

# 노엘의 찬양노트 전용 보안 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://noelnote.kr", "https://www.noelnote.kr",
        "http://noelnote.kr", "http://www.noelnote.kr"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 미국 서버가 완벽하게 준비되었습니다!"}

APP_AI_KEY = os.getenv("APP_AI_KEY")
client = genai.Client(api_key=APP_AI_KEY)

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))

        # 악보 분석을 위한 가장 효율적인 프롬프트
        prompt = "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."
        
        # 목록에서 확인된 가장 안정적인 모델 'gemini-1.5-flash-8b'를 사용합니다.
        response = client.models.generate_content(
            model='gemini-1.5-flash-8b',
            contents=[img, prompt]
        )
        
        # 구글의 응답에서 JSON만 깔끔하게 추출
        text_response = response.text
        clean_json = text_response.replace('```json', '').replace('```', '').strip()
        
        return json.loads(clean_json)

    except Exception as e:
        print(f"Error detail: {str(e)}")
        raise HTTPException(status_code=500, detail="악보 분석 중 오류가 발생했습니다.")
