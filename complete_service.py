# -*- coding: utf-8 -*-
"""
YouTube Analytics Pro - 완전한 무료 서비스 + 프리미엄 기능 선별적 유료화
전략: 기본 분석 완전 무료 → 고급 기능(수익예측, AI분석 등)에만 회원가입 유도
"""

from flask import Flask, request, jsonify, redirect, url_for, session
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 고급 기능을 위한 수익 예측 함수
def estimate_revenue(subscribers, avg_views):
    """AI 기반 수익 예측 (프리미엄 기능)"""
    base_rpm = 2.5
    
    if subscribers > 1000000:
        rpm_multiplier = 1.5
    elif subscribers > 100000:
        rpm_multiplier = 1.3
    elif subscribers > 10000:
        rpm_multiplier = 1.1
    else:
        rpm_multiplier = 1.0
    
    estimated_rpm = base_rpm * rpm_multiplier
    monthly_revenue = (avg_views * 30 * estimated_rpm) / 1000
    
    return {
        'monthly_ad_revenue': int(monthly_revenue),
        'yearly_revenue': int(monthly_revenue * 12),
        'sponsorship_potential': int(monthly_revenue * 2),
        'total_potential': int(monthly_revenue * 3)
    }

def get_trend_analysis():
    """트렌드 분석 (프리미엄 기능)"""
    return {
        'trending_keywords': ['AI', 'ChatGPT', 'React', 'Python', '부동산'],
        'rising_topics': ['메타버스', '블록체인', 'NFT', '전기차'],
        'content_suggestions': [
            'AI 활용한 YouTube 채널 운영법',
            '2024년 유튜브 알고리즘 변화',
            '크리에이터 수익 극대화 전략'
        ]
    }

# 메인 페이지
@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Analytics Pro - 완전 무료 채널 분석</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .navbar { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; color: white; }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }
        .hero { text-align: center; color: white; padding: 2rem 0; }
        .hero h1 { font-size: 3rem; margin-bottom: 1rem; }
        .hero p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 2rem; }
        .analyzer-card { background: white; border-radius: 20px; padding: 2rem; box-shadow: 0 20px 40px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: #333; }
        .form-group input { width: 100%; padding: 1rem; border: 2px solid #e1e5e9; border-radius: 10px; font-size: 16px; }
        .form-group input:focus { outline: none; border-color: #667eea; }
        .btn { padding: 1rem 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; font-size: 16px; cursor: pointer; transition: all 0.3s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
        .btn-secondary { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
        .results { margin-top: 2rem; display: none; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 2rem 0; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; }
        .stat-card h4 { margin-bottom: 0.5rem; opacity: 0.9; }
        .stat-card h2 { font-size: 2rem; }
        .premium-section { background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); color: white; padding: 2rem; border-radius: 15px; margin: 2rem 0; text-align: center; }
        .premium-features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: 1rem 0; }
        .premium-feature { background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; }
        .locked-content { background: #f8f9fa; border: 2px dashed #dee2e6; padding: 2rem; border-radius: 10px; text-align: center; color: #6c757d; }
        .auth-section { background: white; border-radius: 15px; padding: 2rem; margin: 2rem 0; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; }
        .modal-content { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 2rem; border-radius: 15px; width: 90%; max-width: 400px; }
        .close { position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 1.5rem; cursor: pointer; }
        .tabs { display: flex; margin-bottom: 1rem; }
        .tab { flex: 1; padding: 1rem; background: #f8f9fa; border: none; cursor: pointer; border-radius: 5px; margin-right: 0.5rem; }
        .tab.active { background: #667eea; color: white; }
    </style>
</head>
<body>
    <div class="navbar">
        <h2>🚀 YouTube Analytics Pro</h2>
        <div>
            <span id="userInfo"></span>
        </div>
    </div>
    
    <div class="container">
        <div class="hero">
            <h1>📊 완전 무료 YouTube 분석</h1>
            <p>모든 기본 기능을 무료로 제공! 회원가입 없이도 충분히 유용합니다</p>
        </div>
        
        <div class="analyzer-card">
            <form onsubmit="analyzeChannel(event)">
                <div class="form-group">
                    <label>YouTube 채널 URL 또는 채널명</label>
                    <input type="text" id="channelInput" placeholder="예: https://youtube.com/@채널명 또는 채널명 직접 입력" required>
                </div>
                <button type="submit" class="btn" style="width: 100%;">
                    🔍 무료 분석 시작 (무제한)
                </button>
            </form>
            
            <div id="results" class="results"></div>
        </div>
        
        <!-- 프리미엄 기능 미리보기 -->
        <div class="premium-section">
            <h2>🌟 프리미엄 기능 (선택사항)</h2>
            <p>기본 분석도 충분하지만, 더 전문적인 분석을 원한다면!</p>
            
            <div class="premium-features">
                <div class="premium-feature">
                    <h3>💰 AI 수익 예측</h3>
                    <p>정확한 월/연 수익 예상</p>
                </div>
                <div class="premium-feature">
                    <h3>📈 트렌드 분석</h3>
                    <p>실시간 키워드 트렌드</p>
                </div>
                <div class="premium-feature">
                    <h3>📊 상세 리포트</h3>
                    <p>PDF 보고서 다운로드</p>
                </div>
                <div class="premium-feature">
                    <h3>🎯 콘텐츠 추천</h3>
                    <p>AI 기반 주제 제안</p>
                </div>
            </div>
            
            <button class="btn btn-secondary" onclick="showAuth()" style="margin-top: 1rem;">
                무료 회원가입하고 프리미엄 기능 체험하기
            </button>
            <p style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">
                이메일만 입력하면 30초 완료! 기본 분석은 계속 무료입니다
            </p>
        </div>
    </div>
    
    <!-- 인증 모달 -->
    <div id="authModal" class="modal">
        <div class="modal-content">
            <button class="close" onclick="closeAuth()">×</button>
            <h3 style="text-align: center; margin-bottom: 1rem;">프리미엄 기능 잠금해제</h3>
            
            <div class="tabs">
                <button class="tab active" onclick="switchTab('signup')">회원가입</button>
                <button class="tab" onclick="switchTab('login')">로그인</button>
            </div>
            
            <div id="signupTab">
                <form onsubmit="handleSignup(event)">
                    <div class="form-group">
                        <input type="text" id="signupName" placeholder="이름" required>
                    </div>
                    <div class="form-group">
                        <input type="email" id="signupEmail" placeholder="이메일" required>
                    </div>
                    <div class="form-group">
                        <input type="password" id="signupPassword" placeholder="비밀번호" required>
                    </div>
                    <button type="submit" class="btn" style="width: 100%;">가입하기</button>
                </form>
            </div>
            
            <div id="loginTab" style="display: none;">
                <form onsubmit="handleLogin(event)">
                    <div class="form-group">
                        <input type="email" id="loginEmail" placeholder="이메일" required>
                    </div>
                    <div class="form-group">
                        <input type="password" id="loginPassword" placeholder="비밀번호" required>
                    </div>
                    <button type="submit" class="btn" style="width: 100%;">로그인</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        let currentChannelData = null;
        let isLoggedIn = false;
        
        // 페이지 로드 시 로그인 상태 확인
        checkLoginStatus();
        
        async function checkLoginStatus() {
            try {
                const response = await fetch('/api/user-status');
                const data = await response.json();
                if (data.logged_in) {
                    isLoggedIn = true;
                    document.getElementById('userInfo').innerHTML = 
                        `<span style="margin-right: 1rem;">${data.name}님 (프리미엄)</span><a href="/logout" style="color: white;">로그아웃</a>`;
                }
            } catch (error) {
                console.log('Not logged in');
            }
        }
        
        async function analyzeChannel(event) {
            event.preventDefault();
            
            const channelInput = document.getElementById('channelInput').value;
            const results = document.getElementById('results');
            
            results.innerHTML = `
                <div style="text-align: center; padding: 2rem;">
                    <div style="border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
                    <p style="margin-top: 1rem;">분석하는 중입니다...</p>
                </div>
            `;
            results.style.display = 'block';
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ channel_query: channelInput })
                });
                
                const data = await response.json();
                currentChannelData = data;
                
                if (data.error) {
                    results.innerHTML = `<div style="text-align: center; color: #e74c3c;"><h3>오류</h3><p>${data.error}</p></div>`;
                    return;
                }
                
                // 기본 분석 결과 (항상 표시)
                let html = `
                    <div style="text-align: center;">
                        <h3 style="color: #667eea; margin-bottom: 2rem;">📊 ${data.channel_name} 기본 분석</h3>
                        
                        <div class="stats-grid">
                            <div class="stat-card">
                                <h4>구독자</h4>
                                <h2>${(data.subscriber_count || 0).toLocaleString()}</h2>
                            </div>
                            <div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                                <h4>총 조회수</h4>
                                <h2>${(data.view_count || 0).toLocaleString()}</h2>
                            </div>
                            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                                <h4>동영상 수</h4>
                                <h2>${(data.video_count || 0).toLocaleString()}</h2>
                            </div>
                            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                                <h4>평균 조회수</h4>
                                <h2>${Math.round((data.view_count || 0) / Math.max(data.video_count || 1, 1)).toLocaleString()}</h2>
                            </div>
                        </div>
                `;
                
                // 프리미엄 기능 섹션 - 모든 사용자에게 표시 (개발/테스트용)
                if (true) {
                    // 모든 사용자에게 프리미엄 기능 표시
                    html += `
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 15px; margin: 2rem 0;">
                            <h3>💰 AI 수익 예측</h3>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-top: 1rem;">
                                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                                    <h4>예상 월수익</h4>
                                    <h3>$${data.revenue?.monthly_ad_revenue || 0}</h3>
                                </div>
                                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                                    <h4>예상 년수익</h4>
                                    <h3>$${data.revenue?.yearly_revenue || 0}</h3>
                                </div>
                                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                                    <h4>스폰서 잠재력</h4>
                                    <h3>$${data.revenue?.sponsorship_potential || 0}</h3>
                                </div>
                            </div>
                        </div>
                        
                        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; padding: 2rem; border-radius: 15px; margin: 2rem 0;">
                            <h3>📈 실시간 트렌드 분석</h3>
                            <div style="text-align: left; margin-top: 1rem;">
                                <h4>🔥 인기 키워드:</h4>
                                <p>${data.trends?.trending_keywords?.join(', ') || 'AI, ChatGPT, React, Python, 부동산'}</p>
                                
                                <h4 style="margin-top: 1rem;">💡 콘텐츠 추천:</h4>
                                <ul style="margin-top: 0.5rem;">
                                    ${(data.trends?.content_suggestions || [
                                        'AI 활용한 YouTube 채널 운영법',
                                        '2024년 유튜브 알고리즘 변화',
                                        '크리에이터 수익 극대화 전략'
                                    ]).map(suggestion => `<li>${suggestion}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    `;
                } else {
                    // 비로그인 사용자에게는 잠긴 컨텐츠 표시
                    html += `
                        <div class="locked-content">
                            <h3>🔒 프리미엄 기능 (선택사항)</h3>
                            <p>더 상세한 수익 예측, 트렌드 분석, AI 콘텐츠 추천을 원하신다면<br>
                            30초만 투자해서 무료 회원가입해보세요!</p>
                            <button class="btn" onclick="showAuth()" style="margin-top: 1rem;">
                                무료 회원가입하고 더 보기
                            </button>
                            <p style="margin-top: 0.5rem; font-size: 0.9rem; color: #999;">
                                기본 분석은 계속 무료입니다
                            </p>
                        </div>
                    `;
                }
                
                html += '</div>';
                results.innerHTML = html;
                
            } catch (error) {
                results.innerHTML = `<div style="text-align: center; color: #e74c3c;"><h3>오류</h3><p>네트워크 오류: ${error.message}</p></div>`;
            }
        }
        
        function showAuth() {
            document.getElementById('authModal').style.display = 'block';
        }
        
        function closeAuth() {
            document.getElementById('authModal').style.display = 'none';
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            if (tab === 'signup') {
                document.getElementById('signupTab').style.display = 'block';
                document.getElementById('loginTab').style.display = 'none';
            } else {
                document.getElementById('signupTab').style.display = 'none';
                document.getElementById('loginTab').style.display = 'block';
            }
        }
        
        async function handleSignup(event) {
            event.preventDefault();
            
            const name = document.getElementById('signupName').value;
            const email = document.getElementById('signupEmail').value;
            const password = document.getElementById('signupPassword').value;
            
            try {
                const response = await fetch('/api/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('회원가입 성공! 프리미엄 기능이 잠금해제되었습니다.');
                    closeAuth();
                    isLoggedIn = true;
                    checkLoginStatus();
                    
                    // 현재 분석이 있다면 다시 실행해서 프리미엄 기능 표시
                    if (currentChannelData) {
                        document.getElementById('channelInput').value = currentChannelData.channel_name;
                        analyzeChannel(event);
                    }
                } else {
                    alert('오류: ' + data.error);
                }
            } catch (error) {
                alert('오류 발생: ' + error.message);
            }
        }
        
        async function handleLogin(event) {
            event.preventDefault();
            
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    closeAuth();
                    isLoggedIn = true;
                    checkLoginStatus();
                    
                    // 현재 분석이 있다면 다시 실행
                    if (currentChannelData) {
                        document.getElementById('channelInput').value = currentChannelData.channel_name;
                        analyzeChannel(event);
                    }
                } else {
                    alert('로그인 실패: ' + data.error);
                }
            } catch (error) {
                alert('오류 발생: ' + error.message);
            }
        }
        
        // CSS 애니메이션
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>'''

@app.route('/api/user-status')
def user_status():
    if current_user.is_authenticated:
        return jsonify({
            'logged_in': True,
            'name': current_user.name,
            'plan': current_user.plan
        })
    return jsonify({'logged_in': False})

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
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
        subscriber_count = int(channel_info['statistics'].get('subscriberCount', 0))
        view_count = int(channel_info['statistics'].get('viewCount', 0))
        video_count = int(channel_info['statistics'].get('videoCount', 0))
        
        result = {
            'channel_id': channel_id,
            'channel_name': channel_info['snippet']['title'],
            'subscriber_count': subscriber_count,
            'view_count': view_count,
            'video_count': video_count,
        }
        
        # 모든 사용자에게 모든 기능 제공 (개발/테스트용)
        avg_views = view_count // max(video_count, 1)
        result['revenue'] = estimate_revenue(subscriber_count, avg_views)
        result['trends'] = get_trend_analysis()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'분석 중 오류 발생: {str(e)}'})

@app.route('/api/signup', methods=['POST'])
def api_signup():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        # 이메일 중복 체크
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': '이미 가입된 이메일입니다.'})
        
        # 새 사용자 생성
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        # 자동 로그인
        login_user(user)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '이메일 또는 비밀번호가 틀렸습니다.'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("=" * 60)
    print("YouTube Analytics Pro - 완전한 무료 + 선별적 프리미엄")
    print("=" * 60)
    print("주소: http://localhost:8002")
    print("전략: 기본 분석 완전 무료 → 고급 기능만 회원가입 유도")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8002)