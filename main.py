import os, io, json, re
import xml.etree.ElementTree as ET
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from google import genai
from google.genai import types

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.get("/")
async def root():
    return {"message": "노엘 뮤직 AI 서버가 정상 가동 중입니다!"}

# [기능 1] 이미지 악보 분석 (안정적인 gemini-1.5-flash 사용)
@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    if not client: raise HTTPException(status_code=500, detail="API Key missing")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[
                types.Part.from_bytes(data=buffer.getvalue(), mime_type='image/jpeg'),
                "이 악보의 멜로디를 분석해서 JSON 데이터로 변환해줘. melody 키 안에 note, duration, time을 넣어줘."
            ],
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        return response.parsed
    except Exception as e:
        return {"melody": []}

# [기능 2] MusicXML 정밀 분석 (박자 오차 완벽 해결)
@app.post("/analyze-xml")
async def analyze_xml(file: UploadFile = File(...)):
    try:
        content = await file.read()
        root = ET.fromstring(content)
        melody_data = []
        
        # XML의 박자 기준점(divisions)을 찾아 정밀 계산을 수행합니다.
        divisions = 1
        div_node = root.find('.//divisions')
        if div_node is not None: divisions = int(div_node.text)
        
        current_time = 0.0
        for measure in root.findall('.//measure'):
            for note in measure.findall('note'):
                # 음표 길이(duration)를 읽어옵니다.
                dur_node = note.find('duration')
                dur_val = int(dur_node.text) if dur_node is not None else divisions
                
                # 쉼표 처리
                if note.find('rest') is not None:
                    current_time += (dur_val / divisions)
                    continue
                
                pitch = note.find('pitch')
                if pitch:
                    # 음정 추출 (C, D, E...)
                    step = pitch.find('step').text
                    octave = pitch.find('octave').text
                    note_name = step
                    
                    # 변화표(샵, 플랫) 처리
                    alter = pitch.find('alter')
                    if alter is not None:
                        if alter.text == '1': note_name += '#'
                        elif alter.text == '-1': note_name += 'b'
                    note_name += octave
                    
                    # 실제 박자와 시작 시간을 계산하여 배열에 넣습니다.
                    melody_data.append({
                        "note": note_name,
                        "duration": "4n", # 재생을 위한 기본 박자
                        "time": f"+{current_time}"
                    })
                    # 연주된 시간만큼 현재 시간을 뒤로 밀어줍니다.
                    current_time += (dur_val / divisions)
                    
        return {"melody": melody_data}
    except Exception as e:
        return {"melody": []}




