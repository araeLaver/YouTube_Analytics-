# -*- coding: utf-8 -*-
"""
YouTube Analytics Pro - 회원가입/결제 시스템이 포함된 버전
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
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
    plan = db.Column(db.String(20), default='free')  # free, pro, agency
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_payment = db.Column(db.DateTime)
    
    # 관계
    usage_logs = db.relationship('UsageLog', backref='user', lazy=True)

class UsageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'analyze_channel', 'get_script'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    channel_id = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 사용량 체크 함수
def check_usage_limit(user, action):
    if user.plan != 'free':
        return True  # 유료 사용자는 무제한
    
    # 무료 사용자는 월 5회 제한
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage_count = UsageLog.query.filter(
        UsageLog.user_id == user.id,
        UsageLog.action == action,
        UsageLog.created_at >= current_month
    ).count()
    
    return usage_count < 5

def log_usage(user, action, channel_id=None):
    log = UsageLog(user_id=user.id, action=action, channel_id=channel_id)
    db.session.add(log)
    db.session.commit()

# 루트 페이지
@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Analytics Pro</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; padding: 50px 0; }
        .header h1 { font-size: 3rem; margin-bottom: 20px; }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        .auth-section { background: white; border-radius: 20px; padding: 40px; margin: 30px auto; max-width: 500px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        .auth-tabs { display: flex; margin-bottom: 30px; }
        .auth-tab { flex: 1; padding: 15px; text-align: center; background: #f8f9fa; border: none; cursor: pointer; transition: all 0.3s; }
        .auth-tab.active { background: #007bff; color: white; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 500; }
        .form-group input { width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 8px; font-size: 16px; }
        .form-group input:focus { outline: none; border-color: #007bff; }
        .btn { width: 100%; padding: 15px; background: #007bff; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: all 0.3s; }
        .btn:hover { background: #0056b3; transform: translateY(-2px); }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin: 50px 0; }
        .feature-card { background: white; padding: 30px; border-radius: 15px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .feature-icon { font-size: 3rem; color: #007bff; margin-bottom: 20px; }
        .pricing { background: white; border-radius: 20px; padding: 40px; margin: 50px 0; }
        .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; margin-top: 30px; }
        .pricing-card { border: 2px solid #e1e5e9; border-radius: 15px; padding: 30px; text-align: center; transition: all 0.3s; }
        .pricing-card:hover { border-color: #007bff; transform: translateY(-5px); }
        .price { font-size: 2.5rem; color: #007bff; font-weight: bold; margin: 20px 0; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 YouTube Analytics Pro</h1>
            <p>AI 기반 YouTube 채널 분석으로 크리에이터의 성공을 지원합니다</p>
        </div>
        
        <div class="auth-section">
            <div class="auth-tabs">
                <button class="auth-tab active" onclick="showTab('login')">로그인</button>
                <button class="auth-tab" onclick="showTab('register')">회원가입</button>
            </div>
            
            <div id="login-form">
                <form action="/login" method="POST">
                    <div class="form-group">
                        <label>이메일</label>
                        <input type="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label>비밀번호</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">로그인</button>
                </form>
            </div>
            
            <div id="register-form" class="hidden">
                <form action="/register" method="POST">
                    <div class="form-group">
                        <label>이름</label>
                        <input type="text" name="name" required>
                    </div>
                    <div class="form-group">
                        <label>이메일</label>
                        <input type="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label>비밀번호</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">회원가입</button>
                </form>
            </div>
        </div>
        
        <div class="features">
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>심화 채널 분석</h3>
                <p>구독자, 조회수, 참여도 등 상세한 성과 지표를 한눈에 확인하세요</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💰</div>
                <h3>수익 예측</h3>
                <p>AI 알고리즘 기반으로 정확한 월간/연간 수익을 예측합니다</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3>트렌드 분석</h3>
                <p>최신 트렌드를 파악하고 성공하는 콘텐츠 전략을 수립하세요</p>
            </div>
        </div>
        
        <div class="pricing">
            <h2 style="text-align: center; margin-bottom: 20px;">💎 요금제</h2>
            <div class="pricing-grid">
                <div class="pricing-card">
                    <h3>Free</h3>
                    <div class="price">₩0</div>
                    <ul style="text-align: left; margin: 20px 0;">
                        <li>월 5회 채널 분석</li>
                        <li>기본 통계 제공</li>
                        <li>수익 추정</li>
                    </ul>
                </div>
                <div class="pricing-card">
                    <h3>Pro</h3>
                    <div class="price">₩19,900</div>
                    <ul style="text-align: left; margin: 20px 0;">
                        <li>무제한 채널 분석</li>
                        <li>AI 트렌드 예측</li>
                        <li>상세 리포트</li>
                        <li>이메일 지원</li>
                    </ul>
                </div>
                <div class="pricing-card">
                    <h3>Agency</h3>
                    <div class="price">₩99,900</div>
                    <ul style="text-align: left; margin: 20px 0;">
                        <li>Pro 기능 모두 포함</li>
                        <li>다중 채널 관리</li>
                        <li>API 접근</li>
                        <li>전담 지원</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tab) {
            // 탭 버튼 상태 변경
            document.querySelectorAll('.auth-tab').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // 폼 표시/숨김
            if (tab === 'login') {
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('register-form').classList.add('hidden');
            } else {
                document.getElementById('login-form').classList.add('hidden');
                document.getElementById('register-form').classList.remove('hidden');
            }
        }
    </script>
</body>
</html>'''

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    
    # 이메일 중복 체크
    if User.query.filter_by(email=email).first():
        flash('이미 가입된 이메일입니다.')
        return redirect(url_for('index'))
    
    # 새 사용자 생성
    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        name=name
    )
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return redirect(url_for('dashboard'))
    else:
        flash('잘못된 이메일 또는 비밀번호입니다.')
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # 사용량 통계
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage_count = UsageLog.query.filter(
        UsageLog.user_id == current_user.id,
        UsageLog.created_at >= current_month
    ).count()
    
    limit = "무제한" if current_user.plan != 'free' else "5"
    
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>대시보드 - YouTube Analytics Pro</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #f8f9fa; margin: 0; }}
        .navbar {{ background: #007bff; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }}
        .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }}
        .dashboard-card {{ background: white; border-radius: 10px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }}
        .stat-item {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; }}
        .analyze-form {{ display: flex; gap: 1rem; align-items: end; }}
        .form-group {{ flex: 1; }}
        .form-group label {{ display: block; margin-bottom: 0.5rem; font-weight: 500; }}
        .form-group input {{ width: 100%; padding: 0.75rem; border: 2px solid #e1e5e9; border-radius: 5px; }}
        .btn {{ padding: 0.75rem 1.5rem; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
        .btn:hover {{ background: #0056b3; }}
        .results {{ margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 5px; display: none; }}
    </style>
</head>
<body>
    <div class="navbar">
        <h2>YouTube Analytics Pro</h2>
        <div>
            <span>{current_user.name}님 ({current_user.plan.upper()})</span>
            <a href="/logout" style="color: white; margin-left: 1rem;">로그아웃</a>
        </div>
    </div>
    
    <div class="container">
        <div class="dashboard-card">
            <h3>📊 사용 현황</h3>
            <div class="stats">
                <div class="stat-item">
                    <h4>이번 달 사용량</h4>
                    <h2>{usage_count} / {limit}</h2>
                </div>
                <div class="stat-item">
                    <h4>요금제</h4>
                    <h2>{current_user.plan.upper()}</h2>
                </div>
                <div class="stat-item">
                    <h4>가입일</h4>
                    <h2>{current_user.created_at.strftime('%Y-%m-%d')}</h2>
                </div>
            </div>
        </div>
        
        <div class="dashboard-card">
            <h3>🔍 채널 분석</h3>
            <form class="analyze-form" onsubmit="analyzeChannel(event)">
                <div class="form-group">
                    <label>YouTube 채널 URL 또는 채널명</label>
                    <input type="text" id="channelInput" placeholder="예: https://youtube.com/@channel" required>
                </div>
                <button type="submit" class="btn">분석 시작</button>
            </form>
            <div id="results" class="results"></div>
        </div>
        
        <div class="dashboard-card">
            <h3>💎 요금제 업그레이드</h3>
            <p>더 많은 기능과 무제한 사용을 원하시나요?</p>
            <button class="btn" onclick="window.location.href='/upgrade'">업그레이드</button>
        </div>
    </div>
    
    <script>
        async function analyzeChannel(event) {{
            event.preventDefault();
            
            const channelInput = document.getElementById('channelInput').value;
            const results = document.getElementById('results');
            
            results.innerHTML = '<p>분석 중입니다...</p>';
            results.style.display = 'block';
            
            try {{
                const response = await fetch('/api/analyze', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ channel_query: channelInput }})
                }});
                
                const data = await response.json();
                
                if (data.error) {{
                    results.innerHTML = `<p style="color: red;">오류: ${{data.error}}</p>`;
                }} else {{
                    results.innerHTML = `
                        <h4>분석 결과: ${{data.channel_name}}</h4>
                        <p>구독자: ${{data.subscriber_count?.toLocaleString() || 'N/A'}}</p>
                        <p>총 조회수: ${{data.view_count?.toLocaleString() || 'N/A'}}</p>
                        <p>동영상 수: ${{data.video_count?.toLocaleString() || 'N/A'}}</p>
                    `;
                }}
            }} catch (error) {{
                results.innerHTML = `<p style="color: red;">오류가 발생했습니다: ${{error.message}}</p>`;
            }}
        }}
    </script>
</body>
</html>'''

@app.route('/api/analyze', methods=['POST'])
@login_required
def api_analyze():
    # 사용량 체크
    if not check_usage_limit(current_user, 'analyze_channel'):
        return jsonify({'error': '월 사용량을 초과했습니다. 요금제를 업그레이드해주세요.'})
    
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
            return jsonify({'error': '채널을 찾을 수 없습니다.'})
        
        # 채널 정보 가져오기
        channel_response = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        ).execute()
        
        if not channel_response['items']:
            return jsonify({'error': '채널 정보를 가져올 수 없습니다.'})
        
        channel_info = channel_response['items'][0]
        
        # 사용량 로그 기록
        log_usage(current_user, 'analyze_channel', channel_id)
        
        return jsonify({
            'channel_id': channel_id,
            'channel_name': channel_info['snippet']['title'],
            'subscriber_count': int(channel_info['statistics'].get('subscriberCount', 0)),
            'view_count': int(channel_info['statistics'].get('viewCount', 0)),
            'video_count': int(channel_info['statistics'].get('videoCount', 0)),
        })
        
    except Exception as e:
        return jsonify({'error': f'분석 중 오류 발생: {str(e)}'})

@app.route('/upgrade')
@login_required
def upgrade():
    return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>요금제 업그레이드</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f8f9fa; margin: 0; padding: 2rem; }
        .container { max-width: 800px; margin: 0 auto; }
        .pricing-card { background: white; border-radius: 10px; padding: 2rem; margin: 1rem; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .price { font-size: 2rem; color: #007bff; font-weight: bold; margin: 1rem 0; }
        .btn { padding: 1rem 2rem; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1.1rem; }
        .btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1 style="text-align: center;">💎 요금제 업그레이드</h1>
        
        <div class="pricing-card">
            <h3>Pro Plan</h3>
            <div class="price">₩19,900 / 월</div>
            <ul style="text-align: left; margin: 2rem 0;">
                <li>무제한 채널 분석</li>
                <li>AI 트렌드 예측</li>
                <li>상세 리포트</li>
                <li>이메일 지원</li>
            </ul>
            <button class="btn" onclick="upgrade('pro')">Pro로 업그레이드</button>
        </div>
        
        <div class="pricing-card">
            <h3>Agency Plan</h3>
            <div class="price">₩99,900 / 월</div>
            <ul style="text-align: left; margin: 2rem 0;">
                <li>Pro 기능 모두 포함</li>
                <li>다중 채널 관리</li>
                <li>API 접근</li>
                <li>전담 지원</li>
            </ul>
            <button class="btn" onclick="upgrade('agency')">Agency로 업그레이드</button>
        </div>
    </div>
    
    <script>
        function upgrade(plan) {
            alert(`${plan.toUpperCase()} 요금제로 업그레이드하시겠습니까?\\n\\n실제 결제는 아직 구현되지 않았습니다.\\n데모 목적으로 즉시 업그레이드됩니다.`);
            
            fetch('/api/upgrade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plan: plan })
            }).then(response => response.json()).then(data => {
                if (data.success) {
                    alert('업그레이드가 완료되었습니다!');
                    window.location.href = '/dashboard';
                }
            });
        }
    </script>
</body>
</html>'''

@app.route('/api/upgrade', methods=['POST'])
@login_required
def api_upgrade():
    data = request.get_json()
    plan = data.get('plan')
    
    if plan in ['pro', 'agency']:
        current_user.plan = plan
        current_user.last_payment = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': '잘못된 요금제입니다.'})

# 데이터베이스 초기화 함수
def create_tables():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("=" * 60)
    print("YouTube Analytics Pro - 회원가입/결제 시스템 포함")
    print("=" * 60)
    print("주소: http://localhost:8000")
    print("기능: 회원가입, 로그인, 사용량 제한, 요금제")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8000)