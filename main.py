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
