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

# =========================================================
# [기능 1] 이미지 악보 분석 (main1.php 전용)
# =========================================================
@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    if not client: raise HTTPException(status_code=500, detail="API Key missing")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        
        # 모델명을 가장 안정적인 1.5-flash로 고정하여 404 에러를 방지합니다.
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
        print(f">>> [ERROR] 이미지 분석 실패: {str(e)}")
        return {"melody": []}

# =========================================================
# [기능 2] MusicXML 정밀 분석 (main5.html 전용 - 박자 완벽 복구)
# =========================================================
@app.post("/analyze-xml")
async def analyze_xml(file: UploadFile = File(...)):
    try:
        content = await file.read()
        root = ET.fromstring(content)
        melody_data = []
        
        # XML 박자의 기준이 되는 divisions 값을 정확히 찾아야 박자가 꼬이지 않습니다.
        divisions = 1
        div_node = root.find('.//divisions')
        if div_node is not None: divisions = int(div_node.text)
        
        current_time = 0.0
        for measure in root.findall('.//measure'):
            for note in measure.findall('note'):
                # 음표 길이(duration)를 읽어와서 실제 시간으로 환산합니다.
                dur_node = note.find('duration')
                dur_val = int(dur_node.text) if dur_node is not None else divisions
                
                # 쉼표(rest) 처리: 시간만 더하고 소리는 내지 않습니다.
                if note.find('rest') is not None:
                    current_time += (dur_val / divisions)
                    continue
                
                pitch = note.find('pitch')
                if pitch:
                    step = pitch.find('step').text
                    octave = pitch.find('octave').text
                    alter = pitch.find('alter')
                    
                    note_name = step
                    if alter is not None:
                        if alter.text == '1': note_name += '#'
                        elif alter.text == '-1': note_name += 'b'
                    note_name += octave
                    
                    # 계산된 정확한 시간에 음표를 배치합니다.
                    melody_data.append({
                        "note": note_name,
                        "duration": "4n", 
                        "time": f"+{current_time}"
                    })
                    current_time += (dur_val / divisions)
                    
        print(f">>> [LOG] XML 분석 성공! {len(melody_data)}개 음표 추출 완료.")
        return {"melody": melody_data}
    except Exception as e:
        print(f">>> [ERROR] XML 분석 실패: {str(e)}")
        return {"melody": []}




