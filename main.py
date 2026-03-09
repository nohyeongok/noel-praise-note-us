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

# 목사님의 'Tier 1' API 키 설정
client = genai.Client(api_key=os.getenv("APP_AI_KEY"))

@app.get("/")
async def root():
    return {"message": "노엘의 찬양노트 지능형 서버 가동 중! Render 로그를 확인해 주세요."}

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    print(">>> [LOG] 악보 분석 요청 수신 (Tier 1 자동 탐색 모드)")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # [핵심] 목사님 계정에서 현재 사용 가능한 모델 목록을 실시간으로 가져옵니다. [cite: 2026-02-11]
        available_models = [m.name for m in client.models.list() if 'generateContent' in m.supported_actions]
        print(f">>> [DIAGNOSIS] 현재 사용 가능한 모델들: {available_models}")

        if not available_models:
            raise Exception("사용 가능한 모델이 없습니다. API 활성화 상태를 점검해 주세요.")

        # 2026년 표준인 3-flash나 1.5-flash 계열을 우선적으로 찾습니다. [cite: 2026-03-09]
        target_model = None
        for candidate in ['gemini-3-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-latest']:
            # API가 반환하는 이름 형식(models/...)에 맞게 비교합니다.
            full_name = f"models/{candidate}"
            if full_name in available_models or candidate in available_models:
                target_model = candidate
                break
        
        # 후보가 없으면 목록 중 첫 번째 모델을 선택합니다.
        if not target_model:
            target_model = available_models[0].replace('models/', '')

        print(f">>> [TRY] '{target_model}' 모델로 분석을 시작합니다.")
        
        response = client.models.generate_content(
            model=target_model,
            contents=[
                img, 
                "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."
            ]
        )
        
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        print(f">>> [SUCCESS] {target_model} 모델로 분석 성공!")
        return json.loads(clean_json)

    except Exception as e:
        print(f">>> [ERROR] 상세 사유: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

