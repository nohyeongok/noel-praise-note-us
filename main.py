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
    # 서버가 켜질 때 사용 가능한 모델 목록을 로그에 출력합니다.
    print(">>> [DIAGNOSIS] 목사님 계정에서 사용 가능한 모델 목록:")
    try:
        for m in client.models.list():
            print(f" - {m.name}")
    except Exception as e:
        print(f" - 모델 목록 조회 실패: {str(e)}")
    return {"message": "노엘의 찬양노트 지능형 서버 가동 중!"}

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    print(">>> [LOG] 악보 분석 요청 수신 (Tier 1 지능형 모드)")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # 404 에러를 피하기 위해 여러 모델 후보를 순차적으로 시도합니다. [cite: 2026-03-09]
        # 2026년 표준인 gemini-3-flash를 먼저 시도하고 안되면 1.5로 내려갑니다.
        model_candidates = ['gemini-3-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']
        
        response = None
        last_error = ""

        for model_name in model_candidates:
            try:
                print(f">>> [TRY] {model_name} 모델로 시도 중...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        img, 
                        "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."
                    ]
                )
                if response:
                    print(f">>> [SUCCESS] {model_name} 모델로 분석 성공!")
                    break
            except Exception as e:
                last_error = str(e)
                print(f">>> [FAIL] {model_name} 실패: {last_error}")
                continue
        
        if not response:
            raise Exception(f"모든 모델 후보가 실패했습니다. 마지막 에러: {last_error}")

        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)

    except Exception as e:
        print(f">>> [ERROR] 최종 실패 상세: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

