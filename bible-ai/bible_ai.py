from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import google.generativeai as genai

app = FastAPI()

# 1. CORS 설정: noelnote.kr 도메인만 허용
origins = [
    "https://noelnote.kr",
    "https://www.noelnote.kr",
    "http://noelnote.kr",
    "http://www.noelnote.kr",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Gemini AI 설정 (Render의 환경변수 GENAI_API_KEY 사용)
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. 구속사적 관점 시스템 프롬프트
SYSTEM_PROMPT = """
당신은 성경을 '구속사적 관점(Redemptive-Historical Perspective)'으로 해석하는 신학 전문가입니다.
답변 시 다음 원칙을 반드시 지키세요:
1. 모든 성경 사건과 인물을 '예수 그리스도를 통한 하나님의 구원 계획'으로 연결하십시오.
2. 단순한 윤리적 교훈을 넘어 복음의 핵심(은혜, 대속, 완성)을 설명하십시오.
3. 성도들이 성경을 암기하고 묵상할 때 그 의미가 그리스도께 있음을 깨닫게 하십시오.
4. 친절하고 따뜻한 목회자의 어조를 유지하십시오.
"""

class ChatRequest(BaseModel):
    message: str

@app.post("/ask")
async def ask_bible_ai(request: ChatRequest):
    try:
        # 질문에 구속사적 지침을 결합
        prompt = f"{SYSTEM_PROMPT}\n\n사용자 질문: {request.message}"
        response = model.generate_content(prompt)
        return {"answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "Noel Bible AI is online"}
