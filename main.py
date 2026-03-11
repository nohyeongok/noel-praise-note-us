import os
import json
import io
import xml.etree.ElementTree as ET
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from google import genai
from google.genai import types

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "노엘 뮤직 AI 서버 가동 중 (BPM 60-400 정밀 조절판)!"}

api_key = os.getenv("APP_AI_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# =========================================================
# [기능 1] 이미지 악보 분석 (Gemini 2.5 Flash 최신 모델)
# =========================================================
@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    if not client: return {"melody": []}
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        
        prompt = """너는 프로 악보 해독가야. 오선지를 정확히 스캔해서 JSON으로 변환해줘.
        형식: {"melody": [{"note": "C4", "duration": "4n", "time": 0.0}]}"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[types.Part.from_bytes(data=buffer.getvalue(), mime_type='image/jpeg'), prompt],
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        return {"melody": []}

# =========================================================
# [기능 2] MusicXML 정밀 분석 (사용자 지정 BPM 60~400 반영)
# =========================================================
@app.post("/analyze-xml")
async def analyze_xml(file: UploadFile = File(...), bpm: float = None):
    try:
        content = await file.read()
        root = ET.fromstring(content)
        melody_data = []
        
        # 💡 [핵심 로직] 우선순위: 사용자 선택(60~400) -> 악보 내부값 -> 기본값(142)
        final_bpm = 142.0 
        
        # 🚀 에러가 났던 지점을 정확한 들여쓰기로 수정했습니다!
        if bpm is not None:
            # 사용자가 선택한 경우 최소 60으로 제한
            final_bpm = max(60.0, bpm)
        else:
            # 사용자가 선택하지 않은 경우 XML 내부 템포 탐색
            tempo_node = root.find('.//per-minute')
            if tempo_node is not None:
                try:
                    final_bpm = float(tempo_node.text)
                except:
                    pass
        
        seconds_per_beat = 60.0 / final_bpm
        
        divisions = 1
        div_node = root.find('.//divisions')
        if div_node is not None: divisions = int(div_node.text)
        
        current_time = 0.0
        for measure in root.findall('.//measure'):
            for note in measure.findall('note'):
                dur_node = note.find('duration')
                if dur_node is None: continue
                
                dur_val = int(dur_node.text)
                note_dur_sec = (dur_val / divisions) * seconds_per_beat
                
                if note.find('rest') is not None:
                    current_time += note_dur_sec
                    continue
                
                pitch = note.find('pitch')
                if pitch:
                    step = pitch.find('step').text
                    octave = pitch.find('octave').text
                    note_name = step
                    alter = pitch.find('alter')
                    if alter is not None:
                        if alter.text == '1': note_name += '#'
                        elif alter.text == '-1': note_name += 'b'
                    note_name += octave
                    
                    melody_data.append({
                        "note": note_name, 
                        "duration": "4n", 
                        "time": float(current_time) 
                    })
                    current_time += note_dur_sec
                    
        return {"melody": melody_data, "applied_bpm": final_bpm}
    except Exception as e:
        print(f">>> [ERROR] XML 분석: {str(e)}")
        return {"melody": []}
