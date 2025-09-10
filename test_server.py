# -*- coding: utf-8 -*-
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>YouTube Analytics Studio - 테스트 서버</h1>
    <p>서버가 정상적으로 실행되고 있습니다!</p>
    <p>히스토리 저장 시스템이 구현되었습니다.</p>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Analytics Studio 테스트 서버 시작")
    print("=" * 60)
    print("주소: http://localhost:8081")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8081)