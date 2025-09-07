#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube Data API를 사용한 정확한 채널 분석 도구

사용법:
1. Google Cloud Console에서 YouTube Data API v3 활성화
2. API 키 발급
3. 아래 YOUR_API_KEY를 실제 키로 교체
"""

from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
from urllib.parse import unquote
from datetime import datetime

app = Flask(__name__)

# ====================================================
# 여기에 YouTube Data API 키를 입력하세요!
# ====================================================
API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"  # <-- 실제 API 키 설정됨
# ====================================================

class YouTubeAPIAnalyzer:
    """YouTube Data API를 사용한 정확한 분석"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        if api_key and api_key != "YOUR_API_KEY_HERE":
            self.youtube = build('youtube', 'v3', developerKey=api_key)
        else:
            self.youtube = None
    
    def extract_channel_id(self, channel_url):
        """URL에서 채널 ID 또는 사용자명 추출"""
        
        # URL 디코딩
        channel_url = unquote(channel_url)
        
        # 다양한 YouTube URL 패턴 처리
        patterns = [
            r'youtube\.com/channel/(UC[\w-]+)',  # 채널 ID
            r'youtube\.com/@([\w-]+)',  # 핸들
            r'youtube\.com/c/([\w-]+)',  # 커스텀 URL
            r'youtube\.com/user/([\w-]+)'  # 사용자명
        ]
        
        for pattern in patterns:
            match = re.search(pattern, channel_url)
            if match:
                identifier = match.group(1)
                # 핸들인 경우 검색 필요
                if '@' in channel_url:
                    return self.search_channel_by_handle(identifier)
                # 채널 ID인 경우 바로 반환
                elif identifier.startswith('UC'):
                    return identifier
                # 사용자명인 경우 변환 필요
                else:
                    return self.get_channel_id_from_username(identifier)
        
        return None
    
    def search_channel_by_handle(self, handle):
        """핸들(@username)로 채널 검색"""
        if not self.youtube:
            return None
        
        try:
            # 채널 검색
            search_response = self.youtube.search().list(
                q=handle,
                part='snippet',
                type='channel',
                maxResults=5
            ).execute()
            
            # 첫 번째 결과의 채널 ID 반환
            if search_response['items']:
                return search_response['items'][0]['snippet']['channelId']
            
        except HttpError as e:
            print(f"API 검색 오류: {e}")
        
        return None
    
    def get_channel_id_from_username(self, username):
        """사용자명으로 채널 ID 조회"""
        if not self.youtube:
            return None
        
        try:
            response = self.youtube.channels().list(
                forUsername=username,
                part='id'
            ).execute()
            
            if response['items']:
                return response['items'][0]['id']
            
        except HttpError as e:
            print(f"사용자명 조회 오류: {e}")
        
        return None
    
    def get_channel_data(self, channel_id):
        """채널 상세 정보 가져오기"""
        if not self.youtube:
            return None
        
        try:
            # 채널 정보 요청
            channel_response = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response['items']:
                return None
            
            channel = channel_response['items'][0]
            
            # 최근 동영상 가져오기
            videos = self.get_recent_videos(channel_id)
            
            # 평균 조회수 계산
            avg_views = 0
            if videos:
                total_views = sum(video.get('view_count', 0) for video in videos)
                avg_views = total_views / len(videos) if videos else 0
            
            return {
                'channel_id': channel_id,
                'channel_name': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                'total_views': int(channel['statistics'].get('viewCount', 0)),
                'video_count': int(channel['statistics'].get('videoCount', 0)),
                'created_date': channel['snippet']['publishedAt'],
                'country': channel['snippet'].get('country', 'KR'),
                'avg_views_per_video': int(avg_views),
                'recent_videos': videos
            }
            
        except HttpError as e:
            print(f"채널 정보 조회 오류: {e}")
            if "quotaExceeded" in str(e):
                return {'error': 'API 할당량 초과. 내일 다시 시도하세요.'}
            return None
    
    def get_recent_videos(self, channel_id, max_results=10):
        """최근 업로드 동영상 정보"""
        if not self.youtube:
            return []
        
        try:
            # 업로드 재생목록 ID 가져오기
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response['items']:
                return []
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # 최근 동영상 목록
            playlist_response = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=max_results
            ).execute()
            
            video_ids = [item['snippet']['resourceId']['videoId'] 
                        for item in playlist_response['items']]
            
            # 동영상 상세 정보
            videos_response = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            videos = []
            for item in videos_response['items']:
                videos.append({
                    'video_id': item['id'],
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    'duration': item['contentDetails']['duration']
                })
            
            return videos
            
        except HttpError as e:
            print(f"동영상 조회 오류: {e}")
            return []
    
    def analyze_channel(self, channel_url):
        """채널 종합 분석"""
        
        if not self.youtube:
            return {
                'error': 'API 키가 설정되지 않았습니다. 코드에서 API_KEY를 설정하세요.',
                'help': 'Google Cloud Console에서 YouTube Data API v3를 활성화하고 API 키를 발급받으세요.'
            }
        
        # 채널 ID 추출
        channel_id = self.extract_channel_id(channel_url)
        
        if not channel_id:
            return {'error': '유효한 YouTube 채널 URL이 아닙니다.'}
        
        # 채널 데이터 가져오기
        channel_data = self.get_channel_data(channel_id)
        
        if not channel_data:
            return {'error': '채널 정보를 가져올 수 없습니다.'}
        
        if 'error' in channel_data:
            return channel_data
        
        # 수익 분석
        return self.calculate_revenue(channel_data)
    
    def calculate_revenue(self, channel_data):
        """수익 계산 및 분석"""
        
        subscribers = channel_data['subscriber_count']
        avg_views = channel_data['avg_views_per_video']
        video_count = channel_data['video_count']
        total_views = channel_data['total_views']
        
        # 카테고리 추정 (설명 기반)
        description = channel_data.get('description', '').lower()
        if '프로그래밍' in description or '코딩' in description or 'programming' in description:
            category = '교육/프로그래밍'
            cpm = 3500
        elif '게임' in description or 'game' in description:
            category = '게임'
            cpm = 1800
        elif '리뷰' in description or 'review' in description:
            category = '리뷰'
            cpm = 2500
        else:
            category = '일반'
            cpm = 2000
        
        # 월 수익 계산
        monthly_videos = 8  # 평균 월 8개 업로드
        monthly_views = avg_views * monthly_videos
        monthly_ad_revenue = (monthly_views / 1000) * cpm
        
        # 스폰서십 계산
        if subscribers >= 1000000:
            sponsorship = subscribers * 150
            tier = "메가 인플루언서"
            growth_stage = "최상위 크리에이터"
        elif subscribers >= 100000:
            sponsorship = subscribers * 100
            tier = "매크로 인플루언서"
            growth_stage = "프로페셔널 단계"
        elif subscribers >= 10000:
            sponsorship = subscribers * 50
            tier = "마이크로 인플루언서"
            growth_stage = "성장 단계"
        elif subscribers >= 1000:
            sponsorship = subscribers * 20
            tier = "나노 인플루언서"
            growth_stage = "수익화 시작"
        else:
            sponsorship = 0
            tier = "신규 크리에이터"
            growth_stage = "구독자 확보 필요"
        
        # 멤버십 수익
        membership = subscribers * 0.01 * 4900 if subscribers >= 1000 else 0
        
        # 총 수익
        total_monthly = int(monthly_ad_revenue + sponsorship/12 + membership)
        
        # 성장 전략
        strategies = []
        if subscribers < 1000:
            strategies = [
                "1,000명 구독자 달성 (수익화 조건)",
                "YouTube 쇼츠 매일 업로드",
                "SEO 최적화된 제목과 설명",
                "일관된 업로드 스케줄 유지"
            ]
        elif subscribers < 10000:
            strategies = [
                "10,000명 목표 설정",
                "브랜드 아이덴티티 확립",
                "시청자 참여 콘텐츠",
                "소규모 스폰서십 시작"
            ]
        elif subscribers < 100000:
            strategies = [
                "실버 버튼 달성 목표",
                "프리미엄 콘텐츠 제작",
                "멤버십 혜택 강화",
                "대형 브랜드 협업"
            ]
        else:
            strategies = [
                "골드 버튼 목표",
                "자체 상품 개발",
                "다채널 네트워크 구축",
                "글로벌 진출"
            ]
        
        return {
            'success': True,
            'channel_name': channel_data['channel_name'],
            'subscribers': f"{subscribers:,}",
            'avg_views': f"{avg_views:,}",
            'total_views': f"{total_views:,}",
            'video_count': f"{video_count:,}",
            'category': category,
            'tier': tier,
            'growth_stage': growth_stage,
            'monthly_ad': f"{int(monthly_ad_revenue):,}",
            'monthly_sponsor': f"{int(sponsorship/12):,}",
            'monthly_membership': f"{int(membership):,}",
            'total_monthly': f"{total_monthly:,}",
            'annual_potential': f"{total_monthly * 12:,}",
            'strategies': strategies,
            'cpm': f"{cpm:,}",
            'monthly_views': f"{int(monthly_views):,}",
            'data_source': 'YouTube Data API v3',
            'created_date': channel_data['created_date'][:10],
            'country': channel_data['country']
        }

# Flask 앱 설정
analyzer = YouTubeAPIAnalyzer(API_KEY)

@app.route('/')
def index():
    api_configured = API_KEY != "YOUR_API_KEY_HERE"
    
    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube 채널 정확한 분석 도구</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        .api-status {{
            background: {'#d4edda' if api_configured else '#f8d7da'};
            border: 1px solid {'#c3e6cb' if api_configured else '#f5c6cb'};
            color: {'#155724' if api_configured else '#721c24'};
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .api-status h3 {{
            margin-top: 0;
        }}
        .setup-guide {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .input-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #34495e;
        }}
        input[type="text"] {{
            width: 100%;
            padding: 15px;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }}
        input[type="text"]:focus {{
            border-color: #3498db;
            outline: none;
        }}
        .btn {{
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            width: 100%;
            transition: transform 0.2s;
        }}
        .btn:hover {{
            transform: translateY(-2px);
        }}
        .btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}
        .result {{
            margin-top: 30px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #3498db;
            display: none;
        }}
        .result h2 {{
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #e74c3c;
        }}
        .stat-label {{
            color: #7f8c8d;
            margin-top: 5px;
            font-size: 0.9em;
        }}
        .revenue-section {{
            background: #e8f5e8;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .strategy-list {{
            background: #fff3e0;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .strategy-list ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .strategy-list li {{
            margin: 8px 0;
            font-size: 1.1em;
        }}
        .loading {{
            text-align: center;
            padding: 20px;
            display: none;
        }}
        .error {{
            background: #ffebee;
            border: 1px solid #f44336;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .examples {{
            margin: 20px 0;
            padding: 15px;
            background: #e3f2fd;
            border-radius: 8px;
        }}
        .examples h3 {{
            margin-top: 0;
            color: #1976d2;
        }}
        .example-links {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .example-link {{
            background: #2196f3;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 14px;
            cursor: pointer;
        }}
        .example-link:hover {{
            background: #1976d2;
        }}
        code {{
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 YouTube 채널 정확한 분석</h1>
        <p class="subtitle">YouTube Data API로 실제 데이터를 가져와 정확하게 분석합니다</p>
        
        <div class="api-status">
            {'<h3>✅ API 설정 완료</h3><p>YouTube Data API가 설정되어 정확한 데이터를 가져올 수 있습니다.</p>' if api_configured else '<h3>⚠️ API 키 설정 필요</h3><p>정확한 분석을 위해 YouTube Data API 키를 설정해주세요.</p>'}
        </div>
        
        {'' if api_configured else '''
        <div class="setup-guide">
            <h3>📋 API 키 설정 방법</h3>
            <ol>
                <li><a href="https://console.cloud.google.com" target="_blank">Google Cloud Console</a> 접속</li>
                <li>프로젝트 생성 또는 선택</li>
                <li>"API 및 서비스" → "라이브러리"에서 <strong>YouTube Data API v3</strong> 활성화</li>
                <li>"사용자 인증 정보" → "API 키 만들기"</li>
                <li>발급받은 키를 <code>api_analyzer.py</code> 파일의 <code>API_KEY = "YOUR_API_KEY_HERE"</code> 부분에 입력</li>
                <li>서버 재시작</li>
            </ol>
        </div>
        '''}
        
        <form id="analysisForm">
            <div class="input-group">
                <label for="channelUrl">YouTube 채널 URL</label>
                <input type="text" id="channelUrl" name="channelUrl" 
                       placeholder="https://www.youtube.com/@채널명 또는 채널 URL" 
                       value="https://www.youtube.com/@로직알려주는남자"
                       required>
            </div>
            <button type="submit" class="btn" id="analyzeBtn">
                {{'🔍 정확한 데이터로 분석 시작' if api_configured else '⚠️ API 키 설정 후 사용 가능'}}
            </button>
        </form>
        
        <div class="examples">
            <h3>📌 예시 채널 (클릭하여 자동 입력)</h3>
            <div class="example-links">
                <span class="example-link" onclick="setChannel('https://www.youtube.com/@로직알려주는남자')">로직알려주는남자</span>
                <span class="example-link" onclick="setChannel('https://www.youtube.com/@코딩애플')">코딩애플</span>
                <span class="example-link" onclick="setChannel('https://www.youtube.com/@노마드코더NomadCoders')">노마드코더</span>
                <span class="example-link" onclick="setChannel('https://www.youtube.com/@drimbcoding')">드림코딩</span>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <h3>🔄 YouTube API로 데이터 수집 중...</h3>
            <p>실제 채널 데이터를 가져오고 있습니다. 잠시만 기다려주세요.</p>
        </div>
        
        <div class="result" id="result">
            <h2>📈 분석 결과</h2>
            <div id="resultContent"></div>
        </div>
    </div>

    <script>
        function setChannel(url) {{
            document.getElementById('channelUrl').value = url;
        }}
        
        document.getElementById('analysisForm').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            const channelUrl = document.getElementById('channelUrl').value;
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const resultContent = document.getElementById('resultContent');
            const analyzeBtn = document.getElementById('analyzeBtn');
            
            loading.style.display = 'block';
            result.style.display = 'none';
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = '분석 중...';
            
            try {{
                const response = await fetch('/analyze', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{channel_url: channelUrl}})
                }});
                
                const data = await response.json();
                
                if (data.error) {{
                    resultContent.innerHTML = `
                        <div class="error">
                            <h3>❌ 분석 실패</h3>
                            <p>${{data.error}}</p>
                            ${{data.help ? `<p><strong>해결방법:</strong> ${{data.help}}</p>` : ''}}
                        </div>
                    `;
                }} else {{
                    resultContent.innerHTML = `
                        <div style="background: #d4edda; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                            ✅ <strong>데이터 소스:</strong> ${{data.data_source}} (정확한 실시간 데이터)
                        </div>
                        
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${{data.subscribers}}</div>
                                <div class="stat-label">구독자</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${{data.avg_views}}</div>
                                <div class="stat-label">평균 조회수</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${{data.video_count}}</div>
                                <div class="stat-label">총 동영상</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${{data.total_views}}</div>
                                <div class="stat-label">총 조회수</div>
                            </div>
                        </div>
                        
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${{data.tier}}</div>
                                <div class="stat-label">채널 등급</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${{data.category}}</div>
                                <div class="stat-label">카테고리</div>
                            </div>
                        </div>
                        
                        <div class="revenue-section">
                            <h3>💰 예상 월 수익</h3>
                            <div class="stats-grid">
                                <div class="stat-card">
                                    <div class="stat-value">${{data.monthly_ad}}원</div>
                                    <div class="stat-label">광고 수익</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${{data.monthly_sponsor}}원</div>
                                    <div class="stat-label">스폰서십</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${{data.monthly_membership}}원</div>
                                    <div class="stat-label">멤버십</div>
                                </div>
                            </div>
                            <div style="text-align: center; margin-top: 20px;">
                                <h3 style="color: #e74c3c;">총 월 예상 수익: ${{data.total_monthly}}원</h3>
                                <p style="color: #27ae60; font-size: 1.2em;">연 예상 수익: ${{data.annual_potential}}원</p>
                            </div>
                        </div>
                        
                        <div class="strategy-section">
                            <h3>🎯 현재 성장 단계: ${{data.growth_stage}}</h3>
                            <div class="strategy-list">
                                <h4>📋 맞춤형 성장 전략</h4>
                                <ul>
                                    ${{data.strategies.map(strategy => `<li>${{strategy}}</li>`).join('')}}
                                </ul>
                            </div>
                        </div>
                        
                        <div style="margin-top: 20px; padding: 15px; background: #f0f8ff; border-radius: 8px;">
                            <h4>📊 채널 세부 정보</h4>
                            <p><strong>채널명:</strong> ${{data.channel_name}}</p>
                            <p><strong>개설일:</strong> ${{data.created_date}}</p>
                            <p><strong>국가:</strong> ${{data.country}}</p>
                            <p><strong>월 예상 조회수:</strong> ${{data.monthly_views}}회</p>
                            <p><strong>적용 CPM:</strong> ${{data.cpm}}원</p>
                        </div>
                    `;
                }}
                
                loading.style.display = 'none';
                result.style.display = 'block';
                result.scrollIntoView({{behavior: 'smooth'}});
                
            }} catch (error) {{
                loading.style.display = 'none';
                resultContent.innerHTML = `
                    <div class="error">
                        <h3>❌ 네트워크 오류</h3>
                        <p>서버와의 통신 중 오류가 발생했습니다: ${{error.message}}</p>
                    </div>
                `;
                result.style.display = 'block';
            }} finally {{
                analyzeBtn.disabled = false;
                analyzeBtn.textContent = {'API 키가 설정되었으면 "🔍 정확한 데이터로 분석 시작"' if api_configured else '"⚠️ API 키 설정 후 사용 가능"'};
            }}
        }});
    </script>
</body>
</html>
    """

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        channel_url = data.get('channel_url', '')
        
        if not channel_url:
            return jsonify({'error': '채널 URL을 입력해주세요'}), 400
        
        print(f"[API 분석] 요청: {channel_url}")
        result = analyzer.analyze_channel(channel_url)
        print(f"[API 분석] 결과: {result.get('channel_name', 'Unknown')}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[API 분석] 오류: {e}")
        return jsonify({'error': f'분석 중 오류가 발생했습니다: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Data API 채널 분석 도구")
    print("=" * 60)
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("경고: API 키가 설정되지 않았습니다!")
        print("설정 방법:")
        print("1. Google Cloud Console에서 YouTube Data API v3 활성화")
        print("2. API 키 발급")
        print("3. 이 파일의 API_KEY 변수에 키 입력")
        print("4. 서버 재시작")
    else:
        print("API 키 설정 완료!")
        print("정확한 채널 데이터를 가져올 수 있습니다.")
    
    print("=" * 60)
    print("주소: http://localhost:8080")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)