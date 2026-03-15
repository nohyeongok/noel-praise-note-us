from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import google.generativeai as genai

app = FastAPI()

# 1. CORS 설정: noelnote.kr 관련 모든 도메인 허용
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

# 2. Gemini AI 설정 (성공하셨던 2.5 Flash 모델 유지)
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. 구속사적 관점 + 암기 카드 자동 생성 지침
SYSTEM_PROMPT = """
당신은 성경을 '구속사적 관점(Redemptive-Historical Perspective)'으로 해석하는 신학 전문가입니다.
모든 답변은 다음 원칙을 반드시 따릅니다:

1. 성경의 사건과 인물을 예수 그리스도를 통한 하나님의 구원 계획으로 연결하여 설명하십시오.
2. 도덕적 훈계를 넘어 복음의 핵심(은혜, 대속, 완성)을 깊이 있게 다루십시오.
3. 답변의 맨 마지막 줄에는 반드시 [CARD]라는 태그를 붙이고, 전체 내용을 암기하기 좋게 한 줄로 '요약'하십시오.
4. 요약문 안에는 반드시 핵심 성경 구절을 **(성경책 장:절)** 형식으로 '굵게' 포함하십시오.

예시: [CARD] 여자의 후손으로 오신 예수님이 뱀의 머리를 상하게 하심으로 승리하셨습니다. **(창 3:15)**
"""

class ChatRequest(BaseModel):
    message: str

@app.post("/ask")
async def ask_bible_ai(request: ChatRequest):
    try:
        # 시스템 프롬프트와 사용자 질문 결합
        prompt = f"{SYSTEM_PROMPT}\n\n사용자 질문: {request.message}"
        response = model.generate_content(prompt)
        
        if not response.text:
            raise ValueError("AI가 답변을 생성하지 못했습니다.")
            
        return {"answer": response.text}

    except Exception as e:
        # 에러 발생 시 Render 로그에서 상세 내용을 확인할 수 있도록 출력
        print(f"🚨 [에러 발생]: {str(e)}") 
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "Noel Bible AI is online with Memory Card Logic"}
