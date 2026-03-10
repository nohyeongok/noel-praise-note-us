import os
import json
import io
import xml.etree.ElementTree as ET
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from PIL import Image

app = FastAPI()

# 통신 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘 뮤직 AI 프로 서버가 완벽하게 가동 중입니다!"}

# 💡 목사님의 렌더 서버에 세팅된 환경변수(APP_AI_KEY)를 그대로 사용합니다.
api_key = os.getenv("APP_AI_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# =========================================================
# [기능 1] 이미지 악보 분석 (안정된 라이브러리 + 유료 Pro 모델)
# =========================================================
@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        if img.mode != 'RGB': 
            img = img.convert('RGB')
        
        # 🚀 유료 사용자의 특권: 가장 정밀한 'pro' 모델 적용
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = """이 악보의 멜로디를 정밀 분석해서 JSON으로 변환해줘. 
        반드시 다음 형식으로만 대답해: 
        {"melody": [{"note": "C4", "duration": "4n", "time": "+0.0"}]}
        다른 설명은 절대 하지 마."""
        
        response = model.generate_content([img, prompt])
        
        # 결과에서 JSON 텍스트만 깔끔하게 추출 (기존 성공 로직)
        text_response = response.text
        clean_json = text_response.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)

    except Exception as e:
        print(f">>> [ERROR] 이미지 분석 실패: {str(e)}")
        # 실패 시 빈 배열 반환하여 화면이 멈추지 않도록 함
        return {"melody": []}

# =========================================================
# [기능 2] MusicXML 정밀 분석 (main5.html 용 박자 동기화)
# =========================================================
@app.post("/analyze-xml")
async def analyze_xml(file: UploadFile = File(...)):
    try:
        content = await file.read()
        root = ET.fromstring(content)
        melody_data = []
        
        divisions = 1
        div_node = root.find('.//divisions')
        if div_node is not None: 
            divisions = int(div_node.text)
        
        # BPM 120 속도 기준
        seconds_per_beat = 0.5 
        current_time = 0.0
        
        for measure in root.findall('.//measure'):
            for note in measure.findall('note'):
                dur_node = note.find('duration')
                if dur_node is None: 
                    continue
                
                dur_val = int(dur_node.text)
                note_dur_sec = (dur_val / divisions) * seconds_per_beat
                
                # 쉼표 처리
                if note.find('rest') is not None:
                    current_time += note_dur_sec
                    continue
                
                pitch = note.find('pitch')
                if pitch:
                    note_name = f"{pitch.find('step').text}{pitch.find('octave').text}"
                    melody_data.append({
                        "note": note_name, 
                        "duration": "4n", 
                        "time": f"+{current_time}"
                    })
                    current_time += note_dur_sec
                    
        return {"melody": melody_data}
    except Exception as e:
        print(f">>> [ERROR] XML 분석 실패: {str(e)}")
        return {"melody": []}

