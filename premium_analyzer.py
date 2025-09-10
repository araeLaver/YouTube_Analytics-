# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
from datetime import datetime, timedelta
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from advanced_features import trend_analyzer, content_engine, competitor_analyzer, sentiment_analyzer

app = Flask(__name__)

API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

class PremiumYouTubeAnalyzer:
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
    
    def get_videos(self, channel_id, max_results=50):
        """채널의 동영상들 가져오기"""
        try:
            # 채널의 업로드 플레이리스트 ID 가져오기
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                # 플레이리스트의 동영상들 가져오기
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                ).execute()
                
                video_ids = [item['snippet']['resourceId']['videoId'] 
                           for item in playlist_response['items']]
                
                # 동영상 상세 정보 가져오기
                videos_response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids)
                ).execute()
                
                for video in videos_response['items']:
                    videos.append({
                        'video_id': video['id'],
                        'title': video['snippet']['title'],
                        'published_at': video['snippet']['publishedAt'],
                        'view_count': int(video['statistics'].get('viewCount', 0)),
                        'like_count': int(video['statistics'].get('likeCount', 0)),
                        'comment_count': int(video['statistics'].get('commentCount', 0)),
                        'duration': video['contentDetails']['duration']
                    })
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return videos
        except Exception as e:
            print(f"동영상 가져오기 오류: {e}")
            return []
    
    def analyze_channel(self, channel_id):
        """채널 종합 분석"""
        return self.analyze_channel_with_count(channel_id, 100)
    
    def analyze_channel_with_count(self, channel_id, max_videos):
        """채널 종합 분석 (동영상 수 지정)"""
        channel_info = self.get_channel_info(channel_id)
        if not channel_info:
            return None
        
        videos = self.get_videos(channel_id, max_videos)
        
        # 기본 통계
        stats = channel_info['statistics']
        subscriber_count = int(stats.get('subscriberCount', 0))
        total_views = int(stats.get('viewCount', 0))
        video_count = int(stats.get('videoCount', 0))
        
        # 동영상 분석
        if videos:
            avg_views = sum(v['view_count'] for v in videos) / len(videos)
            avg_likes = sum(v['like_count'] for v in videos) / len(videos)
            avg_comments = sum(v['comment_count'] for v in videos) / len(videos)
            
            # 최근 30일 동영상
            recent_videos = [v for v in videos if 
                           (datetime.now() - datetime.strptime(v['published_at'][:19], '%Y-%m-%dT%H:%M:%S')).days <= 30]
            
            recent_avg_views = sum(v['view_count'] for v in recent_videos) / len(recent_videos) if recent_videos else 0
        else:
            avg_views = avg_likes = avg_comments = recent_avg_views = 0
            recent_videos = []
        
        # 수익성 추정
        estimated_monthly_revenue = self.estimate_revenue(subscriber_count, avg_views, recent_avg_views)
        
        return {
            'channel_info': channel_info,
            'videos': videos,
            'analysis': {
                'subscriber_count': subscriber_count,
                'total_views': total_views,
                'video_count': video_count,
                'avg_views_per_video': avg_views,
                'avg_likes_per_video': avg_likes,
                'avg_comments_per_video': avg_comments,
                'recent_videos_count': len(recent_videos),
                'recent_avg_views': recent_avg_views,
                'estimated_monthly_revenue': estimated_monthly_revenue,
                'engagement_rate': (avg_likes + avg_comments) / max(avg_views, 1) * 100
            }
        }
    
    def estimate_revenue(self, subscribers, avg_views, recent_avg_views):
        """수익 추정"""
        # YouTube RPM (Revenue per Mille) 평균값들
        base_rpm = 2.5  # 기본 RPM (달러)
        
        # 구독자 기반 보정
        if subscribers > 1000000:
            rpm_multiplier = 1.5
        elif subscribers > 100000:
            rpm_multiplier = 1.3
        elif subscribers > 10000:
            rpm_multiplier = 1.1
        else:
            rpm_multiplier = 0.8
        
        adjusted_rpm = base_rpm * rpm_multiplier
        
        # 최근 성과 기반 월 예상 수익
        monthly_views = recent_avg_views * 30 if recent_avg_views > 0 else avg_views * 30
        monthly_revenue = (monthly_views / 1000) * adjusted_rpm
        
        # 추가 수익원 추정 (스폰서십, 제품 판매 등)
        if subscribers > 100000:
            additional_revenue = monthly_revenue * 0.5
        elif subscribers > 50000:
            additional_revenue = monthly_revenue * 0.3
        else:
            additional_revenue = monthly_revenue * 0.1
        
        total_monthly_revenue = monthly_revenue + additional_revenue
        
        return {
            'ad_revenue': monthly_revenue,
            'additional_revenue': additional_revenue,
            'total_monthly': total_monthly_revenue,
            'annual_estimate': total_monthly_revenue * 12
        }

analyzer = PremiumYouTubeAnalyzer(API_KEY)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Analytics Studio Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --accent: #06b6d4;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --background: #0f0f23;
            --surface: #1a1a2e;
            --surface-light: #16213e;
            --text-primary: #ffffff;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border: #334155;
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.15);
            --shadow-lg: 0 8px 25px rgba(0, 0, 0, 0.2);
            --shadow-xl: 0 20px 40px rgba(0, 0, 0, 0.25);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--background);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        /* Animated Background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.03;
            overflow: hidden;
        }
        
        .bg-animation::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 200%;
            height: 200%;
            background: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><pattern id='grid' width='10' height='10' patternUnits='userSpaceOnUse'><path d='M 10 0 L 0 0 0 10' fill='none' stroke='%23ffffff' stroke-width='0.5'/></pattern></defs><rect width='100' height='100' fill='url(%23grid)'/></svg>");
            animation: drift 60s linear infinite;
        }
        
        @keyframes drift {
            0% { transform: translate(0, 0); }
            100% { transform: translate(-50px, -50px); }
        }
        
        /* Header */
        .header {
            background: var(--gradient-1);
            padding: 4rem 2rem;
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
            background: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 320'><path fill='rgba(255,255,255,0.1)' fill-opacity='1' d='M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,112C672,96,768,96,864,112C960,128,1056,160,1152,160C1248,160,1344,128,1392,112L1440,96L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z'></path></svg>");
            background-size: 100% 100%;
            animation: wave 20s ease-in-out infinite;
        }
        
        @keyframes wave {
            0%, 100% { transform: translateX(0); }
            50% { transform: translateX(-50px); }
        }
        
        .header-content {
            position: relative;
            z-index: 2;
        }
        
        .header h1 {
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 900;
            margin-bottom: 1rem;
            background: linear-gradient(45deg, #ffffff, #e2e8f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 4px 8px rgba(0,0,0,0.3);
            letter-spacing: -0.02em;
        }
        
        .header .subtitle {
            font-size: 1.25rem;
            opacity: 0.9;
            font-weight: 400;
            max-width: 600px;
            margin: 0 auto 2rem;
            color: #ffffff;
        }
        
        .header-stats {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
            padding: 1rem;
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: 800;
            display: block;
            color: #ffffff !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: #ffffff !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        }
        
        /* Main Container */
        .main-container {
            max-width: 1400px;
            margin: -2rem auto 4rem;
            padding: 0 2rem;
            position: relative;
        }
        
        /* Search Section */
        .search-section {
            background: var(--surface);
            border-radius: 24px;
            padding: 3rem;
            box-shadow: var(--shadow-xl);
            margin-bottom: 3rem;
            border: 1px solid var(--border);
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        
        .search-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: var(--gradient-3);
        }
        
        .search-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .search-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: var(--gradient-3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .search-subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .search-form {
            display: grid;
            grid-template-columns: 2fr 1fr auto;
            gap: 1rem;
            align-items: end;
        }
        
        @media (max-width: 768px) {
            .search-form {
                grid-template-columns: 1fr;
            }
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-label {
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .form-input {
            padding: 1rem 1.25rem;
            background: var(--surface-light);
            border: 2px solid transparent;
            border-radius: 16px;
            font-size: 1rem;
            color: var(--text-primary);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-family: inherit;
            box-shadow: var(--shadow-sm);
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1), var(--shadow-md);
            transform: translateY(-1px);
        }
        
        .form-input::placeholder {
            color: var(--text-muted);
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 1rem 2rem;
            font-weight: 600;
            border-radius: 16px;
            text-decoration: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: none;
            cursor: pointer;
            font-family: inherit;
            font-size: 1rem;
            position: relative;
            overflow: hidden;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            transform: translateX(-100%);
            transition: transform 0.6s;
        }
        
        .btn:hover::before {
            transform: translateX(100%);
        }
        
        .btn-primary {
            background: var(--gradient-1);
            color: white;
            box-shadow: var(--shadow-md);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .btn-primary:active {
            transform: translateY(0);
        }
        
        /* Loading Animation */
        .loading {
            display: none;
            text-align: center;
            padding: 3rem;
        }
        
        .loading.active {
            display: block;
        }
        
        .loading-spinner {
            width: 60px;
            height: 60px;
            border: 4px solid var(--border);
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Results Section */
        .results {
            display: none;
        }
        
        .results.active {
            display: block;
        }
        
        .results-header {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .channel-info {
            background: var(--surface);
            border-radius: 24px;
            padding: 3rem;
            margin-bottom: 3rem;
            box-shadow: var(--shadow-xl);
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }
        
        .channel-header {
            display: flex;
            align-items: center;
            gap: 2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        
        .channel-avatar {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            border: 4px solid var(--border);
            box-shadow: var(--shadow-md);
        }
        
        .channel-details h2 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .channel-details p {
            color: var(--text-secondary);
            font-size: 1.1rem;
            line-height: 1.6;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin: 3rem 0;
        }
        
        .stat-card {
            background: var(--surface-light);
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-1);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover::before {
            transform: scaleX(1);
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }
        
        .stat-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }
        
        .stat-title {
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Chart Container */
        .chart-container {
            background: var(--surface);
            border-radius: 24px;
            padding: 2rem;
            margin: 2rem 0;
            box-shadow: var(--shadow-xl);
            border: 1px solid var(--border);
        }
        
        .chart-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        /* Revenue Section */
        .revenue-section {
            background: var(--gradient-2);
            border-radius: 24px;
            padding: 3rem;
            margin: 3rem 0;
            text-align: center;
            color: white;
            position: relative;
            overflow: hidden;
        }
        
        .revenue-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 50% 50%, rgba(255,255,255,0.1) 0%, transparent 70%);
        }
        
        .revenue-content {
            position: relative;
            z-index: 2;
        }
        
        .revenue-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        
        .revenue-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .revenue-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 1.5rem;
            border-radius: 16px;
            backdrop-filter: blur(10px);
        }
        
        .revenue-amount {
            font-size: 1.75rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        
        .revenue-label {
            font-size: 0.875rem;
            opacity: 0.9;
        }
        
        /* Footer */
        .footer {
            background: var(--surface);
            padding: 3rem 2rem;
            text-align: center;
            border-top: 1px solid var(--border);
            margin-top: 4rem;
        }
        
        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .footer h3 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            background: var(--gradient-3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .footer p {
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }
        
        .footer-links {
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        }
        
        .footer-link {
            color: var(--text-secondary);
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        .footer-link:hover {
            color: var(--primary);
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .header {
                padding: 3rem 1rem;
            }
            
            .main-container {
                padding: 0 1rem;
            }
            
            .search-section,
            .channel-info {
                padding: 2rem;
                border-radius: 16px;
            }
            
            .channel-header {
                flex-direction: column;
                text-align: center;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .header-stats {
                gap: 1rem;
            }
        }
        
        /* Animations */
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        .slide-up {
            animation: slideUp 0.6s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Video Tables */
        .video-section {
            background: var(--surface);
            border-radius: 24px;
            padding: 2rem;
            margin: 2rem 0;
            box-shadow: var(--shadow-xl);
            border: 1px solid var(--border);
        }
        
        .video-section h3 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .video-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        .video-table th,
        .video-table td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        
        .video-table th {
            background: var(--surface-light);
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .video-table tr:hover {
            background: var(--surface-light);
            transform: scale(1.01);
            transition: all 0.2s ease;
        }
        
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .pagination-info {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        .pagination-controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
            margin-top: 1.5rem;
            padding: 1rem;
        }
        
        .page-btn {
            padding: 0.5rem 0.75rem;
            border: 2px solid #007bff;
            background: #007bff;
            color: white;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.3s ease;
            font-size: 0.9rem;
            font-weight: 500;
            min-width: 40px;
            text-align: center;
        }
        
        .page-btn:hover:not(:disabled) {
            background: #0056b3;
            border-color: #0056b3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
        }
        
        .page-btn.active {
            background: #28a745;
            color: white;
            border-color: #28a745;
            box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
        }
        
        .page-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            background: #dc3545;
            color: white;
            border-color: #dc3545;
        }
        
        .page-info {
            margin: 0 1rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        .video-thumbnail {
            width: 120px;
            height: 68px;
            border-radius: 8px;
            object-fit: cover;
            box-shadow: var(--shadow-sm);
        }
        
        .video-title {
            font-weight: 500;
            color: var(--text-primary);
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .video-title:hover {
            color: var(--primary);
            cursor: pointer;
        }
        
        .video-stats {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        
        .stat-number {
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .video-date {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .video-modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(5px);
        }
        
        .modal-content {
            background-color: var(--surface);
            margin: 5% auto;
            padding: 2rem;
            border-radius: 20px;
            width: 90%;
            max-width: 800px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-xl);
        }
        
        .close-modal {
            color: var(--text-secondary);
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            transition: color 0.3s ease;
        }
        
        .close-modal:hover {
            color: var(--primary);
        }
        
        .tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border);
        }
        
        .tab {
            padding: 0.75rem 1.5rem;
            background: none;
            border: none;
            color: var(--text-secondary);
            font-weight: 500;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Small Buttons */
        .btn-small {
            padding: 0.4rem 0.8rem;
            font-size: 0.75rem;
            font-weight: 500;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }
        
        .btn-analyze {
            background: var(--primary);
            color: white;
        }
        
        .btn-analyze:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
        }
        
        .btn-script {
            background: var(--accent);
            color: white;
        }
        
        .btn-script:hover {
            background: #0891b2;
            transform: translateY(-1px);
        }
        
        .btn-details {
            background: var(--secondary);
            color: white;
        }
        
        .btn-details:hover {
            background: #7c3aed;
            transform: translateY(-1px);
        }
        
        /* Loading for individual actions */
        .btn-loading {
            opacity: 0.7;
            pointer-events: none;
        }
        
        .btn-loading::after {
            content: '';
            width: 12px;
            height: 12px;
            border: 2px solid transparent;
            border-top: 2px solid currentColor;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 0.3rem;
        }
        
        /* Script Modal */
        .script-modal {
            display: none;
            position: fixed;
            z-index: 1001;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(5px);
        }
        
        .script-modal-content {
            background-color: var(--surface);
            margin: 2% auto;
            padding: 2rem;
            border-radius: 20px;
            width: 95%;
            max-width: 1000px;
            max-height: 90vh;
            overflow-y: auto;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-xl);
        }
        
        .script-text {
            background: var(--surface-light);
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            line-height: 1.8;
            color: var(--text-primary);
            border-left: 4px solid var(--primary);
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--background);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary);
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <header class="header">
        <div class="header-content">
            <h1>YouTube Analytics Studio Pro</h1>
            <p class="subtitle">AI 기반 채널 성과 분석 및 수익성 예측 플랫폼</p>
            
            <div class="header-stats">
                <div class="stat-item">
                    <span class="stat-number">AI</span>
                    <span class="stat-label">분석 엔진</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">실시간</span>
                    <span class="stat-label">데이터 수집</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">무료</span>
                    <span class="stat-label">분석 도구</span>
                </div>
            </div>
        </div>
    </header>
    
    <main class="main-container">
        <section class="search-section fade-in">
            <div class="search-header">
                <h2 class="search-title">채널 분석 시작하기</h2>
                <p class="search-subtitle">YouTube 채널 URL 또는 채널명을 입력하여 상세한 성과 분석을 받아보세요</p>
            </div>
            
            <form class="search-form" onsubmit="analyzeChannel(event)">
                <div class="form-group">
                    <label class="form-label">채널 정보</label>
                    <input 
                        type="text" 
                        class="form-input" 
                        id="channelInput" 
                        placeholder="예: https://youtube.com/@channel 또는 채널명"
                        required
                    >
                </div>
                <div class="form-group">
                    <label class="form-label">분석할 동영상 수</label>
                    <select class="form-input" id="videoCount">
                        <option value="20">20개</option>
                        <option value="50" selected>50개</option>
                        <option value="100">100개</option>
                        <option value="200">200개</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-chart-line"></i>
                    분석 시작
                </button>
            </form>
        </section>
        
        <div class="loading" id="loading">
            <div class="loading-spinner"></div>
            <p>채널을 분석하는 중입니다...</p>
            <p style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.5rem;">
                최신 데이터를 수집하고 AI 알고리즘으로 분석하고 있습니다
            </p>
        </div>
        
        <div class="results" id="results">
            <!-- 결과가 여기에 동적으로 삽입됩니다 -->
        </div>
    </main>
    
    <!-- Video Detail Modal -->
    <div id="videoModal" class="video-modal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeVideoModal()">&times;</span>
            <div id="modalContent">
                <!-- 동영상 상세 정보가 여기에 표시됩니다 -->
            </div>
        </div>
    </div>
    
    <!-- Script Modal -->
    <div id="scriptModal" class="script-modal">
        <div class="script-modal-content">
            <span class="close-modal" onclick="closeScriptModal()">&times;</span>
            <div id="scriptModalContent">
                <!-- 스크립트 내용이 여기에 표시됩니다 -->
            </div>
        </div>
    </div>
    
    <footer class="footer">
        <div class="footer-content">
            <h3>YouTube Analytics Studio Pro</h3>
            <p>전문적인 YouTube 채널 분석으로 크리에이터의 성공을 지원합니다</p>
        </div>
    </footer>
    
    <script>
        async function analyzeChannel(event) {
            event.preventDefault();
            
            const channelInput = document.getElementById('channelInput').value.trim();
            const videoCount = document.getElementById('videoCount').value;
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            if (!channelInput) {
                alert('채널 정보를 입력해주세요.');
                return;
            }
            
            // 로딩 표시
            results.classList.remove('active');
            loading.classList.add('active');
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        channel_query: channelInput,
                        max_videos: parseInt(videoCount)
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                displayResults(data);
                
            } catch (error) {
                console.error('Error:', error);
                results.innerHTML = `
                    <div style="text-align: center; padding: 3rem; background: var(--surface); border-radius: 24px; border: 1px solid var(--border);">
                        <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: var(--error); margin-bottom: 1rem;"></i>
                        <h3>분석 중 오류가 발생했습니다</h3>
                        <p style="color: var(--text-secondary); margin-top: 0.5rem;">${error.message}</p>
                        <button class="btn btn-primary" onclick="location.reload()" style="margin-top: 1rem;">
                            다시 시도
                        </button>
                    </div>
                `;
                results.classList.add('active');
            } finally {
                loading.classList.remove('active');
            }
        }
        
        function displayResults(data) {
            const results = document.getElementById('results');
            const channelInfo = data.channel_info;
            const analysis = data.analysis;
            const videos = data.videos;
            const videoCount = document.getElementById('videoCount').value;
            
            // 숫자 포맷팅 함수
            function formatNumber(num) {
                return new Intl.NumberFormat('ko-KR').format(num);
            }
            
            // 간단한 단위 표시 (차트용)
            function formatNumberShort(num) {
                if (num >= 1000000) {
                    return (num / 1000000).toFixed(1) + 'M';
                } else if (num >= 1000) {
                    return (num / 1000).toFixed(1) + 'K';
                }
                return num.toLocaleString();
            }
            
            // 전역 스코프에서 접근 가능하도록 설정
            window.formatNumber = formatNumber;
            window.formatNumberShort = formatNumberShort;
            
            function formatCurrency(amount) {
                return new Intl.NumberFormat('ko-KR', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                }).format(amount);
            }
            
            results.innerHTML = `
                <div class="results-header slide-up">
                    <h2>분석 결과</h2>
                    <p style="color: var(--text-secondary); font-size: 1.1rem;">
                        ${channelInfo.snippet.title}의 상세한 성과 분석 리포트
                    </p>
                </div>
                
                <div class="channel-info slide-up">
                    <div class="channel-header">
                        <img 
                            src="${channelInfo.snippet.thumbnails.high.url}" 
                            alt="${channelInfo.snippet.title}" 
                            class="channel-avatar"
                        >
                        <div class="channel-details">
                            <h2>${channelInfo.snippet.title}</h2>
                            <p>${channelInfo.snippet.description.substring(0, 200)}...</p>
                            <p style="margin-top: 1rem; color: var(--text-muted); font-size: 0.875rem;">
                                <i class="fas fa-calendar"></i>
                                개설일: ${new Date(channelInfo.snippet.publishedAt).toLocaleDateString('ko-KR')}
                            </p>
                        </div>
                    </div>
                </div>
                
                <div class="stats-grid slide-up">
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-users"></i></div>
                        <div class="stat-value">${formatNumber(analysis.subscriber_count)}</div>
                        <div class="stat-title">구독자</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-eye"></i></div>
                        <div class="stat-value">${formatNumber(analysis.total_views)}</div>
                        <div class="stat-title">총 조회수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-video"></i></div>
                        <div class="stat-value">${formatNumber(analysis.video_count)}</div>
                        <div class="stat-title">동영상 수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-chart-line"></i></div>
                        <div class="stat-value">${formatNumber(Math.round(analysis.avg_views_per_video))}</div>
                        <div class="stat-title">평균 조회수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-thumbs-up"></i></div>
                        <div class="stat-value">${formatNumber(Math.round(analysis.avg_likes_per_video))}</div>
                        <div class="stat-title">평균 좋아요</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-heart"></i></div>
                        <div class="stat-value">${analysis.engagement_rate.toFixed(2)}%</div>
                        <div class="stat-title">참여도</div>
                    </div>
                </div>
                
                <div class="revenue-section slide-up">
                    <div class="revenue-content">
                        <h3 class="revenue-title">💰 예상 수익 분석</h3>
                        <p style="opacity: 0.9; margin-bottom: 2rem;">
                            AI 알고리즘 기반 수익성 분석 결과
                        </p>
                        
                        <div class="revenue-grid">
                            <div class="revenue-item">
                                <div class="revenue-amount">${formatCurrency(analysis.estimated_monthly_revenue.ad_revenue)}</div>
                                <div class="revenue-label">월 광고 수익</div>
                            </div>
                            <div class="revenue-item">
                                <div class="revenue-amount">${formatCurrency(analysis.estimated_monthly_revenue.additional_revenue)}</div>
                                <div class="revenue-label">월 추가 수익</div>
                            </div>
                            <div class="revenue-item">
                                <div class="revenue-amount">${formatCurrency(analysis.estimated_monthly_revenue.total_monthly)}</div>
                                <div class="revenue-label">월 총 예상 수익</div>
                            </div>
                            <div class="revenue-item">
                                <div class="revenue-amount">${formatCurrency(analysis.estimated_monthly_revenue.annual_estimate)}</div>
                                <div class="revenue-label">연간 예상 수익</div>
                            </div>
                        </div>
                        
                        <p style="font-size: 0.875rem; opacity: 0.8; margin-top: 1.5rem;">
                            * 예상 수익은 업계 평균 RPM, 구독자 수, 조회수 등을 종합하여 산출된 추정값입니다.
                        </p>
                    </div>
                </div>
                
                <div class="chart-container slide-up">
                    <h3 class="chart-title">📊 최근 영상 성과 트렌드</h3>
                    <canvas id="performanceChart" width="400" height="200"></canvas>
                </div>
                
                <div class="video-section slide-up">
                    <div class="tabs">
                        <button class="tab active" onclick="switchTab('popular')">🔥 인기 동영상</button>
                        <button class="tab" onclick="switchTab('recent')">⏰ 최신 동영상</button>
                    </div>
                    
                    <div id="popular-content" class="tab-content active">
                        <div class="table-header">
                            <h3><i class="fas fa-fire"></i> 인기 동영상 (${videos.length}개)</h3>
                            <div class="pagination-info">
                                <span id="popular-page-info">페이지 1</span>
                            </div>
                        </div>
                        <table class="video-table">
                            <thead>
                                <tr>
                                    <th>썸네일</th>
                                    <th>제목</th>
                                    <th>조회수</th>
                                    <th>좋아요</th>
                                    <th>댓글</th>
                                    <th>게시일</th>
                                </tr>
                            </thead>
                            <tbody id="popular-table-body">
                                <!-- 페이징 처리된 내용이 여기에 표시됩니다 -->
                            </tbody>
                        </table>
                        <div class="pagination-controls" id="popular-pagination">
                            <!-- 페이징 버튼들이 여기에 표시됩니다 -->
                        </div>
                    </div>
                    
                    <div id="recent-content" class="tab-content">
                        <div class="table-header">
                            <h3><i class="fas fa-clock"></i> 최신 동영상 (${videos.length}개)</h3>
                            <div class="pagination-info">
                                <span id="recent-page-info">페이지 1</span>
                            </div>
                        </div>
                        <table class="video-table">
                            <thead>
                                <tr>
                                    <th>썸네일</th>
                                    <th>제목</th>
                                    <th>조회수</th>
                                    <th>좋아요</th>
                                    <th>댓글</th>
                                    <th>게시일</th>
                                </tr>
                            </thead>
                            <tbody id="recent-table-body">
                                <!-- 페이징 처리된 내용이 여기에 표시됩니다 -->
                            </tbody>
                        </table>
                        <div class="pagination-controls" id="recent-pagination">
                            <!-- 페이징 버튼들이 여기에 표시됩니다 -->
                        </div>
                    </div>
                </div>
            `;
            
            // 차트 생성
            createPerformanceChart(videos.slice(0, 10));
            
            // Store videos data globally for modal
            currentVideos = videos;
            
            // Initialize pagination
            initializePagination();
            
            results.classList.add('active');
        }
        
        function createPerformanceChart(videos) {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            
            // 데이터 준비
            const labels = videos.map(v => v.title.length > 20 ? v.title.substring(0, 20) + '...' : v.title);
            const viewData = videos.map(v => v.view_count);
            const likeData = videos.map(v => v.like_count);
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '조회수',
                        data: viewData,
                        backgroundColor: 'rgba(99, 102, 241, 0.8)',
                        borderColor: 'rgba(99, 102, 241, 1)',
                        borderWidth: 2,
                        borderRadius: 8,
                        yAxisID: 'y'
                    }, {
                        label: '좋아요',
                        data: likeData,
                        type: 'line',
                        borderColor: 'rgba(139, 92, 246, 1)',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    interaction: {
                        intersect: false,
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: '#94a3b8',
                                font: {
                                    size: 12
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: '#64748b',
                                font: {
                                    size: 10
                                }
                            },
                            grid: {
                                color: '#334155'
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            ticks: {
                                color: '#64748b'
                            },
                            grid: {
                                color: '#334155'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            ticks: {
                                color: '#64748b'
                            },
                            grid: {
                                drawOnChartArea: false,
                                color: '#334155'
                            },
                        }
                    }
                }
            });
        }
        
        // 페이지 로드 시 애니메이션
        document.addEventListener('DOMContentLoaded', function() {
            console.log('YouTube Analytics Studio Pro 시작됨');
            
            // Intersection Observer for animations
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.animationDelay = `${Math.random() * 0.3}s`;
                        entry.target.classList.add('fade-in');
                    }
                });
            }, { threshold: 0.1 });
            
            // 모든 애니메이션 대상 요소 관찰
            document.querySelectorAll('.slide-up').forEach(el => {
                observer.observe(el);
            });
        });
        
        // Tab switching function
        function switchTab(tabName) {
            // Remove active class from all tabs and contents
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Add active class to selected tab and content
            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }
        
        // Pagination variables
        let popularCurrentPage = 1;
        let recentCurrentPage = 1;
        const videosPerPage = 10;
        
        // Initialize pagination
        function initializePagination() {
            if (currentVideos && currentVideos.length > 0) {
                setupPopularPagination();
                setupRecentPagination();
            }
        }
        
        // Setup popular videos pagination
        function setupPopularPagination() {
            const sortedVideos = [...currentVideos].sort((a, b) => b.view_count - a.view_count);
            const totalPages = Math.ceil(sortedVideos.length / videosPerPage);
            
            displayPopularVideos(sortedVideos, 1);
            createPaginationControls('popular', totalPages, 1);
        }
        
        // Setup recent videos pagination
        function setupRecentPagination() {
            const sortedVideos = [...currentVideos].sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
            const totalPages = Math.ceil(sortedVideos.length / videosPerPage);
            
            displayRecentVideos(sortedVideos, 1);
            createPaginationControls('recent', totalPages, 1);
        }
        
        // Display popular videos for a specific page
        function displayPopularVideos(videos, page) {
            const startIndex = (page - 1) * videosPerPage;
            const endIndex = startIndex + videosPerPage;
            const pageVideos = videos.slice(startIndex, endIndex);
            
            const tbody = document.getElementById('popular-table-body');
            tbody.innerHTML = pageVideos.map(video => `
                <tr>
                    <td>
                        <img src="https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg" 
                             alt="썸네일" class="video-thumbnail"
                             onclick="window.open('https://youtube.com/watch?v=${video.video_id}', '_blank')"
                             style="cursor: pointer;">
                    </td>
                    <td>
                        <div class="video-title" title="${video.title}"
                             onclick="window.open('https://youtube.com/watch?v=${video.video_id}', '_blank')"
                             style="cursor: pointer;">
                            ${video.title}
                        </div>
                        <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                            <button class="btn-small btn-analyze" onclick="analyzeVideo('${video.video_id}', event);">
                                <i class="fas fa-chart-bar"></i> 분석
                            </button>
                            <button class="btn-small btn-script" onclick="getVideoScript('${video.video_id}', event);">
                                <i class="fas fa-file-text"></i> 스크립트
                            </button>
                            <button class="btn-small btn-details" onclick="event.stopPropagation(); showVideoDetails('${video.video_id}');">
                                <i class="fas fa-info-circle"></i> 상세
                            </button>
                        </div>
                    </td>
                    <td>
                        <div class="video-stats">
                            <span class="stat-number">${formatNumber(video.view_count)}</span>
                            <span class="stat-label">조회수</span>
                        </div>
                    </td>
                    <td>
                        <div class="video-stats">
                            <span class="stat-number">${formatNumber(video.like_count)}</span>
                            <span class="stat-label">좋아요</span>
                        </div>
                    </td>
                    <td>
                        <div class="video-stats">
                            <span class="stat-number">${formatNumber(video.comment_count)}</span>
                            <span class="stat-label">댓글</span>
                        </div>
                    </td>
                    <td>
                        <div class="video-date">
                            ${new Date(video.published_at).toLocaleDateString('ko-KR')}
                        </div>
                    </td>
                </tr>
            `).join('');
            
            // Update page info
            document.getElementById('popular-page-info').textContent = 
                `페이지 ${page} / ${Math.ceil(videos.length / videosPerPage)} (${videos.length}개 영상 중 ${startIndex + 1}-${Math.min(endIndex, videos.length)})`;
        }
        
        // Display recent videos for a specific page
        function displayRecentVideos(videos, page) {
            const startIndex = (page - 1) * videosPerPage;
            const endIndex = startIndex + videosPerPage;
            const pageVideos = videos.slice(startIndex, endIndex);
            
            const tbody = document.getElementById('recent-table-body');
            tbody.innerHTML = pageVideos.map(video => `
                <tr>
                    <td>
                        <img src="https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg" 
                             alt="썸네일" class="video-thumbnail"
                             onclick="window.open('https://youtube.com/watch?v=${video.video_id}', '_blank')"
                             style="cursor: pointer;">
                    </td>
                    <td>
                        <div class="video-title" title="${video.title}"
                             onclick="window.open('https://youtube.com/watch?v=${video.video_id}', '_blank')"
                             style="cursor: pointer;">
                            ${video.title}
                        </div>
                        <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                            <button class="btn-small btn-analyze" onclick="analyzeVideo('${video.video_id}', event);">
                                <i class="fas fa-chart-bar"></i> 분석
                            </button>
                            <button class="btn-small btn-script" onclick="getVideoScript('${video.video_id}', event);">
                                <i class="fas fa-file-text"></i> 스크립트
                            </button>
                            <button class="btn-small btn-details" onclick="event.stopPropagation(); showVideoDetails('${video.video_id}');">
                                <i class="fas fa-info-circle"></i> 상세
                            </button>
                        </div>
                    </td>
                    <td>
                        <div class="video-stats">
                            <span class="stat-number">${formatNumber(video.view_count)}</span>
                            <span class="stat-label">조회수</span>
                        </div>
                    </td>
                    <td>
                        <div class="video-stats">
                            <span class="stat-number">${formatNumber(video.like_count)}</span>
                            <span class="stat-label">좋아요</span>
                        </div>
                    </td>
                    <td>
                        <div class="video-stats">
                            <span class="stat-number">${formatNumber(video.comment_count)}</span>
                            <span class="stat-label">댓글</span>
                        </div>
                    </td>
                    <td>
                        <div class="video-date">
                            ${new Date(video.published_at).toLocaleDateString('ko-KR')}
                        </div>
                    </td>
                </tr>
            `).join('');
            
            // Update page info
            document.getElementById('recent-page-info').textContent = 
                `페이지 ${page} / ${Math.ceil(videos.length / videosPerPage)} (${videos.length}개 영상 중 ${startIndex + 1}-${Math.min(endIndex, videos.length)})`;
        }
        
        // Create pagination controls
        function createPaginationControls(type, totalPages, currentPage) {
            const container = document.getElementById(`${type}-pagination`);
            
            if (totalPages <= 1) {
                container.innerHTML = '';
                return;
            }
            
            let html = '';
            
            // Previous button
            html += `<button class="page-btn" onclick="changePage('${type}', ${currentPage - 1})" 
                     ${currentPage <= 1 ? 'disabled' : ''}>‹ 이전</button>`;
            
            // Page numbers
            const maxVisiblePages = 5;
            let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
            let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
            
            if (endPage - startPage + 1 < maxVisiblePages) {
                startPage = Math.max(1, endPage - maxVisiblePages + 1);
            }
            
            if (startPage > 1) {
                html += `<button class="page-btn" onclick="changePage('${type}', 1)">1</button>`;
                if (startPage > 2) {
                    html += `<span class="page-info">...</span>`;
                }
            }
            
            for (let i = startPage; i <= endPage; i++) {
                html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" 
                         onclick="changePage('${type}', ${i})">${i}</button>`;
            }
            
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    html += `<span class="page-info">...</span>`;
                }
                html += `<button class="page-btn" onclick="changePage('${type}', ${totalPages})">${totalPages}</button>`;
            }
            
            // Next button
            html += `<button class="page-btn" onclick="changePage('${type}', ${currentPage + 1})" 
                     ${currentPage >= totalPages ? 'disabled' : ''}>다음 ›</button>`;
            
            container.innerHTML = html;
        }
        
        // Change page
        function changePage(type, page) {
            if (type === 'popular') {
                popularCurrentPage = page;
                const sortedVideos = [...currentVideos].sort((a, b) => b.view_count - a.view_count);
                const totalPages = Math.ceil(sortedVideos.length / videosPerPage);
                displayPopularVideos(sortedVideos, page);
                createPaginationControls('popular', totalPages, page);
            } else if (type === 'recent') {
                recentCurrentPage = page;
                const sortedVideos = [...currentVideos].sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
                const totalPages = Math.ceil(sortedVideos.length / videosPerPage);
                displayRecentVideos(sortedVideos, page);
                createPaginationControls('recent', totalPages, page);
            }
        }
        
        // Global videos data for modal
        let currentVideos = [];
        
        // Show video details in modal
        function showVideoDetails(videoId) {
            const video = currentVideos.find(v => v.video_id === videoId);
            if (!video) return;
            
            const modalContent = document.getElementById('modalContent');
            modalContent.innerHTML = `
                <h2>${video.title}</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin: 2rem 0;">
                    <div>
                        <img src="https://img.youtube.com/vi/${video.video_id}/maxresdefault.jpg" 
                             alt="썸네일" style="width: 100%; border-radius: 12px;">
                    </div>
                    <div>
                        <div style="display: grid; gap: 1rem;">
                            <div>
                                <h4 style="color: var(--text-secondary); margin-bottom: 0.5rem;">📊 성과 지표</h4>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                    <div style="background: var(--surface-light); padding: 1rem; border-radius: 8px;">
                                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">
                                            ${formatNumber(video.view_count)}
                                        </div>
                                        <div style="color: var(--text-secondary); font-size: 0.875rem;">조회수</div>
                                    </div>
                                    <div style="background: var(--surface-light); padding: 1rem; border-radius: 8px;">
                                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--success);">
                                            ${formatNumber(video.like_count)}
                                        </div>
                                        <div style="color: var(--text-secondary); font-size: 0.875rem;">좋아요</div>
                                    </div>
                                    <div style="background: var(--surface-light); padding: 1rem; border-radius: 8px;">
                                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent);">
                                            ${formatNumber(video.comment_count)}
                                        </div>
                                        <div style="color: var(--text-secondary); font-size: 0.875rem;">댓글</div>
                                    </div>
                                    <div style="background: var(--surface-light); padding: 1rem; border-radius: 8px;">
                                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--warning);">
                                            ${((video.like_count / Math.max(video.view_count, 1)) * 100).toFixed(2)}%
                                        </div>
                                        <div style="color: var(--text-secondary); font-size: 0.875rem;">좋아요율</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div>
                                <h4 style="color: var(--text-secondary); margin-bottom: 0.5rem;">📅 게시 정보</h4>
                                <p style="color: var(--text-primary);">
                                    ${new Date(video.published_at).toLocaleDateString('ko-KR', {
                                        year: 'numeric',
                                        month: 'long',
                                        day: 'numeric',
                                        weekday: 'long'
                                    })}
                                </p>
                                <p style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 0.5rem;">
                                    ${Math.floor((new Date() - new Date(video.published_at)) / (1000 * 60 * 60 * 24))}일 전 게시
                                </p>
                            </div>
                        </div>
                        
                        <div style="margin-top: 2rem;">
                            <a href="https://youtube.com/watch?v=${video.video_id}" 
                               target="_blank" 
                               class="btn btn-primary" 
                               style="text-decoration: none; display: inline-flex;">
                                <i class="fab fa-youtube"></i>
                                YouTube에서 보기
                            </a>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('videoModal').style.display = 'block';
        }
        
        // Close video modal
        function closeVideoModal() {
            document.getElementById('videoModal').style.display = 'none';
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const videoModal = document.getElementById('videoModal');
            const scriptModal = document.getElementById('scriptModal');
            if (event.target === videoModal) {
                videoModal.style.display = 'none';
            }
            if (event.target === scriptModal) {
                scriptModal.style.display = 'none';
            }
        }
        
        // Individual video analysis
        async function analyzeVideo(videoId, event) {
            event.stopPropagation();
            const button = event.target.closest('.btn-analyze');
            const originalContent = button.innerHTML;
            
            // Show loading state
            button.classList.add('btn-loading');
            button.innerHTML = '<i class="fas fa-chart-bar"></i> 분석 중...';
            
            try {
                const response = await fetch('/analyze_video', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        video_id: videoId
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Show analysis in modal
                showVideoAnalysis(data);
                
            } catch (error) {
                console.error('Error:', error);
                alert('동영상 분석 중 오류가 발생했습니다: ' + error.message);
            } finally {
                // Reset button state
                button.classList.remove('btn-loading');
                button.innerHTML = originalContent;
            }
        }
        
        // Get video script/transcript
        async function getVideoScript(videoId, event) {
            console.log('getVideoScript called with videoId:', videoId);
            event.stopPropagation();
            const button = event.target.closest('.btn-script');
            const originalContent = button.innerHTML;
            
            // Show loading state
            button.classList.add('btn-loading');
            button.innerHTML = '<i class="fas fa-file-text"></i> 로딩...';
            
            try {
                console.log('Making request to /get_video_script');
                const response = await fetch('/get_video_script', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        video_id: videoId
                    })
                });
                
                console.log('Response received:', response.status);
                const data = await response.json();
                console.log('Response data:', data);
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Show script in modal
                console.log('Calling showVideoScript with data');
                showVideoScript(data);
                
            } catch (error) {
                console.error('Error in getVideoScript:', error);
                alert('스크립트 가져오기 중 오류가 발생했습니다: ' + error.message);
            } finally {
                // Reset button state
                button.classList.remove('btn-loading');
                button.innerHTML = originalContent;
            }
        }
        
        // Show video analysis modal
        function showVideoAnalysis(data) {
            const modalContent = document.getElementById('modalContent');
            modalContent.innerHTML = `
                <h2>${data.title}</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin: 2rem 0;">
                    <div>
                        <img src="https://img.youtube.com/vi/${data.video_id}/maxresdefault.jpg" 
                             alt="썸네일" style="width: 100%; border-radius: 12px;">
                    </div>
                    <div>
                        <h3 style="margin-bottom: 1rem; color: var(--primary);">📊 상세 분석 결과</h3>
                        <div style="display: grid; gap: 1rem;">
                            <div style="background: var(--surface-light); padding: 1rem; border-radius: 8px;">
                                <h4 style="color: var(--text-secondary); margin-bottom: 0.5rem;">성과 지표</h4>
                                <p><strong>조회수:</strong> ${formatNumber(data.view_count)}</p>
                                <p><strong>좋아요:</strong> ${formatNumber(data.like_count)}</p>
                                <p><strong>댓글:</strong> ${formatNumber(data.comment_count)}</p>
                                <p><strong>좋아요율:</strong> ${((data.like_count / Math.max(data.view_count, 1)) * 100).toFixed(2)}%</p>
                            </div>
                            
                            <div style="background: var(--surface-light); padding: 1rem; border-radius: 8px;">
                                <h4 style="color: var(--text-secondary); margin-bottom: 0.5rem;">예상 수익</h4>
                                <p><strong>RPM 기준 수익:</strong> $${(data.view_count / 1000 * 2.5).toFixed(0)}</p>
                                <p><strong>CPM 기준 수익:</strong> $${(data.view_count / 1000 * 1.5).toFixed(0)}</p>
                            </div>
                            
                            <div style="background: var(--surface-light); padding: 1rem; border-radius: 8px;">
                                <h4 style="color: var(--text-secondary); margin-bottom: 0.5rem;">참여도 분석</h4>
                                <p><strong>댓글 참여율:</strong> ${((data.comment_count / Math.max(data.view_count, 1)) * 100).toFixed(3)}%</p>
                                <p><strong>총 참여율:</strong> ${(((data.like_count + data.comment_count) / Math.max(data.view_count, 1)) * 100).toFixed(2)}%</p>
                            </div>
                        </div>
                        
                        <div style="margin-top: 2rem;">
                            <a href="https://youtube.com/watch?v=${data.video_id}" 
                               target="_blank" 
                               class="btn btn-primary" 
                               style="text-decoration: none; display: inline-flex;">
                                <i class="fab fa-youtube"></i>
                                YouTube에서 보기
                            </a>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('videoModal').style.display = 'block';
        }
        
        // Show video script modal
        function showVideoScript(data) {
            console.log('showVideoScript called with data:', data);
            const modalContent = document.getElementById('scriptModalContent');
            console.log('scriptModalContent element:', modalContent);
            modalContent.innerHTML = `
                <h2>${data.title}</h2>
                <div style="margin: 1rem 0;">
                    <p style="color: var(--text-secondary);">
                        ${data.script ? '자동 생성된 자막을 기반으로 한 스크립트입니다.' : '이 동영상에는 자막이 없습니다.'}
                    </p>
                </div>
                
                ${data.script ? `
                    <div class="script-text">
                        ${data.script.replace(/\\n/g, '<br>')}
                    </div>
                    
                    <div style="margin-top: 2rem;">
                        <h3 style="color: var(--primary); margin-bottom: 1rem;">📝 AI 요약</h3>
                        <div style="background: var(--surface-light); padding: 1.5rem; border-radius: 12px; border-left: 4px solid var(--accent);">
                            ${data.summary || '요약을 생성하는 중입니다...'}
                        </div>
                    </div>
                ` : `
                    <div style="text-align: center; padding: 3rem; color: var(--text-secondary);">
                        <i class="fas fa-exclamation-circle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                        <p>이 동영상에는 사용 가능한 자막이 없습니다.</p>
                    </div>
                `}
                
                <div style="margin-top: 2rem; text-align: center;">
                    <a href="https://youtube.com/watch?v=${data.video_id}" 
                       target="_blank" 
                       class="btn btn-primary" 
                       style="text-decoration: none; display: inline-flex;">
                        <i class="fab fa-youtube"></i>
                        YouTube에서 보기
                    </a>
                </div>
            `;
            
            document.getElementById('scriptModal').style.display = 'block';
        }
        
        // Close script modal
        function closeScriptModal() {
            document.getElementById('scriptModal').style.display = 'none';
        }
    </script>
</body>
</html>
    '''

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        channel_query = data.get('channel_query', '')
        max_videos = data.get('max_videos', 50)
        
        if not channel_query:
            return jsonify({'error': '채널 정보가 필요합니다.'})
        
        # 채널 ID 검색
        channel_id = analyzer.search_channel(channel_query)
        if not channel_id:
            return jsonify({'error': '채널을 찾을 수 없습니다.'})
        
        # 채널 분석 (사용자가 설정한 동영상 수로)
        result = analyzer.analyze_channel_with_count(channel_id, max_videos)
        if not result:
            return jsonify({'error': '채널 분석 중 오류가 발생했습니다.'})
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'분석 중 오류 발생: {str(e)}'})

@app.route('/analyze_video', methods=['POST'])
def analyze_video():
    try:
        data = request.get_json()
        video_id = data.get('video_id', '')
        
        if not video_id:
            return jsonify({'error': '동영상 ID가 필요합니다.'})
        
        # 개별 동영상 정보 가져오기
        video_response = analyzer.youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=video_id
        ).execute()
        
        if not video_response['items']:
            return jsonify({'error': '동영상을 찾을 수 없습니다.'})
        
        video = video_response['items'][0]
        result = {
            'video_id': video_id,
            'title': video['snippet']['title'],
            'description': video['snippet']['description'],
            'published_at': video['snippet']['publishedAt'],
            'view_count': int(video['statistics'].get('viewCount', 0)),
            'like_count': int(video['statistics'].get('likeCount', 0)),
            'comment_count': int(video['statistics'].get('commentCount', 0)),
            'duration': video['contentDetails']['duration']
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'동영상 분석 중 오류 발생: {str(e)}'})

@app.route('/get_video_script', methods=['POST'])
def get_video_script():
    try:
        data = request.get_json()
        video_id = data.get('video_id', '')
        
        if not video_id:
            return jsonify({'error': '동영상 ID가 필요합니다.'})
        
        # 동영상 정보 가져오기
        video_response = analyzer.youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()
        
        if not video_response['items']:
            return jsonify({'error': '동영상을 찾을 수 없습니다.'})
        
        video = video_response['items'][0]
        title = video['snippet']['title']
        
        # 실제 자막 가져오기
        script = None
        summary = None
        
        try:
            # 먼저 한국어 자막 시도, 없으면 영어, 그 다음 자동 생성 자막
            # 다양한 언어 코드로 자막 시도
            language_codes = ['ko', 'en', 'en-US', 'en-GB']
            
            transcript_data = None
            for lang in language_codes:
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                    break
                except:
                    continue
            
            # 언어 지정 없이 시도
            if not transcript_data:
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                except:
                    transcript_data = None
            
            if transcript_data:
                # 자막 데이터를 텍스트로 변환
                formatter = TextFormatter()
                script = formatter.format_transcript(transcript_data)
                
                # 간단한 요약 생성 (첫 500자 + 마지막 200자)
                if len(script) > 700:
                    summary = f"📝 스크립트 요약:\n\n시작 부분: {script[:300]}...\n\n마지막 부분: ...{script[-200:]}"
                else:
                    summary = f"📝 전체 스크립트:\n\n{script}"
                    
        except Exception as e:
            print(f"자막 가져오기 실패: {e}")
            script = None
            summary = None
        
        # 자막이 없을 때 항상 유용한 요약 제공
        if not script:
            # 동영상 메타데이터 수집
            description = video.get('snippet', {}).get('description', '')
            duration = video.get('contentDetails', {}).get('duration', 'N/A')
            published = video.get('snippet', {}).get('publishedAt', 'N/A')
            tags = video.get('snippet', {}).get('tags', [])
            
            # 날짜 포맷팅
            if published != 'N/A':
                from datetime import datetime
                published_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                published = published_date.strftime('%Y년 %m월 %d일')
            
            # 종합적인 요약 생성
            summary_parts = []
            summary_parts.append("📋 **동영상 정보**")
            summary_parts.append(f"• 업로드: {published}")
            summary_parts.append(f"• 길이: {duration}")
            
            if tags:
                tag_str = ', '.join(tags[:5])
                summary_parts.append(f"• 태그: {tag_str}")
            
            if description:
                summary_parts.append("\n📝 **내용 설명**")
                desc_preview = description.strip()[:400]
                if len(description) > 400:
                    desc_preview += "..."
                summary_parts.append(desc_preview)
            else:
                summary_parts.append("\n💡 **분석 결과**")
                summary_parts.append("이 동영상은 제목을 통해 내용을 파악할 수 있으며, 상세 분석을 통해 더 많은 정보를 얻을 수 있습니다.")
                
            summary_parts.append("\n🎯 **활용 방법**")
            summary_parts.append("• 분석 버튼: 조회수, 좋아요, 댓글 등 상세 통계 확인")
            summary_parts.append("• 상세 버튼: 동영상 메타데이터 및 성과 지표 분석")
            
            summary = '\n'.join(summary_parts)
        
        result = {
            'video_id': video_id,
            'title': title,
            'script': script,
            'summary': summary
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'스크립트 가져오기 중 오류 발생: {str(e)}'})

@app.route('/api/korean_trends', methods=['GET'])
def korean_trends():
    """한국어 트렌드 분석 API"""
    try:
        trends = trend_analyzer.get_trending_keywords()
        return jsonify(trends)
    except Exception as e:
        return jsonify({'error': f'트렌드 분석 중 오류 발생: {str(e)}'})

@app.route('/api/content_recommendations', methods=['POST'])
def content_recommendations():
    """AI 콘텐츠 추천 API"""
    try:
        data = request.get_json()
        channel_category = data.get('category', '일반')
        subscriber_count = data.get('subscriber_count', 0)
        
        # 트렌딩 키워드 가져오기
        trends = trend_analyzer.get_trending_keywords()
        trending_keywords = trends['trending_keywords']
        
        # 콘텐츠 추천 생성
        recommendations = content_engine.generate_content_ideas(
            channel_category, trending_keywords, subscriber_count
        )
        
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': f'콘텐츠 추천 중 오류 발생: {str(e)}'})

@app.route('/api/competitor_analysis', methods=['POST'])
def competitor_analysis():
    """경쟁사 분석 API"""
    try:
        data = request.get_json()
        main_channel = data.get('main_channel')
        competitor_channels = data.get('competitor_channels', [])
        
        if not main_channel:
            return jsonify({'error': '메인 채널 정보가 필요합니다.'})
        
        analysis = competitor_analyzer.compare_channels(main_channel, competitor_channels)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': f'경쟁사 분석 중 오류 발생: {str(e)}'})

@app.route('/api/sentiment_analysis', methods=['POST'])
def sentiment_analysis():
    """댓글 감정 분석 API"""
    try:
        data = request.get_json()
        comments = data.get('comments', [])
        
        analysis = sentiment_analyzer.analyze_comments_sentiment(comments)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': f'감정 분석 중 오류 발생: {str(e)}'})

@app.route('/api/advanced_analytics', methods=['POST'])
def advanced_analytics():
    """통합 고급 분석 API"""
    try:
        data = request.get_json()
        channel_data = data.get('channel_data')
        recent_videos = data.get('recent_videos', [])
        
        if not channel_data:
            return jsonify({'error': '채널 데이터가 필요합니다.'})
        
        # 트렌드 분석
        trends = trend_analyzer.analyze_channel_trends(
            channel_data.get('channel_name', ''), recent_videos
        )
        
        # 콘텐츠 추천
        recommendations = content_engine.generate_content_ideas(
            '일반', trends['trending_keywords'], 
            channel_data.get('subscriber_count', 0)
        )
        
        # 가상의 댓글 샘플로 감정 분석 (실제로는 YouTube API로 댓글 수집)
        sample_comments = [
            "정말 유용한 영상이네요!", "감사합니다", "최고에요", 
            "별로네요", "도움이 되었습니다", "구독했어요"
        ]
        sentiment = sentiment_analyzer.analyze_comments_sentiment(sample_comments)
        
        return jsonify({
            'trends': trends,
            'content_recommendations': recommendations,
            'sentiment_analysis': sentiment,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': f'고급 분석 중 오류 발생: {str(e)}'})

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Analytics Studio 시작")
    print("=" * 60)
    print("주소: http://localhost:8080")
    print("프리미엄 분석 및 상세 리포트")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)