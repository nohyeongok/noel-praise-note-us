import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from PIL import Image

app = FastAPI()

# [cite: 2026-02-11] 모든 접속 경로와 방식을 허용하는 완벽한 보안 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://noelnote.kr",
        "https://www.noelnote.kr",
        "http://noelnote.kr",
        "http://www.noelnote.kr"
    ],
    allow_credentials=True,
    allow_methods=["*"], # GET, POST 등 모든 통신 방식 허용
    allow_headers=["*"], # 모든 데이터 헤더 허용
)

# 서버 연결 확인용 인사말
@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 AI 서버가 준비되었습니다!"}

# 제미나이 AI 설정
GOOGLE_API_KEY = os.getenv("APP_AI_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    try:
        # 1. 업로드된 악보 이미지 읽기
        content = await file.read()
        img = Image.open(io.BytesIO(content))

        # 2. 제미나이에게 내리는 정교한 명령
        prompt = """
        이 악보 이미지를 음악적으로 분석해서 멜로디 데이터를 추출해줘.
        결과는 반드시 다른 설명 없이 아래의 JSON 형식으로만 대답해:
        {
            "melody": [
                {"note": "C4", "duration": "4n", "time": "0:0:0"},
                {"note": "E4", "duration": "4n", "time": "0:1:0"},
                ...
            ]
        }
        - note: C4, D#4, Bb4 형식 (옥타브 포함)
        - duration: 4n(4분음표), 8n(8분음표), 2n(2분음표) 형식
        - time: '마디:박자:하위박자' 형식
        """

        # 3. AI 분석 실행
        response = model.generate_content([prompt, img])
        
        # 4. 응답 텍스트에서 JSON 부분만 정제
        text_result = response.text.replace('```json', '').replace('```', '').strip()
        
        # 5. 결과 반환
        return json.loads(text_result)

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="악보 분석 중 오류가 발생했습니다.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
