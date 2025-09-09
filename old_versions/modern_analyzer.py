# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime

app = Flask(__name__)
API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

class ModernAnalyzer:
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    def search_channel(self, query):
        try:
            import re
            from urllib.parse import unquote
            
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
                    if pattern == r'youtube\.com/channel/([^/]+)':
                        return channel_name
                    query = channel_name
                    break
            
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
    
    def get_videos(self, channel_id, max_videos=30):
        try:
            channel_info = self.get_channel_info(channel_id)
            uploads_id = channel_info['contentDetails']['relatedPlaylists']['uploads']
            
            videos = []
            next_page_token = None
            
            while len(videos) < max_videos:
                request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_id,
                    maxResults=min(50, max_videos - len(videos)),
                    pageToken=next_page_token
                )
                response = request.execute()
                
                video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
                
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
            print(f"Video Error: {e}")
            return []
    
    def analyze_complete(self, query, max_videos=30):
        try:
            print(f"Analysis Start: {query}, Videos: {max_videos}")
            
            channel_id = self.search_channel(query)
            if not channel_id:
                return {'error': 'Channel not found'}
            
            print(f"Channel ID: {channel_id}")
            
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return {'error': 'No channel info'}
            
            videos = self.get_videos(channel_id, max_videos)
            
            stats = channel_info['statistics']
            subscribers = int(stats.get('subscriberCount', 0))
            total_views = int(stats.get('viewCount', 0))
            video_count = int(stats.get('videoCount', 0))
            
            if videos:
                total_video_views = sum(v['views'] for v in videos)
                avg_views = int(total_video_views / len(videos))
                total_likes = sum(v['likes'] for v in videos)
                avg_engagement = (total_likes / total_video_views * 100) if total_video_views > 0 else 0
                
                top_videos = sorted(videos, key=lambda x: x['views'], reverse=True)[:5]
                recent_videos = videos[:5]
            else:
                avg_views = int(subscribers * 0.3)
                avg_engagement = 3.0
                top_videos = []
                recent_videos = []
            
            monthly_ad = (avg_views * 8 / 1000) * 3000
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
                'input_max_videos': max_videos,
                'all_videos': videos
            }
            
        except Exception as e:
            print(f"Analysis Error: {e}")
            return {'error': f'Analysis Error: {str(e)}'}

analyzer = ModernAnalyzer()

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>YouTube Analytics Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .navbar {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            padding: 15px 0;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #764ba2;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .nav-menu {
            display: flex;
            gap: 30px;
        }
        
        .nav-item {
            color: #333;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .nav-item:hover { color: #764ba2; }
        .nav-item.active { color: #764ba2; }
        
        .main-container {
            margin-top: 80px;
            padding: 40px 20px;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .hero-section {
            text-align: center;
            margin-bottom: 50px;
            color: white;
        }
        
        .hero-title {
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .hero-subtitle {
            font-size: 20px;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }
        
        .form-section {
            display: grid;
            grid-template-columns: 1fr 200px;
            gap: 20px;
            margin-bottom: 30px;
            align-items: end;
        }
        
        .form-group {
            position: relative;
        }
        
        .form-label {
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            display: block;
            font-size: 14px;
        }
        
        .form-input {
            width: 100%;
            padding: 15px 20px 15px 50px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s;
            background: rgba(255,255,255,0.9);
        }
        
        .form-input:focus {
            outline: none;
            border-color: #764ba2;
            box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.1);
        }
        
        .input-icon {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: #764ba2;
            font-size: 18px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(118, 75, 162, 0.4);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 5px;
            position: relative;
            z-index: 1;
        }
        
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }
        
        .section-title {
            font-size: 24px;
            font-weight: 700;
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .loading {
            text-align: center;
            padding: 60px;
            display: none;
            color: #333;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #e1e5e9;
            border-top: 4px solid #764ba2;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
        }
        
        .result { display: none; }
        
        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .video-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        
        .video-card:hover {
            transform: translateY(-5px);
        }
        
        .video-thumbnail {
            width: 100%;
            height: 180px;
            object-fit: cover;
        }
        
        .video-info {
            padding: 20px;
        }
        
        .video-title-link {
            text-decoration: none;
            color: #333;
            font-weight: 600;
            font-size: 16px;
            display: block;
            margin-bottom: 10px;
            transition: color 0.3s;
            line-height: 1.4;
        }
        
        .video-title-link:hover { color: #764ba2; }
        
        .video-stats {
            color: #666;
            font-size: 14px;
        }
        
        .tabs {
            display: flex;
            gap: 0;
            margin-bottom: 20px;
            background: #f8f9fa;
            border-radius: 12px;
            padding: 4px;
        }
        
        .tab {
            flex: 1;
            padding: 12px 20px;
            background: none;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            color: #666;
        }
        
        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 30px 0;
        }
        
        .pagination button {
            padding: 10px 15px;
            border: 2px solid #e1e5e9;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .pagination button:hover {
            border-color: #764ba2;
            color: #764ba2;
        }
        
        .pagination button.active {
            background: #764ba2;
            color: white;
            border-color: #764ba2;
        }
        
        @media (max-width: 768px) {
            .form-section { grid-template-columns: 1fr; }
            .hero-title { font-size: 32px; }
            .nav-menu { display: none; }
            .stats-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <!-- 네비게이션 바 -->
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fab fa-youtube"></i>
                YouTube Analytics Pro
            </div>
            <div class="nav-menu">
                <a href="#" class="nav-item active"><i class="fas fa-home"></i> 홈</a>
                <a href="#" class="nav-item"><i class="fas fa-chart-line"></i> 분석</a>
                <a href="#" class="nav-item"><i class="fas fa-star"></i> 즐겨찾기</a>
                <a href="#" class="nav-item"><i class="fas fa-cog"></i> 설정</a>
            </div>
        </div>
    </nav>

    <div class="main-container">
        <!-- 히어로 섹션 -->
        <div class="hero-section">
            <h1 class="hero-title">YouTube Analytics Pro</h1>
            <p class="hero-subtitle">유튜브 채널을 분석하고 수익성을 확인하세요</p>
        </div>

        <!-- 분석 입력 섹션 -->
        <div class="card">
            <div class="section-title">
                <i class="fas fa-search"></i>
                채널 분석하기
            </div>
            
            <div class="form-section">
                <div class="form-group">
                    <label class="form-label">채널명 또는 URL</label>
                    <div style="position: relative;">
                        <i class="fas fa-search input-icon"></i>
                        <input type="text" id="channelInput" class="form-input" 
                               value="로직알려주는남자" placeholder="채널명 또는 YouTube URL을 입력하세요">
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">분석할 동영상 수</label>
                    <input type="number" id="videoCount" class="form-input" 
                           value="30" min="10" max="300" style="padding-left: 20px;">
                </div>
            </div>
            
            <button class="btn" onclick="analyze()" id="analyzeBtn">
                <i class="fas fa-chart-line"></i>
                분석 시작하기
            </button>
        </div>

        <!-- 로딩 -->
        <div class="card loading" id="loading">
            <div class="spinner"></div>
            <h3>채널을 분석하고 있습니다...</h3>
            <p>잠시만 기다려 주세요</p>
        </div>

        <!-- 결과 -->
        <div class="result" id="result">
            <div id="content"></div>
        </div>
    </div>

    <script>
    let analysisData = null;
    let currentPage = 1;
    const videosPerPage = 12;
    
    async function analyze() {
        const channel = document.getElementById('channelInput').value;
        const maxVideos = document.getElementById('videoCount').value;
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        const btn = document.getElementById('analyzeBtn');
        const content = document.getElementById('content');
        
        if (!channel.trim()) {
            alert('채널명을 입력하세요');
            return;
        }
        
        loading.style.display = 'block';
        result.style.display = 'none';
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 분석 중...';
        
        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: channel.trim(),
                    max_videos: parseInt(maxVideos)
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                content.innerHTML = '<div class="error"><h3><i class="fas fa-exclamation-triangle"></i> 분석 실패</h3><p>' + data.error + '</p></div>';
            } else {
                analysisData = data;
                displayResults(data);
            }
            
        } catch (error) {
            content.innerHTML = '<div class="error"><h3><i class="fas fa-wifi"></i> 네트워크 오류</h3><p>' + error.message + '</p></div>';
        }
        
        loading.style.display = 'none';
        result.style.display = 'block';
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-chart-line"></i> 분석 시작하기';
    }
    
    function displayResults(data) {
        document.getElementById('content').innerHTML = `
            <!-- 채널 정보 -->
            <div class="card">
                <div class="section-title">
                    <i class="fas fa-tv"></i>
                    ${data.channel_name}
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${data.subscribers.toLocaleString()}</div>
                        <div class="stat-label">구독자</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.total_views.toLocaleString()}</div>
                        <div class="stat-label">총 조회수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.video_count}</div>
                        <div class="stat-label">총 동영상</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.avg_engagement}%</div>
                        <div class="stat-label">평균 참여율</div>
                    </div>
                </div>
            </div>
            
            <!-- 수익 정보 -->
            <div class="card">
                <div class="section-title">
                    <i class="fas fa-money-bill-wave"></i>
                    예상 수익
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                        <div class="stat-value">${data.monthly_ad.toLocaleString()}원</div>
                        <div class="stat-label">월 광고 수익</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                        <div class="stat-value">${data.monthly_sponsor.toLocaleString()}원</div>
                        <div class="stat-label">월 스폰서십</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                        <div class="stat-value">${data.monthly_membership.toLocaleString()}원</div>
                        <div class="stat-label">월 멤버십</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333;">
                        <div class="stat-value">${data.total_monthly.toLocaleString()}원</div>
                        <div class="stat-label">총 월 수익</div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;">
                    <h2 style="margin-bottom: 10px;">연 예상 수익</h2>
                    <div style="font-size: 48px; font-weight: bold;">${data.annual_revenue.toLocaleString()}원</div>
                </div>
            </div>
            
            <!-- 동영상 탭 -->
            <div class="card">
                <div class="section-title">
                    <i class="fas fa-video"></i>
                    동영상 분석
                </div>
                
                <div class="tabs">
                    <button class="tab active" onclick="showTab('popular')">인기 동영상</button>
                    <button class="tab" onclick="showTab('recent')">최신 동영상</button>
                    <button class="tab" onclick="showTab('all')">전체 목록</button>
                </div>
                
                <div id="popular" class="tab-content active">
                    <div class="video-grid">
                        ${data.top_videos.map(video => `
                            <div class="video-card">
                                <img src="${video.thumbnail}" alt="썸네일" class="video-thumbnail">
                                <div class="video-info">
                                    <a href="${video.url}" target="_blank" class="video-title-link">
                                        ${video.title}
                                    </a>
                                    <div class="video-stats">
                                        <i class="fas fa-eye"></i> ${video.views.toLocaleString()}회 |
                                        <i class="fas fa-thumbs-up"></i> ${video.likes.toLocaleString()}개 |
                                        <i class="fas fa-calendar"></i> ${video.published}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div id="recent" class="tab-content">
                    <div class="video-grid">
                        ${data.recent_videos.map(video => `
                            <div class="video-card">
                                <img src="${video.thumbnail}" alt="썸네일" class="video-thumbnail">
                                <div class="video-info">
                                    <a href="${video.url}" target="_blank" class="video-title-link">
                                        ${video.title}
                                    </a>
                                    <div class="video-stats">
                                        <i class="fas fa-eye"></i> ${video.views.toLocaleString()}회 |
                                        <i class="fas fa-thumbs-up"></i> ${video.likes.toLocaleString()}개 |
                                        <i class="fas fa-calendar"></i> ${video.published}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div id="all" class="tab-content">
                    <div id="allVideosList">
                        <div class="video-grid" id="allVideosGrid"></div>
                        <div class="pagination" id="pagination"></div>
                    </div>
                </div>
            </div>
        `;
        
        displayAllVideos();
    }
    
    function showTab(tabName) {
        // 모든 탭 비활성화
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // 선택된 탭 활성화
        event.target.classList.add('active');
        document.getElementById(tabName).classList.add('active');
    }
    
    function displayAllVideos() {
        if (!analysisData || !analysisData.all_videos) return;
        
        const videos = analysisData.all_videos;
        const totalPages = Math.ceil(videos.length / videosPerPage);
        const startIndex = (currentPage - 1) * videosPerPage;
        const endIndex = startIndex + videosPerPage;
        const pageVideos = videos.slice(startIndex, endIndex);
        
        // 비디오 그리드
        document.getElementById('allVideosGrid').innerHTML = pageVideos.map(video => `
            <div class="video-card">
                <img src="${video.thumbnail}" alt="썸네일" class="video-thumbnail">
                <div class="video-info">
                    <a href="${video.url}" target="_blank" class="video-title-link">
                        ${video.title}
                    </a>
                    <div class="video-stats">
                        <i class="fas fa-eye"></i> ${video.views.toLocaleString()}회 |
                        <i class="fas fa-thumbs-up"></i> ${video.likes.toLocaleString()}개 |
                        <i class="fas fa-calendar"></i> ${video.published}
                    </div>
                </div>
            </div>
        `).join('');
        
        // 페이지네이션
        let paginationHTML = '';
        if (currentPage > 1) {
            paginationHTML += '<button onclick="changePage(' + (currentPage - 1) + ')">이전</button>';
        }
        
        for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
            paginationHTML += `<button onclick="changePage(${i})" ${i === currentPage ? 'class="active"' : ''}>${i}</button>`;
        }
        
        if (currentPage < totalPages) {
            paginationHTML += '<button onclick="changePage(' + (currentPage + 1) + ')">다음</button>';
        }
        
        document.getElementById('pagination').innerHTML = paginationHTML;
    }
    
    function changePage(page) {
        currentPage = page;
        displayAllVideos();
    }
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

if __name__ == '__main__':
    print("=" * 50)
    print("YouTube Analytics Pro")
    print("Address: http://localhost:8080")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=8080)