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
    return {"message": "노엘 뮤직 AI 서버 가동 중 (사운드 최적화 완료)!"}

api_key = os.getenv("APP_AI_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    if not client: return {"melody": []}
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=buffer.getvalue(), mime_type='image/jpeg'),
                "이 악보를 분석해서 JSON으로 변환해줘. 반드시 다음 형식으로만 대답해: {\"melody\": [{\"note\": \"C4\", \"duration\": \"4n\", \"time\": 0.0}]}. 다른 설명은 절대 하지 마."
            ],
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        raw_text = response.text
        if not raw_text: return {"melody": []}
            
        clean_json = raw_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        return {"melody": []}

@app.post("/analyze-xml")
async def analyze_xml(file: UploadFile = File(...)):
    try:
        content = await file.read()
        root = ET.fromstring(content)
        melody_data = []
        divisions = 1
        div_node = root.find('.//divisions')
        if div_node is not None: divisions = int(div_node.text)
        
        seconds_per_beat = 0.5 
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
                    note_name = f"{pitch.find('step').text}{pitch.find('octave').text}"
                    alter = pitch.find('alter')
                    if alter is not None:
                        if alter.text == '1': note_name = note_name.replace(note_name[0], note_name[0] + '#')
                        elif alter.text == '-1': note_name = note_name.replace(note_name[0], note_name[0] + 'b')
                    
                    melody_data.append({
                        "note": note_name, 
                        "duration": f"{note_dur_sec}s", # 💡 XML의 정확한 초(seconds)를 전달합니다!
                        "time": float(current_time) 
                    })
                    current_time += note_dur_sec
                    
        return {"melody": melody_data}
    except Exception as e:
        return {"melody": []}
