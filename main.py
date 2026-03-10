import os, io, json, re
import xml.etree.ElementTree as ET
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from google import genai
from google.genai import types

app = FastAPI()

# 통신 허용 설정 (이게 있어야 화면에서 서버로 데이터를 보냅니다)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 키 및 클라이언트 설정
api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.get("/")
async def root():
    return {"message": "노엘 뮤직 AI 서버가 정상 가동 중입니다!"}

# [기능 1] 이미지 악보 분석 (최신 Gemini 3 모델)
@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    if not client: raise HTTPException(status_code=500, detail="API Key missing")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        
        # 🚀 2026년 최신 모델 'gemini-3-flash' 적용 [cite: 2026-03-11]
        response = client.models.generate_content(
            model='gemini-3-flash',
            contents=[
                types.Part.from_bytes(data=buffer.getvalue(), mime_type='image/jpeg'),
                "이 악보의 멜로디를 분석해서 연주 가능한 JSON 데이터로 변환해줘. "
                "반드시 melody 키 안에 note, duration, time 정보를 포함해야 해."
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "melody": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "note": {"type": "STRING"},
                                    "duration": {"type": "STRING"},
                                    "time": {"type": "STRING"}
                                },
                                "required": ["note", "duration", "time"]
                            }
                        }
                    },
                    "required": ["melody"]
                }
            )
        )
        return response.parsed
    except Exception as e:
        print(f">>> [ERROR] 이미지 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# [기능 2] MusicXML 정밀 분석 (박자 오차 수정)
@app.post("/analyze-xml")
async def analyze_xml(file: UploadFile = File(...)):
    try:
        content = await file.read()
        root = ET.fromstring(content)
        melody_data = []
        
        divisions = 1
        div_node = root.find('.//divisions')
        if div_node is not None: divisions = int(div_node.text)
        
        current_time = 0.0
        for measure in root.findall('.//measure'):
            for note in measure.findall('note'):
                dur_node = note.find('duration')
                dur_val = int(dur_node.text) if dur_node is not None else divisions
                
                if note.find('rest') is not None:
                    current_time += (dur_val / divisions)
                    continue
                
                pitch = note.find('pitch')
                if pitch:
                    note_name = f"{pitch.find('step').text}{pitch.find('octave').text}"
                    melody_data.append({
                        "note": note_name,
                        "duration": "4n",
                        "time": f"+{current_time}"
                    })
                    current_time += (dur_val / divisions)
                    
        return {"melody": melody_data}
    except Exception as e:
        print(f">>> [ERROR] XML 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


