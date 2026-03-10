# main.py의 analyze_sheet 함수 부분을 아래와 같이 수정하세요.
@app.post("/analyze-sheet")
async def analyze_sheet(file: UploadFile = File(...)):
    print(f">>> [LOG] 악보 분석 요청 수신: {file.filename}")
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # BMP 또는 RGBA 형식을 제미나이가 선호하는 RGB/JPEG 형식으로 변환합니다.
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 분석을 위해 메모리 내에서 JPEG로 변환하여 전송 (속도 향상)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        img_to_send = Image.open(buffer)

        # 사용 가능한 모델을 자동으로 찾아 분석 수행
        response = client.models.generate_content(
            model='gemini-2.0-flash-001', # 목사님 계정에서 성공했던 모델
            contents=[
                img_to_send, 
                "이 악보를 분석해서 {melody: [{note: 'C4', duration: '4n', time: '0:0:0'}]} 형식의 JSON 데이터만 출력해줘."
            ]
        )
        
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        print(">>> [LOG] BMP 파일 분석 성공!")
        return json.loads(clean_json)

    except Exception as e:
        print(f">>> [ERROR] 상세 사유: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

import xml.etree.ElementTree as ET

# 기존 /analyze-sheet 밑에 새로운 XML 전용 경로를 추가합니다.
@app.post("/analyze-xml")
async def analyze_xml(file: UploadFile = File(...)):
    print(f">>> [LOG] MusicXML 분석 요청 수신: {file.filename}")
    try:
        content = await file.read()
        
        # 1. XML 데이터 파싱 (제미나이를 거치지 않고 파이썬이 직접 해독)
        root = ET.fromstring(content)
        melody_data = []
        
        # 기본 템포 및 박자 설정 (수학적 계산을 위한 기준값)
        current_time = 0.0
        
        # 2. XML의 모든 <note> 태그를 순회하며 음표와 박자 추출
        for measure in root.findall('.//measure'):
            for note in measure.findall('note'):
                # 쉼표(rest)인 경우 시간만 건너뜁니다
                if note.find('rest') is not None:
                    duration_node = note.find('duration')
                    if duration_node is not None:
                        # 쉼표의 길이만큼 시간 추가 (기본 1/4박자 기준 등 비율 계산 필요)
                        current_time += float(duration_node.text) * 0.25 
                    continue
                
                # 음정(pitch) 추출
                pitch = note.find('pitch')
                if pitch is not None:
                    step = pitch.find('step').text # C, D, E 등
                    octave = pitch.find('octave').text # 4, 5 등
                    note_name = f"{step}{octave}"
                    
                    # 변화표(샵, 플랫) 확인
                    alter = pitch.find('alter')
                    if alter is not None:
                        if alter.text == '1':
                            note_name = f"{step}#{octave}"
                        elif alter.text == '-1':
                            note_name = f"{step}b{octave}"
                    
                    # 박자(duration) 및 음표 종류(type) 추출
                    type_node = note.find('type')
                    duration_str = "4n" # 기본값 4분음표
                    if type_node is not None:
                        type_val = type_node.text
                        if type_val == 'whole': duration_str = '1n'
                        elif type_val == 'half': duration_str = '2n'
                        elif type_val == 'quarter': duration_str = '4n'
                        elif type_val == 'eighth': duration_str = '8n'
                        elif type_val == '16th': duration_str = '16n'
                    
                    # 추출한 데이터를 JSON 형식으로 배열에 저장
                    melody_data.append({
                        "note": note_name,
                        "duration": duration_str,
                        "time": f"+{current_time}"
                    })
                    
                    # 다음 음표를 위해 시간 진행 (간이 계산식)
                    current_time += 0.5 if duration_str == '8n' else 1.0

        print(f">>> [LOG] MusicXML 분석 성공! 총 {len(melody_data)}개의 음표 추출.")
        return {"melody": melody_data}

    except Exception as e:
        print(f">>> [ERROR] MusicXML 파싱 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"XML 분석 오류: {str(e)}")
