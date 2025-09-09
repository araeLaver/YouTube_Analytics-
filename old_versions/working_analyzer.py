# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime

app = Flask(__name__)

API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

class WorkingAnalyzer:
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    def search_channel(self, query):
        try:
            # URL에서 채널명 추출
            import re
            from urllib.parse import unquote
            
            # YouTube URL 패턴들
            patterns = [
                r'youtube\.com/@([^/]+)',
                r'youtube\.com/c/([^/]+)',
                r'youtube\.com/channel/([^/]+)',
                r'youtube\.com/user/([^/]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    channel_name = unquote(match.group(1))
                    # 채널 ID인 경우 바로 반환
                    if pattern == r'youtube\.com/channel/([^/]+)':
                        return channel_name
                    # 채널명인 경우 검색
                    query = channel_name
                    break
            
            # 채널 검색
            response = self.youtube.search().list(
                q=query,
                part='snippet',
                type='channel',
                maxResults=1
            ).execute()
            
            if response['items']:
                return response['items'][0]['snippet']['channelId']
            return None
        except Exception as e:
            print(f"Search Error: {e}")
            return None
    
    def get_channel_info(self, channel_id):
        try:
            response = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            ).execute()
            
            if response['items']:
                return response['items'][0]
            return None
        except Exception as e:
            print(f"Channel Info Error: {e}")
            return None
    
    def get_all_videos(self, channel_id, max_videos=50):
        """전체 동영상 목록 가져오기"""
        try:
            # 업로드 재생목록 ID
            channel_info = self.get_channel_info(channel_id)
            uploads_id = channel_info['contentDetails']['relatedPlaylists']['uploads']
            
            videos = []
            next_page_token = None
            
            while len(videos) < max_videos:
                # 재생목록에서 동영상 가져오기
                request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_id,
                    maxResults=min(50, max_videos - len(videos)),
                    pageToken=next_page_token
                )
                response = request.execute()
                
                video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
                
                # 동영상 상세 정보
                videos_response = self.youtube.videos().list(
                    part='statistics,snippet',
                    id=','.join(video_ids)
                ).execute()
                
                for video in videos_response['items']:
                    video_id = video['id']
                    videos.append({
                        'title': video['snippet']['title'],
                        'published': video['snippet']['publishedAt'][:10],
                        'views': int(video['statistics'].get('viewCount', 0)),
                        'likes': int(video['statistics'].get('likeCount', 0)),
                        'comments': int(video['statistics'].get('commentCount', 0)),
                        'video_id': video_id,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'thumbnail': video['snippet']['thumbnails']['medium']['url']
                    })
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return videos
            
        except Exception as e:
            print(f"All Videos Error: {e}")
            return []

    def get_videos(self, channel_id, max_videos=30):
        try:
            # 업로드 재생목록 ID
            channel_info = self.get_channel_info(channel_id)
            uploads_id = channel_info['contentDetails']['relatedPlaylists']['uploads']
            
            # 재생목록에서 동영상 가져오기
            response = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_id,
                maxResults=max_videos
            ).execute()
            
            video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
            
            # 동영상 상세 정보
            videos_response = self.youtube.videos().list(
                part='statistics,snippet',
                id=','.join(video_ids)
            ).execute()
            
            videos = []
            for video in videos_response['items']:
                video_id = video['id']
                videos.append({
                    'title': video['snippet']['title'],
                    'published': video['snippet']['publishedAt'][:10],
                    'views': int(video['statistics'].get('viewCount', 0)),
                    'likes': int(video['statistics'].get('likeCount', 0)),
                    'comments': int(video['statistics'].get('commentCount', 0)),
                    'video_id': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'thumbnail': video['snippet']['thumbnails']['medium']['url']
                })
            
            return videos
            
        except Exception as e:
            print(f"Video Error: {e}")
            return []
    
    def analyze_complete(self, query, max_videos=30):
        try:
            print(f"Analysis Start: {query}, Videos: {max_videos}")
            
            # 채널 검색
            channel_id = self.search_channel(query)
            if not channel_id:
                return {'error': 'Channel not found'}
            
            print(f"Channel ID: {channel_id}")
            
            # 채널 정보
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return {'error': 'No channel info'}
            
            # 동영상 정보
            videos = self.get_videos(channel_id, max_videos)
            
            # 기본 통계
            stats = channel_info['statistics']
            subscribers = int(stats.get('subscriberCount', 0))
            total_views = int(stats.get('viewCount', 0))
            video_count = int(stats.get('videoCount', 0))
            
            # 동영상 분석
            if videos:
                total_video_views = sum(v['views'] for v in videos)
                avg_views = int(total_video_views / len(videos))
                total_likes = sum(v['likes'] for v in videos)
                avg_engagement = (total_likes / total_video_views * 100) if total_video_views > 0 else 0
                
                # TOP 5 인기 영상
                top_videos = sorted(videos, key=lambda x: x['views'], reverse=True)[:5]
                # 최신 5개
                recent_videos = videos[:5]
            else:
                avg_views = int(subscribers * 0.3)
                avg_engagement = 3.0
                top_videos = []
                recent_videos = []
            
            # 수익 계산
            monthly_ad = (avg_views * 8 / 1000) * 3000  # 월 8개 * CPM 3000원
            monthly_sponsor = subscribers * 50 / 12 if subscribers >= 10000 else 0
            monthly_membership = subscribers * 0.015 * 4900 if subscribers >= 1000 else 0
            total_monthly = int(monthly_ad + monthly_sponsor + monthly_membership)
            
            return {
                'success': True,
                'channel_name': channel_info['snippet']['title'],
                'channel_description': channel_info['snippet']['description'][:200],
                'subscribers': subscribers,
                'total_views': total_views,
                'video_count': video_count,
                'analyzed_videos': len(videos),
                'avg_views': avg_views,
                'avg_engagement': round(avg_engagement, 2),
                'monthly_ad': int(monthly_ad),
                'monthly_sponsor': int(monthly_sponsor),
                'monthly_membership': int(monthly_membership),
                'total_monthly': total_monthly,
                'annual_revenue': total_monthly * 12,
                'top_videos': top_videos,
                'recent_videos': recent_videos,
                'channel_id': channel_id,
                'input_max_videos': max_videos
            }
            
        except Exception as e:
            print(f"Analysis Error: {e}")
            return {'error': f'Analysis Error: {str(e)}'}

analyzer = WorkingAnalyzer()

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>YouTube 채널 완전 분석</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-accent: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --border-primary: #e2e8f0;
            --border-secondary: #cbd5e1;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
            --gradient-brand: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-success: linear-gradient(135deg, #34d399 0%, #059669 100%);
            --gradient-warning: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
        }
        
        [data-theme="dark"] {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
            --border-primary: #334155;
            --border-secondary: #475569;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 24px; 
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            line-height: 1.6;
        }
        
        .header {
            text-align: center;
            margin-bottom: 48px;
            position: relative;
        }
        
        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            background: var(--gradient-brand);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            font-weight: 400;
        }
        
        .glass-card { 
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: var(--radius-xl);
            padding: 32px;
            box-shadow: var(--shadow-xl);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .main-card {
            background: var(--bg-secondary);
            border-radius: var(--radius-xl);
            padding: 40px;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border-primary);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .form-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
        }
        
        @media (max-width: 768px) {
            .form-container {
                grid-template-columns: 1fr;
            }
        }
        
        .form-group { 
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        label { 
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        input { 
            padding: 16px 20px;
            border: 2px solid var(--border-primary);
            border-radius: var(--radius-md);
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            outline: none;
        }
        
        input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            transform: translateY(-2px);
        }
        
        .btn-primary { 
            background: var(--gradient-brand);
            color: white; 
            padding: 16px 32px; 
            border: none; 
            border-radius: var(--radius-md);
            cursor: pointer;
            font-weight: 600;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-md);
            position: relative;
            overflow: hidden;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
        }
        
        .btn-primary:active {
            transform: translateY(0);
        }
        
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 24px; 
            margin: 32px 0; 
        }
        
        .stat-card { 
            background: var(--bg-secondary);
            padding: 24px;
            border-radius: var(--radius-lg);
            text-align: center;
            border: 1px solid var(--border-primary);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: var(--gradient-brand);
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }
        
        .stat-value { 
            font-size: 2.5rem; 
            font-weight: 800; 
            background: var(--gradient-brand);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }
        
        .stat-label { 
            color: var(--text-secondary); 
            font-weight: 500;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .section-card { 
            background: var(--bg-secondary);
            margin: 32px 0; 
            padding: 32px; 
            border-radius: var(--radius-xl);
            border: 1px solid var(--border-primary);
            box-shadow: var(--shadow-md);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--border-primary);
        }
        
        .section-header h2 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0;
        }
        
        .section-icon {
            font-size: 1.5rem;
            background: var(--gradient-brand);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .video-grid {
            display: grid;
            gap: 16px;
        }
        
        .video-card { 
            padding: 20px;
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-md);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            background: var(--bg-primary);
            position: relative;
        }
        
        .video-card:hover {
            transform: translateX(8px);
            border-color: #667eea;
            box-shadow: var(--shadow-md);
        }
        
        .video-title { 
            font-weight: 600; 
            color: var(--text-primary);
            font-size: 1.1rem;
            margin-bottom: 8px;
            line-height: 1.4;
        }
        
        .video-stats { 
            color: var(--text-muted); 
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .loading-container { 
            text-align: center; 
            padding: 64px 32px; 
            display: none;
        }
        
        .loading-spinner {
            width: 48px;
            height: 48px;
            border: 4px solid var(--border-primary);
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 24px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .theme-toggle { 
            position: fixed; 
            top: 24px; 
            right: 24px; 
            background: var(--bg-secondary);
            border: 2px solid var(--border-primary);
            border-radius: 50%; 
            width: 56px; 
            height: 56px; 
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: var(--text-primary);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-md);
            z-index: 1000;
        }
        
        .theme-toggle:hover {
            transform: scale(1.1) rotate(10deg);
            box-shadow: var(--shadow-lg);
            border-color: #667eea;
        }
        
        .error-card {
            background: linear-gradient(135deg, #fecaca 0%, #f87171 100%);
            color: #7f1d1d;
            padding: 24px;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-md);
            border: 1px solid #fca5a5;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 16px;
            margin: 32px 0;
        }
        
        .pagination button {
            padding: 12px 20px;
            border: 2px solid var(--border-primary);
            background: var(--bg-secondary);
            color: var(--text-primary);
            border-radius: var(--radius-md);
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .pagination button:hover:not(:disabled) {
            border-color: #667eea;
            transform: translateY(-2px);
        }
        
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .page-info {
            font-weight: 600;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()" title="다크모드 토글">🌙</button>
    
    <div class="header">
        <h1>YouTube Analytics Pro</h1>
        <p class="subtitle">채널 데이터 분석 및 수익성 평가 도구</p>
    </div>
    
    <div class="main-card">
        <div class="form-container">
            <div class="form-group">
                <label>채널명 또는 URL</label>
                <input type="text" id="channelInput" value="로직알려주는남자" placeholder="채널명 또는 YouTube URL을 입력하세요">
            </div>
            
            <div class="form-group">
                <label>분석할 동영상 수</label>
                <input type="number" id="videoCount" value="30" min="10" max="300" placeholder="10-300">
            </div>
        </div>
        
        <button class="btn-primary" onclick="analyze()" id="analyzeBtn">
            🚀 분석 시작하기
        </button>
        
        <div class="loading-container" id="loading">
            <div class="loading-spinner"></div>
            <h3>데이터 분석 중...</h3>
            <p>YouTube API에서 채널 정보와 동영상 데이터를 수집하고 있습니다.</p>
        </div>
        
        <div class="result" id="result">
            <div id="content"></div>
        </div>
    </div>

    <script>
    async function analyze() {
        const channel = document.getElementById('channelInput').value;
        const maxVideos = document.getElementById('videoCount').value;
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        const btn = document.getElementById('analyzeBtn');
        const content = document.getElementById('content');
        
        if (!channel) {
            alert('Please enter channel name');
            return;
        }
        
        loading.style.display = 'block';
        result.style.display = 'none';
        btn.disabled = true;
        btn.textContent = '분석 중...';
        
        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: channel,
                    max_videos: parseInt(maxVideos)
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                content.innerHTML = '<div class="error-card"><h3>분석 실패</h3><p>' + data.error + '</p></div>';
            } else {
                window.lastAnalysisData = data;
                content.innerHTML = `
                    <div class="section-card">
                        <div class="section-header">
                            <span class="section-icon">📺</span>
                            <h2>채널 정보</h2>
                        </div>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${data.channel_name.length > 15 ? data.channel_name.substring(0, 15) + '...' : data.channel_name}</div>
                                <div class="stat-label">채널명</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${data.subscribers.toLocaleString()}</div>
                                <div class="stat-label">구독자 수</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${data.total_views.toLocaleString()}</div>
                                <div class="stat-label">총 조회수</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${data.video_count}</div>
                                <div class="stat-label">총 동영상 수</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section-card">
                        <div class="section-header">
                            <span class="section-icon">📊</span>
                            <h2>동영상 분석</h2>
                        </div>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${data.analyzed_videos}</div>
                                <div class="stat-label">분석된 동영상</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${data.avg_views.toLocaleString()}</div>
                                <div class="stat-label">평균 조회수</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${data.avg_engagement}%</div>
                                <div class="stat-label">평균 참여율</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section-card">
                        <div class="section-header">
                            <span class="section-icon">💰</span>
                            <h2>예상 수익 분석</h2>
                        </div>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">₩${(data.monthly_ad/10000).toFixed(0)}만</div>
                                <div class="stat-label">월 광고 수익</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">₩${(data.monthly_sponsor/10000).toFixed(0)}만</div>
                                <div class="stat-label">월 스폰서십</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">₩${(data.monthly_membership/10000).toFixed(0)}만</div>
                                <div class="stat-label">월 멤버십</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">₩${(data.total_monthly/10000).toFixed(0)}만</div>
                                <div class="stat-label">총 월 수익</div>
                            </div>
                        </div>
                        <div style="text-align: center; margin: 24px 0; padding: 20px; background: var(--gradient-success); color: white; border-radius: var(--radius-md); box-shadow: var(--shadow-md);">
                            <h3 style="margin: 0; font-size: 1.5rem; font-weight: 700;">📈 연간 예상 수익: ₩${(data.annual_revenue/100000000).toFixed(1)}억원</h3>
                        </div>
                    </div>
                    
                    <div class="section-card">
                        <div class="section-header">
                            <span class="section-icon">🏆</span>
                            <h2>인기 동영상 TOP 5</h2>
                        </div>
                        <div class="video-grid">
                            ${data.top_videos.map((video, i) => `
                                <div class="video-card" style="display: flex; gap: 20px; align-items: flex-start;">
                                    <img src="${video.thumbnail}" style="width: 160px; height: 120px; object-fit: cover; border-radius: var(--radius-md); flex-shrink: 0; box-shadow: var(--shadow-sm);" alt="썸네일">
                                    <div style="flex: 1; min-width: 0;">
                                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                                            <span style="background: var(--gradient-brand); color: white; font-weight: 700; padding: 6px 12px; border-radius: 20px; font-size: 0.875rem;">TOP ${i+1}</span>
                                        </div>
                                        <div class="video-title" style="margin-bottom: 12px;">
                                            <a href="${video.url}" target="_blank" style="text-decoration: none; color: var(--text-primary); font-weight: 600; font-size: 1.1rem; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                                                ${video.title}
                                            </a>
                                        </div>
                                        <div class="video-stats" style="display: flex; gap: 20px; flex-wrap: wrap;">
                                            <span>👀 ${video.views.toLocaleString()}회</span>
                                            <span>👍 ${video.likes.toLocaleString()}개</span>
                                            <span>📅 ${video.published}</span>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="section-card">
                        <div class="section-header">
                            <span class="section-icon">🆕</span>
                            <h2>최신 동영상 5개</h2>
                        </div>
                        <div class="video-grid">
                            ${data.recent_videos.map((video, i) => `
                                <div class="video-card" style="display: flex; gap: 20px; align-items: flex-start;">
                                    <img src="${video.thumbnail}" style="width: 160px; height: 120px; object-fit: cover; border-radius: var(--radius-md); flex-shrink: 0; box-shadow: var(--shadow-sm);" alt="썸네일">
                                    <div style="flex: 1; min-width: 0;">
                                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                                            <span style="background: var(--gradient-warning); color: white; font-weight: 700; padding: 6px 12px; border-radius: 20px; font-size: 0.875rem;">NEW</span>
                                        </div>
                                        <div class="video-title" style="margin-bottom: 12px;">
                                            <a href="${video.url}" target="_blank" style="text-decoration: none; color: var(--text-primary); font-weight: 600; font-size: 1.1rem; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                                                ${video.title}
                                            </a>
                                        </div>
                                        <div class="video-stats" style="display: flex; gap: 20px; flex-wrap: wrap;">
                                            <span>👀 ${video.views.toLocaleString()}회</span>
                                            <span>👍 ${video.likes.toLocaleString()}개</span>
                                            <span>📅 ${video.published}</span>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="section-card">
                        <div class="section-header">
                            <span class="section-icon">📋</span>
                            <h2>전체 동영상 목록</h2>
                        </div>
                        <div style="text-align: center; margin: 32px 0;">
                            <button class="btn-primary" onclick="showAllVideos()" id="showAllBtn">
                                📋 전체 동영상 목록 보기 (${data.analyzed_videos}개)
                            </button>
                        </div>
                        <div id="allVideosList" style="display: none; margin-top: 20px;"></div>
                    </div>
                `;
            }
            
        } catch (error) {
            content.innerHTML = '<div class="error"><h3>오류</h3><p>' + error.message + '</p></div>';
        }
        
        loading.style.display = 'none';
        result.style.display = 'block';
        btn.disabled = false;
        btn.textContent = '완전 분석 시작';
    }
    
    let allVideosData = null;
    let currentPage = 1;
    const videosPerPage = 10;
    
    async function showAllVideos() {
        const channelId = window.lastAnalysisData?.channel_id;
        const maxVideos = window.lastAnalysisData?.input_max_videos || window.lastAnalysisData?.analyzed_videos || 30;
        if (!channelId) {
            alert('분석을 먼저 진행해주세요');
            return;
        }
        
        const btn = document.getElementById('showAllBtn');
        btn.disabled = true;
        btn.textContent = '로딩 중...';
        
        try {
            const response = await fetch('/get_all_videos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel_id: channelId, max_videos: maxVideos })
            });
            
            const data = await response.json();
            
            if (data.error) {
                alert('오류: ' + data.error);
            } else {
                allVideosData = data.videos;
                currentPage = 1;
                displayPaginatedVideos();
                document.getElementById('allVideosList').style.display = 'block';
                btn.textContent = '목록 숨기기';
                btn.onclick = hideAllVideos;
            }
            
        } catch (error) {
            alert('네트워크 오류: ' + error.message);
        }
        
        btn.disabled = false;
    }
    
    function hideAllVideos() {
        document.getElementById('allVideosList').style.display = 'none';
        const btn = document.getElementById('showAllBtn');
        btn.textContent = '전체 동영상 보기';
        btn.onclick = showAllVideos;
    }
    
    function displayPaginatedVideos() {
        const startIndex = (currentPage - 1) * videosPerPage;
        const endIndex = startIndex + videosPerPage;
        const pageVideos = allVideosData.slice(startIndex, endIndex);
        const totalPages = Math.ceil(allVideosData.length / videosPerPage);
        
        const videosList = pageVideos.map((video, i) => `
            <div class="video-card" style="display: flex; gap: 20px; align-items: flex-start;">
                <img src="${video.thumbnail}" style="width: 160px; height: 120px; object-fit: cover; border-radius: var(--radius-md); flex-shrink: 0; box-shadow: var(--shadow-sm);" alt="썸네일">
                <div style="flex: 1; min-width: 0;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <span style="background: var(--gradient-brand); color: white; font-weight: 700; padding: 6px 12px; border-radius: 20px; font-size: 0.875rem;">#${startIndex + i + 1}</span>
                    </div>
                    <div class="video-title" style="margin-bottom: 12px;">
                        <a href="${video.url}" target="_blank" style="text-decoration: none; color: var(--text-primary); font-weight: 600; font-size: 1.1rem; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                            ${video.title}
                        </a>
                    </div>
                    <div class="video-stats" style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <span>👀 ${video.views.toLocaleString()}회</span>
                        <span>👍 ${video.likes.toLocaleString()}개</span>
                        <span>📅 ${video.published}</span>
                    </div>
                </div>
            </div>
        `).join('');
        
        const pagination = `
            <div class="pagination">
                <button onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>← 이전</button>
                <span class="page-info">페이지 ${currentPage} / ${totalPages}</span>
                <button onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>다음 →</button>
            </div>
        `;
        
        document.getElementById('allVideosList').innerHTML = `
            <h4>전체 동영상 목록 (총 ${allVideosData.length}개)</h4>
            ${pagination}
            ${videosList}
            ${pagination}
        `;
    }
    
    function changePage(page) {
        const totalPages = Math.ceil(allVideosData.length / videosPerPage);
        if (page < 1 || page > totalPages) return;
        
        currentPage = page;
        displayPaginatedVideos();
    }
    
    function toggleTheme() {
        const body = document.body;
        const themeToggle = document.querySelector('.theme-toggle');
        const currentTheme = body.getAttribute('data-theme');
        
        if (currentTheme === 'dark') {
            body.removeAttribute('data-theme');
            themeToggle.innerHTML = '🌙';
            localStorage.setItem('theme', 'light');
        } else {
            body.setAttribute('data-theme', 'dark');
            themeToggle.innerHTML = '☀️';
            localStorage.setItem('theme', 'dark');
        }
    }
    
    // Load saved theme on page load
    window.addEventListener('DOMContentLoaded', function() {
        const savedTheme = localStorage.getItem('theme');
        const themeToggle = document.querySelector('.theme-toggle');
        
        if (savedTheme === 'dark') {
            document.body.setAttribute('data-theme', 'dark');
            themeToggle.innerHTML = '☀️';
        } else {
            themeToggle.innerHTML = '🌙';
        }
    });
    
    </script>
</body>
</html>
    '''

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json(force=True)
        query = data.get('query', '')
        max_videos = data.get('max_videos', 30)
        
        print(f"Received query: {query}, max_videos: {max_videos}")
        
        result = analyzer.analyze_complete(query, max_videos)
        return jsonify(result)
        
    except Exception as e:
        print(f"Analyze error: {e}")
        return jsonify({'error': str(e)})

@app.route('/get_all_videos', methods=['POST'])
def get_all_videos():
    try:
        data = request.get_json(force=True)
        channel_id = data.get('channel_id', '')
        max_videos = data.get('max_videos', 100)
        
        videos = analyzer.get_all_videos(channel_id, max_videos)
        return jsonify({'videos': videos, 'total': len(videos)})
        
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    print("=" * 50)
    print("YouTube 완전 분석 도구")
    print("주소: http://localhost:8080")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=8080)