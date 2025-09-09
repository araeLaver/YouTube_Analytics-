# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)

API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

class ServiceYouTubeAnalyzer:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def search_channel(self, query):
        """채널 검색"""
        try:
            search_response = self.youtube.search().list(
                q=query,
                part='snippet',
                type='channel',
                maxResults=1
            ).execute()
            
            if search_response['items']:
                return search_response['items'][0]['snippet']['channelId']
            return None
        except Exception as e:
            print(f"검색 오류: {e}")
            return None
    
    def get_channel_info(self, channel_id):
        """채널 기본 정보"""
        try:
            response = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            ).execute()
            
            if response['items']:
                return response['items'][0]
            return None
        except Exception as e:
            print(f"채널 정보 오류: {e}")
            return None
    
    def get_videos(self, channel_id, max_results=20):
        """채널의 동영상들 가져오기"""
        try:
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return []
            
            uploads_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']
            
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                ).execute()
                
                video_ids = [item['snippet']['resourceId']['videoId'] 
                           for item in playlist_response['items']]
                
                videos_response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids)
                ).execute()
                
                for video in videos_response['items']:
                    video_data = {
                        'video_id': video['id'],
                        'title': video['snippet']['title'],
                        'description': video['snippet']['description'][:200],
                        'published_date': video['snippet']['publishedAt'],
                        'duration': video['contentDetails']['duration'],
                        'view_count': int(video['statistics'].get('viewCount', 0)),
                        'like_count': int(video['statistics'].get('likeCount', 0)),
                        'comment_count': int(video['statistics'].get('commentCount', 0)),
                        'thumbnail': video['snippet']['thumbnails']['medium']['url']
                    }
                    videos.append(video_data)
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return videos
            
        except Exception as e:
            print(f"동영상 목록 오류: {e}")
            return []

    def analyze_complete(self, query, max_videos=20):
        """완전 분석"""
        try:
            # URL에서 채널 ID 추출
            channel_id = self.extract_channel_id(query)
            if not channel_id:
                channel_id = self.search_channel(query)
            
            if not channel_id:
                return {'error': '채널을 찾을 수 없습니다.'}
            
            # 채널 정보
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return {'error': '채널 정보를 가져올 수 없습니다.'}
            
            # 동영상 정보
            videos = self.get_videos(channel_id, max_videos)
            
            # 통계 계산
            stats = self.calculate_stats(channel_info, videos)
            
            return {
                'channel_info': channel_info,
                'videos': videos,
                'stats': stats,
                'revenue_analysis': self.calculate_revenue(channel_info, videos)
            }
            
        except Exception as e:
            return {'error': f'분석 중 오류 발생: {str(e)}'}

    def extract_channel_id(self, url):
        """URL에서 채널 ID 추출"""
        patterns = [
            r'youtube\.com/channel/([^/?]+)',
            r'youtube\.com/@([^/?]+)',
            r'youtube\.com/c/([^/?]+)',
            r'youtube\.com/user/([^/?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                if '@' in pattern:
                    return self.search_channel(match.group(1))
                elif 'channel/' in pattern:
                    return match.group(1)
                else:
                    return self.search_channel(match.group(1))
        return None

    def calculate_stats(self, channel_info, videos):
        """통계 계산"""
        stats = channel_info['statistics']
        
        if videos:
            total_views = sum(v['view_count'] for v in videos)
            avg_views = total_views // len(videos)
            total_likes = sum(v['like_count'] for v in videos)
            engagement_rate = (total_likes / total_views * 100) if total_views > 0 else 0
        else:
            avg_views = 0
            engagement_rate = 0
        
        return {
            'subscriber_count': int(stats.get('subscriberCount', 0)),
            'total_views': int(stats.get('viewCount', 0)),
            'video_count': int(stats.get('videoCount', 0)),
            'avg_views': avg_views,
            'engagement_rate': round(engagement_rate, 2)
        }

    def calculate_revenue(self, channel_info, videos):
        """수익 계산"""
        stats = self.calculate_stats(channel_info, videos)
        subscribers = stats['subscriber_count']
        avg_views = stats['avg_views']
        
        # CPM 기반 광고 수익 (월 8개 영상 가정)
        monthly_views = avg_views * 8
        monthly_ad_revenue = (monthly_views / 1000) * 3000  # CPM 3000원
        
        # 스폰서십 수익
        if subscribers >= 100000:
            monthly_sponsorship = subscribers * 80 // 12
            tier = "프리미엄 채널"
        elif subscribers >= 10000:
            monthly_sponsorship = subscribers * 50 // 12
            tier = "성장 채널"
        else:
            monthly_sponsorship = subscribers * 20 // 12
            tier = "신규 채널"
        
        # 멤버십 수익 (구독자의 1.5%)
        monthly_membership = subscribers * 0.015 * 4900 if subscribers >= 1000 else 0
        
        total_monthly = int(monthly_ad_revenue + monthly_sponsorship + monthly_membership)
        
        return {
            'monthly_ad': int(monthly_ad_revenue),
            'monthly_sponsorship': int(monthly_sponsorship),
            'monthly_membership': int(monthly_membership),
            'total_monthly': total_monthly,
            'annual_estimate': total_monthly * 12,
            'tier': tier
        }

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Analytics Pro - 프리미엄 채널 분석 서비스</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #f8fafc;
            --accent: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --border: #e2e8f0;
            --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 25px 50px -12px rgb(0 0 0 / 0.25);
            --radius: 16px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        [data-theme="dark"] {
            --primary: #6366f1;
            --secondary: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
            --border: #334155;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--secondary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }

        /* Header */
        .header {
            background: var(--bg-gradient);
            padding: 4rem 0 6rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            animation: float 20s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(180deg); }
        }

        .header-content {
            position: relative;
            z-index: 2;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }

        .header h1 {
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 800;
            color: white;
            margin-bottom: 1rem;
            text-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }

        .header .subtitle {
            font-size: 1.25rem;
            color: rgba(255,255,255,0.9);
            font-weight: 500;
            max-width: 600px;
            margin: 0 auto;
        }

        /* Main Container */
        .container {
            max-width: 1200px;
            margin: -3rem auto 0;
            padding: 0 2rem 4rem;
            position: relative;
            z-index: 3;
        }

        /* Analysis Card */
        .analysis-card {
            background: white;
            border-radius: var(--radius);
            box-shadow: var(--shadow-lg);
            padding: 3rem;
            margin-bottom: 3rem;
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }

        .analysis-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--bg-gradient);
        }

        .card-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .card-title i {
            color: var(--primary);
        }

        /* Form */
        .form-grid {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        @media (max-width: 768px) {
            .form-grid {
                grid-template-columns: 1fr;
            }
        }

        .form-group {
            position: relative;
        }

        .form-input {
            width: 100%;
            padding: 1rem 1.25rem;
            border: 2px solid var(--border);
            border-radius: var(--radius);
            font-size: 1rem;
            font-weight: 500;
            background: white;
            color: var(--text-primary);
            transition: var(--transition);
            outline: none;
        }

        .form-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            transform: translateY(-2px);
        }

        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: var(--radius);
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            white-space: nowrap;
        }

        .btn-primary {
            background: var(--bg-gradient);
            color: white;
            box-shadow: var(--shadow);
        }

        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* Examples */
        .examples {
            margin: 2rem 0;
            padding: 1.5rem;
            background: rgba(99, 102, 241, 0.05);
            border-radius: var(--radius);
            border: 1px solid rgba(99, 102, 241, 0.1);
        }

        .examples h3 {
            font-size: 1rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .example-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .example-tag {
            padding: 0.5rem 1rem;
            background: white;
            border: 1px solid var(--border);
            border-radius: 50px;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            transition: var(--transition);
        }

        .example-tag:hover {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
            transform: translateY(-1px);
        }

        /* Loading */
        .loading {
            display: none;
            text-align: center;
            padding: 3rem 0;
        }

        .loading.show {
            display: block;
        }

        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid rgba(99, 102, 241, 0.1);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1.5rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .loading h3 {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .loading p {
            color: var(--text-secondary);
        }

        /* Progress Bar */
        .progress-container {
            margin: 2rem 0;
            display: none;
        }

        .progress-container.show {
            display: block;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(99, 102, 241, 0.1);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--bg-gradient);
            border-radius: 4px;
            transition: width 0.5s ease;
            width: 0%;
        }

        .progress-text {
            text-align: center;
            margin-top: 1rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        /* Results */
        .results {
            display: none;
        }

        .results.show {
            display: block;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }

        .stat-card {
            background: white;
            padding: 2rem;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            text-align: center;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--bg-gradient);
        }

        .stat-icon {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(99, 102, 241, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
            font-size: 1.5rem;
            color: var(--primary);
        }

        .stat-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
            line-height: 1;
        }

        .stat-label {
            color: var(--text-secondary);
            font-weight: 500;
        }

        /* Revenue Section */
        .revenue-section {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%);
            padding: 2rem;
            border-radius: var(--radius);
            margin: 2rem 0;
            border: 1px solid rgba(16, 185, 129, 0.1);
        }

        .revenue-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .total-revenue {
            text-align: center;
            padding: 2rem;
            background: white;
            border-radius: var(--radius);
            margin-top: 2rem;
            box-shadow: var(--shadow);
        }

        .total-amount {
            font-size: 3rem;
            font-weight: 900;
            background: var(--bg-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }

        /* Video Grid */
        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }

        .video-card {
            background: white;
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            transition: var(--transition);
        }

        .video-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }

        .video-thumbnail {
            position: relative;
            width: 100%;
            height: 180px;
            overflow: hidden;
        }

        .video-thumbnail img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: var(--transition);
        }

        .video-card:hover .video-thumbnail img {
            transform: scale(1.05);
        }

        .video-views {
            position: absolute;
            bottom: 0.5rem;
            right: 0.5rem;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .video-content {
            padding: 1.5rem;
        }

        .video-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.75rem;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .video-stats {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        .video-stat {
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }

        /* Theme Toggle */
        .theme-toggle {
            position: fixed;
            top: 2rem;
            right: 2rem;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: white;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            color: var(--text-primary);
            transition: var(--transition);
            z-index: 1000;
        }

        .theme-toggle:hover {
            transform: scale(1.1);
            box-shadow: var(--shadow-lg);
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 0 1rem 2rem;
                margin-top: -2rem;
            }

            .analysis-card {
                padding: 2rem 1.5rem;
            }

            .header h1 {
                font-size: 2.5rem;
            }

            .stats-grid {
                grid-template-columns: 1fr;
                gap: 1rem;
            }

            .video-grid {
                grid-template-columns: 1fr;
            }

            .theme-toggle {
                top: 1rem;
                right: 1rem;
                width: 50px;
                height: 50px;
            }
        }

        /* Animations */
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .slide-up {
            animation: slideUp 0.8s ease-out;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(40px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>
<body>
    <!-- Theme Toggle -->
    <button class="theme-toggle" onclick="toggleTheme()" aria-label="테마 변경">
        <i class="fas fa-moon"></i>
    </button>

    <!-- Header -->
    <header class="header">
        <div class="header-content">
            <h1>YouTube Analytics Pro</h1>
            <p class="subtitle">AI 기반 채널 분석으로 당신의 YouTube 성공을 도와드립니다</p>
        </div>
    </header>

    <!-- Main Container -->
    <div class="container">
        <!-- Analysis Card -->
        <div class="analysis-card fade-in">
            <h2 class="card-title">
                <i class="fas fa-chart-line"></i>
                채널 분석 시작하기
            </h2>

            <form id="analysisForm">
                <div class="form-grid">
                    <div class="form-group">
                        <input type="text" id="channelUrl" class="form-input" 
                               placeholder="YouTube 채널 URL 또는 채널명을 입력하세요..." 
                               required autocomplete="off">
                    </div>
                    <button type="submit" class="btn btn-primary" id="analyzeBtn">
                        <i class="fas fa-search"></i>
                        분석 시작
                    </button>
                </div>

                <!-- Examples -->
                <div class="examples">
                    <h3>
                        <i class="fas fa-lightbulb"></i>
                        인기 채널로 체험해보기
                    </h3>
                    <div class="example-tags">
                        <span class="example-tag" onclick="setChannel('https://www.youtube.com/@로직알려주는남자')">로직알려주는남자</span>
                        <span class="example-tag" onclick="setChannel('https://www.youtube.com/@코딩애플')">코딩애플</span>
                        <span class="example-tag" onclick="setChannel('https://www.youtube.com/@노마드코더')">노마드코더</span>
                        <span class="example-tag" onclick="setChannel('https://www.youtube.com/@보다BODA')">보다BODA</span>
                        <span class="example-tag" onclick="setChannel('https://www.youtube.com/@빵형의개발도상국')">빵형의개발도상국</span>
                    </div>
                </div>

                <!-- Progress -->
                <div class="progress-container" id="progressContainer">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText">분석 준비 중...</div>
                </div>
            </form>

            <!-- Loading -->
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <h3>채널을 분석하고 있습니다</h3>
                <p>YouTube API를 통해 데이터를 수집하고 있어요. 잠시만 기다려주세요!</p>
            </div>
        </div>

        <!-- Results -->
        <div class="results" id="results">
            <div id="resultsContent"></div>
        </div>
    </div>

    <script>
        let currentTheme = 'light';

        // Theme Toggle
        function toggleTheme() {
            currentTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', currentTheme);
            const icon = document.querySelector('.theme-toggle i');
            icon.className = currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
            localStorage.setItem('theme', currentTheme);
        }

        // Load saved theme
        function loadTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            currentTheme = savedTheme;
            document.documentElement.setAttribute('data-theme', currentTheme);
            const icon = document.querySelector('.theme-toggle i');
            icon.className = currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }

        // Set example channel
        function setChannel(url) {
            document.getElementById('channelUrl').value = url;
            document.getElementById('channelUrl').focus();
        }

        // Format number
        function formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(1) + 'M';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'K';
            }
            return num.toString();
        }

        // Format Korean currency
        function formatCurrency(amount) {
            if (amount >= 100000000) {
                return Math.floor(amount / 100000000) + '억 ' + Math.floor((amount % 100000000) / 10000) + '만원';
            } else if (amount >= 10000) {
                return Math.floor(amount / 10000) + '만원';
            }
            return amount.toLocaleString() + '원';
        }

        // Progress animation
        function updateProgress(percent, text) {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            const progressContainer = document.getElementById('progressContainer');
            
            progressContainer.classList.add('show');
            progressFill.style.width = percent + '%';
            progressText.textContent = text;
        }

        // Form submission
        document.getElementById('analysisForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const channelUrl = document.getElementById('channelUrl').value;
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            const analyzeBtn = document.getElementById('analyzeBtn');
            const progressContainer = document.getElementById('progressContainer');
            
            // Reset states
            loading.classList.add('show');
            results.classList.remove('show');
            analyzeBtn.disabled = true;
            progressContainer.classList.remove('show');
            
            // Progress simulation
            updateProgress(10, '채널 정보 수집 중...');
            
            setTimeout(() => updateProgress(30, '동영상 데이터 분석 중...'), 500);
            setTimeout(() => updateProgress(60, '통계 계산 중...'), 1500);
            setTimeout(() => updateProgress(90, '수익 분석 중...'), 2500);
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({channel_url: channelUrl})
                });
                
                const data = await response.json();
                
                if (data.error) {
                    alert('오류: ' + data.error);
                    return;
                }
                
                updateProgress(100, '분석 완료!');
                
                setTimeout(() => {
                    displayResults(data);
                    loading.classList.remove('show');
                    results.classList.add('show');
                    progressContainer.classList.remove('show');
                    
                    // Scroll to results
                    results.scrollIntoView({behavior: 'smooth', block: 'start'});
                }, 500);
                
            } catch (error) {
                alert('분석 중 오류가 발생했습니다: ' + error.message);
            } finally {
                analyzeBtn.disabled = false;
            }
        });

        function displayResults(data) {
            const { channel_info, videos, stats, revenue_analysis } = data;
            
            const resultsHTML = `
                <div class="analysis-card slide-up">
                    <h2 class="card-title">
                        <i class="fas fa-trophy"></i>
                        ${channel_info.snippet.title} 분석 결과
                    </h2>
                    
                    <!-- Channel Stats -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-users"></i>
                            </div>
                            <div class="stat-value">${formatNumber(stats.subscriber_count)}</div>
                            <div class="stat-label">구독자</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-eye"></i>
                            </div>
                            <div class="stat-value">${formatNumber(stats.total_views)}</div>
                            <div class="stat-label">총 조회수</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-play-circle"></i>
                            </div>
                            <div class="stat-value">${stats.video_count}</div>
                            <div class="stat-label">동영상 수</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-chart-bar"></i>
                            </div>
                            <div class="stat-value">${formatNumber(stats.avg_views)}</div>
                            <div class="stat-label">평균 조회수</div>
                        </div>
                    </div>
                    
                    <!-- Revenue Analysis -->
                    <div class="revenue-section">
                        <h3 class="revenue-title">
                            <i class="fas fa-dollar-sign"></i>
                            예상 수익 분석
                        </h3>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-icon">
                                    <i class="fas fa-ad"></i>
                                </div>
                                <div class="stat-value">${formatCurrency(revenue_analysis.monthly_ad)}</div>
                                <div class="stat-label">월 광고 수익</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-icon">
                                    <i class="fas fa-handshake"></i>
                                </div>
                                <div class="stat-value">${formatCurrency(revenue_analysis.monthly_sponsorship)}</div>
                                <div class="stat-label">월 스폰서십</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-icon">
                                    <i class="fas fa-crown"></i>
                                </div>
                                <div class="stat-value">${formatCurrency(revenue_analysis.monthly_membership)}</div>
                                <div class="stat-label">월 멤버십</div>
                            </div>
                        </div>
                        
                        <div class="total-revenue">
                            <div class="total-amount">${formatCurrency(revenue_analysis.total_monthly)}</div>
                            <div class="stat-label">월 총 예상 수익</div>
                            <p style="margin-top: 1rem; color: var(--text-secondary);">
                                연간 예상 수익: <strong>${formatCurrency(revenue_analysis.annual_estimate)}</strong> | 
                                채널 등급: <strong>${revenue_analysis.tier}</strong>
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Videos -->
                ${videos.length > 0 ? `
                <div class="analysis-card slide-up" style="animation-delay: 0.2s;">
                    <h2 class="card-title">
                        <i class="fas fa-video"></i>
                        최근 동영상 (${videos.length}개)
                    </h2>
                    <div class="video-grid">
                        ${videos.map(video => `
                            <div class="video-card">
                                <div class="video-thumbnail">
                                    <img src="${video.thumbnail}" alt="${video.title}" loading="lazy">
                                    <div class="video-views">${formatNumber(video.view_count)} 회</div>
                                </div>
                                <div class="video-content">
                                    <div class="video-title">${video.title}</div>
                                    <div class="video-stats">
                                        <div class="video-stat">
                                            <i class="fas fa-thumbs-up"></i>
                                            <span>${formatNumber(video.like_count)}</span>
                                        </div>
                                        <div class="video-stat">
                                            <i class="fas fa-comment"></i>
                                            <span>${formatNumber(video.comment_count)}</span>
                                        </div>
                                        <div class="video-stat">
                                            <i class="fas fa-clock"></i>
                                            <span>${new Date(video.published_date).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>` : ''}
            `;
            
            document.getElementById('resultsContent').innerHTML = resultsHTML;
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadTheme();
        });
    </script>
</body>
</html>
    '''

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        channel_url = data.get('channel_url', '')
        
        if not channel_url:
            return jsonify({'error': '채널 URL을 입력해주세요'}), 400
        
        analyzer = ServiceYouTubeAnalyzer(API_KEY)
        result = analyzer.analyze_complete(channel_url, max_videos=20)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Analytics Pro - 프리미엄 서비스")
    print("=" * 60)
    print("주소: http://localhost:8080")
    print("사용자 중심의 현대적인 UI/UX")
    print("실시간 채널 분석 및 수익 예측")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)