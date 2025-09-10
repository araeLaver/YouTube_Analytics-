# -*- coding: utf-8 -*-
"""
YouTube Analytics Pro - 비회원 우선 체험형 버전
점진적 전환 전략: 체험 → 가치 인식 → 자연스러운 회원가입
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import os
import re

# Flask 앱 초기화
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///youtube_analytics.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 확장 프로그램 초기화
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# YouTube API 설정
API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"
youtube = build('youtube', 'v3', developerKey=API_KEY)

# 사용자 모델
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(20), default='free')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_payment = db.Column(db.DateTime)
    usage_logs = db.relationship('UsageLog', backref='user', lazy=True)

class UsageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 비회원은 NULL
    session_id = db.Column(db.String(100))  # 비회원 세션 추적
    action = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    channel_id = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 비회원 사용량 체크
def check_guest_usage():
    if 'session_id' not in session:
        session['session_id'] = os.urandom(16).hex()
    
    today = datetime.now().date()
    usage_count = UsageLog.query.filter(
        UsageLog.session_id == session['session_id'],
        UsageLog.created_at >= today
    ).count()
    
    return usage_count < 3  # 비회원은 일 3회 제한

# 로그인 사용자 사용량 체크
def check_user_usage(user):
    if user.plan != 'free':
        return True
    
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage_count = UsageLog.query.filter(
        UsageLog.user_id == user.id,
        UsageLog.created_at >= current_month
    ).count()
    
    return usage_count < 10  # 회원은 월 10회

def log_usage(action, channel_id=None):
    if current_user.is_authenticated:
        log = UsageLog(user_id=current_user.id, action=action, channel_id=channel_id)
    else:
        if 'session_id' not in session:
            session['session_id'] = os.urandom(16).hex()
        log = UsageLog(session_id=session['session_id'], action=action, channel_id=channel_id)
    
    db.session.add(log)
    db.session.commit()

# 메인 페이지 (비회원도 바로 사용 가능)
@app.route('/')
def index():
    # 사용량 체크 - 일단 무제한
    can_use = True
    limit_message = "무료 무제한 분석"
    
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Analytics Pro - 무료 채널 분석</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
        .navbar {{ background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; color: white; }}
        .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }}
        .hero {{ text-align: center; color: white; padding: 3rem 0; }}
        .hero h1 {{ font-size: 3rem; margin-bottom: 1rem; }}
        .hero p {{ font-size: 1.2rem; opacity: 0.9; margin-bottom: 2rem; }}
        .analyzer-card {{ background: white; border-radius: 20px; padding: 3rem; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }}
        .usage-status {{ background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; padding: 1rem; border-radius: 10px; margin-bottom: 2rem; text-align: center; }}
        .analyzer-form {{ display: flex; gap: 1rem; align-items: end; margin-bottom: 2rem; }}
        .form-group {{ flex: 1; }}
        .form-group label {{ display: block; margin-bottom: 0.5rem; font-weight: 500; }}
        .form-group input {{ width: 100%; padding: 1rem; border: 2px solid #e1e5e9; border-radius: 10px; font-size: 16px; }}
        .form-group input:focus {{ outline: none; border-color: #667eea; }}
        .btn {{ padding: 1rem 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; font-size: 16px; cursor: pointer; transition: all 0.3s; }}
        .btn:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }}
        .btn:disabled {{ background: #ccc; cursor: not-allowed; transform: none; }}
        .results {{ margin-top: 2rem; padding: 2rem; background: #f8f9fa; border-radius: 10px; display: none; }}
        .signup-prompt {{ background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); color: white; padding: 2rem; border-radius: 15px; margin: 2rem 0; text-align: center; }}
        .features-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 3rem 0; }}
        .feature-card {{ background: white; padding: 2rem; border-radius: 15px; text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
        .feature-icon {{ font-size: 3rem; margin-bottom: 1rem; }}
        .auth-links {{ display: flex; gap: 1rem; align-items: center; }}
        .auth-links a {{ color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 5px; transition: all 0.3s; }}
        .auth-links a:hover {{ background: rgba(255,255,255,0.2); }}
    </style>
</head>
<body>
    <div class="navbar">
        <h2>🚀 YouTube Analytics Pro</h2>
        <div class="auth-links">
            {"<span>" + current_user.name + "님</span> <a href='/logout'>로그아웃</a>" if current_user.is_authenticated else ""}
        </div>
    </div>
    
    <div class="container">
        <div class="hero">
            <h1>⚡ 즉시 무료 체험</h1>
            <p>회원가입 없이 바로 YouTube 채널을 분석해보세요!</p>
        </div>
        
        <div class="analyzer-card">
            <div class="usage-status">
                💎 {limit_message}
            </div>
            
            <form class="analyzer-form" onsubmit="analyzeChannel(event)">
                <div class="form-group">
                    <label>YouTube 채널 URL 또는 채널명</label>
                    <input type="text" id="channelInput" placeholder="예: https://youtube.com/@채널명 또는 채널명 입력" required>
                </div>
                <button type="submit" class="btn" {"disabled" if not can_use else ""}>
                    🔍 무료 분석 시작
                </button>
            </form>
            
            <div id="results" class="results"></div>
        </div>
        
        
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>실시간 채널 분석</h3>
                <p>구독자, 조회수, 참여도 등 핵심 지표를 실시간으로 확인하세요</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💰</div>
                <h3>수익 예측</h3>
                <p>AI 기반 알고리즘으로 정확한 월간/연간 수익을 예측합니다</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3>한국 시장 특화</h3>
                <p>K-콘텐츠와 한국 시장에 최적화된 분석을 제공합니다</p>
            </div>
        </div>
    </div>
    
    <!-- 회원가입 모달 -->
    <div id="signupModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 3rem; border-radius: 20px; width: 400px;">
            <h3 style="text-align: center; margin-bottom: 2rem;">🚀 무료 회원가입</h3>
            <form id="signupForm">
                <div style="margin-bottom: 1rem;">
                    <input type="text" placeholder="이름" required style="width: 100%; padding: 1rem; border: 2px solid #e1e5e9; border-radius: 10px;">
                </div>
                <div style="margin-bottom: 1rem;">
                    <input type="email" placeholder="이메일" required style="width: 100%; padding: 1rem; border: 2px solid #e1e5e9; border-radius: 10px;">
                </div>
                <div style="margin-bottom: 2rem;">
                    <input type="password" placeholder="비밀번호" required style="width: 100%; padding: 1rem; border: 2px solid #e1e5e9; border-radius: 10px;">
                </div>
                <button type="submit" class="btn" style="width: 100%;">가입하고 10회 더 사용하기!</button>
            </form>
            <button onclick="closeSignup()" style="position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 1.5rem; cursor: pointer;">×</button>
        </div>
    </div>
    
    <script>
        async function analyzeChannel(event) {{
            event.preventDefault();
            
            const channelInput = document.getElementById('channelInput').value;
            const results = document.getElementById('results');
            
            results.innerHTML = '<div style="text-align: center; padding: 2rem;"><div style="border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto;"></div><p style="margin-top: 1rem;">분석하는 중입니다...</p></div>';
            results.style.display = 'block';
            
            try {{
                const response = await fetch('/api/analyze', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ channel_query: channelInput }})
                }});
                
                const data = await response.json();
                
                if (data.error) {{
                    results.innerHTML = `<div style="text-align: center; color: #e74c3c;"><h3>오류 발생</h3><p>${{data.error}}</p></div>`;
                }} else {{
                    results.innerHTML = `
                        <div style="text-align: center;">
                            <h3 style="color: #667eea; margin-bottom: 2rem;">📊 ${{data.channel_name}} 분석 결과</h3>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px;">
                                    <h4>구독자</h4>
                                    <h2>${{(data.subscriber_count || 0).toLocaleString()}}</h2>
                                </div>
                                <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; padding: 1.5rem; border-radius: 10px;">
                                    <h4>총 조회수</h4>
                                    <h2>${{(data.view_count || 0).toLocaleString()}}</h2>
                                </div>
                                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); color: white; padding: 1.5rem; border-radius: 10px;">
                                    <h4>동영상 수</h4>
                                    <h2>${{(data.video_count || 0).toLocaleString()}}</h2>
                                </div>
                            </div>
                        </div>
                    `;
                }}
            }} catch (error) {{
                results.innerHTML = `<div style="text-align: center; color: #e74c3c;"><h3>오류</h3><p>네트워크 오류가 발생했습니다: ${{error.message}}</p></div>`;
            }}
        }}
        
        function showSignup() {{
            document.getElementById('signupModal').style.display = 'block';
        }}
        
        function closeSignup() {{
            document.getElementById('signupModal').style.display = 'none';
        }}
        
        function showLogin() {{
            window.location.href = '/login';
        }}
        
        // CSS 애니메이션 추가
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>'''

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    # 사용량 체크 - 일단 무제한으로 설정
    # if current_user.is_authenticated:
    #     if not check_user_usage(current_user):
    #         return jsonify({'error': '월 사용량을 초과했습니다. Pro 플랜으로 업그레이드하시면 무제한 사용 가능합니다!'})
    # else:
    #     if not check_guest_usage():
    #         return jsonify({'error': '오늘 무료 체험 한도를 초과했습니다. 회원가입하시면 월 10회까지 사용 가능합니다!'})
    
    data = request.get_json()
    channel_query = data.get('channel_query', '')
    
    try:
        # 채널 ID 찾기
        channel_id = None
        if 'youtube.com' in channel_query or 'youtu.be' in channel_query:
            if '/@' in channel_query:
                handle = channel_query.split('/@')[-1].split('/')[0]
                search_response = youtube.search().list(
                    q=handle,
                    type='channel',
                    part='snippet',
                    maxResults=1
                ).execute()
                if search_response['items']:
                    channel_id = search_response['items'][0]['snippet']['channelId']
            elif '/channel/' in channel_query:
                channel_id = channel_query.split('/channel/')[-1].split('/')[0]
        else:
            search_response = youtube.search().list(
                q=channel_query,
                type='channel',
                part='snippet',
                maxResults=1
            ).execute()
            if search_response['items']:
                channel_id = search_response['items'][0]['snippet']['channelId']
        
        if not channel_id:
            return jsonify({'error': '채널을 찾을 수 없습니다. 채널명이나 URL을 정확히 입력해주세요.'})
        
        # 채널 정보 가져오기
        channel_response = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        ).execute()
        
        if not channel_response['items']:
            return jsonify({'error': '채널 정보를 가져올 수 없습니다.'})
        
        channel_info = channel_response['items'][0]
        
        # 사용량 로그 기록
        log_usage('analyze_channel', channel_id)
        
        return jsonify({
            'channel_id': channel_id,
            'channel_name': channel_info['snippet']['title'],
            'subscriber_count': int(channel_info['statistics'].get('subscriberCount', 0)),
            'view_count': int(channel_info['statistics'].get('viewCount', 0)),
            'video_count': int(channel_info['statistics'].get('videoCount', 0)),
        })
        
    except Exception as e:
        return jsonify({'error': f'분석 중 오류 발생: {{str(e)}}'})

# 간단한 로그인 페이지
@app.route('/login')
def login_page():
    return '''<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>로그인</title></head>
<body style="font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center;">
    <div style="background: white; padding: 3rem; border-radius: 20px; width: 400px; text-align: center;">
        <h2>로그인</h2>
        <form action="/api/login" method="POST" style="margin-top: 2rem;">
            <input type="email" name="email" placeholder="이메일" required style="width: 100%; padding: 1rem; margin-bottom: 1rem; border: 2px solid #e1e5e9; border-radius: 10px;">
            <input type="password" name="password" placeholder="비밀번호" required style="width: 100%; padding: 1rem; margin-bottom: 2rem; border: 2px solid #e1e5e9; border-radius: 10px;">
            <button type="submit" style="width: 100%; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; cursor: pointer;">로그인</button>
        </form>
        <p style="margin-top: 1rem;"><a href="/">← 메인으로 돌아가기</a></p>
    </div>
</body>
</html>'''

@app.route('/api/login', methods=['POST'])
def api_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("=" * 60)
    print("YouTube Analytics Pro - 비회원 우선 체험형")
    print("=" * 60) 
    print("주소: http://localhost:8001")
    print("특징: 회원가입 없이 바로 체험 → 자연스러운 전환")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8001)