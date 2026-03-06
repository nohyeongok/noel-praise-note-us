import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from PIL import Image

app = FastAPI()

# 2월 11일에 말씀하신 화면 구성 지침을 위해 CORS를 모두 허용합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 표준 서버가 가동 중입니다!"}

# 표준 라이브러리 설정
genai.configure(api_key=os.getenv("APP_AI_KEY"))

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # 목록에서 확인된 1.5-flash 모델을 가장 표준적인 방식으로 호출합니다.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."
        
        response = model.generate_content([img, prompt])
        
        # 결과에서 JSON 텍스트만 깔끔하게 추출
        text_response = response.text
        clean_json = text_response.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)

    except Exception as e:
        print(f"Error detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")


