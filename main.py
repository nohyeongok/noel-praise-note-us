import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from PIL import Image

app = FastAPI()

# 2월 11일에 말씀하신 디자인 지침(중앙 정렬 등)이 잘 반영되도록 서버 설정을 유지합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 미국 서버가 최종 응답 대기 중입니다!"}

APP_AI_KEY = os.getenv("APP_AI_KEY")
# 가장 기본 설정으로 클라이언트를 생성합니다.
client = genai.Client(api_key=APP_AI_KEY)

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # 모델 이름을 'models/' 없이 가장 단순한 별칭으로 부릅니다.
        # 구글 SDK가 내부적으로 가장 잘 알아듣는 방식입니다.
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=[
                img, 
                "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."
            ]
        )
        
        text_response = response.text
        # 결과에서 불필요한 마크다운 기호를 제거합니다.
        clean_json = text_response.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)

    except Exception as e:
        print(f"Error detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 시도 중 오류 발생: {str(e)}")

