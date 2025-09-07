# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)

API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

class CompleteYouTubeAnalyzer:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def search_channel(self, query):
        """채널 검색"""
        try:
            search_response = self.youtube.search().list(
                q=query,
                part='snippet',
                type='channel',
                maxResults=5
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
    
    def get_all_videos(self, channel_id, max_results=50):
        """채널의 모든 동영상 가져오기"""
        try:
            # 업로드 재생목록 ID
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return []
            
            uploads_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']
            
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                # 재생목록에서 동영상 ID 가져오기
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                ).execute()
                
                video_ids = [item['snippet']['resourceId']['videoId'] 
                           for item in playlist_response['items']]
                
                # 동영상 상세 정보
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
            print(f"동영상 조회 오류: {e}")
            return []
    
    def analyze_videos(self, videos):
        """동영상 분석"""
        if not videos:
            return {}
        
        df = pd.DataFrame(videos)
        
        # 날짜 변환 (시간대 정보 제거)
        df['published_date'] = pd.to_datetime(df['published_date']).dt.tz_localize(None)
        df['days_ago'] = (datetime.now() - df['published_date']).dt.days
        
        # 참여율 계산
        df['engagement_rate'] = ((df['like_count'] + df['comment_count']) / df['view_count'] * 100)
        df['engagement_rate'] = df['engagement_rate'].fillna(0)
        
        # 성과 분석
        analysis = {
            'total_videos': len(videos),
            'total_views': int(df['view_count'].sum()),
            'total_likes': int(df['like_count'].sum()),
            'total_comments': int(df['comment_count'].sum()),
            'avg_views': int(df['view_count'].mean()),
            'avg_likes': int(df['like_count'].mean()),
            'avg_comments': int(df['comment_count'].mean()),
            'avg_engagement': round(df['engagement_rate'].mean(), 2),
            'max_views': int(df['view_count'].max()),
            'min_views': int(df['view_count'].min()),
        }
        
        # 최고 성과 동영상 TOP 5
        top_videos = df.nlargest(5, 'view_count')[['title', 'view_count', 'like_count', 'published_date']].to_dict('records')
        analysis['top_videos'] = top_videos
        
        # 최신 동영상 5개
        recent_videos = df.nsmallest(5, 'days_ago')[['title', 'view_count', 'like_count', 'published_date']].to_dict('records')
        analysis['recent_videos'] = recent_videos
        
        # 월별 분석
        df['month'] = df['published_date'].dt.to_period('M')
        monthly_stats = df.groupby('month').agg({
            'view_count': ['sum', 'mean', 'count'],
            'like_count': 'sum',
            'engagement_rate': 'mean'
        }).round(0)
        
        analysis['monthly_stats'] = monthly_stats.to_dict() if not monthly_stats.empty else {}
        
        return analysis
    
    def calculate_detailed_revenue(self, channel_info, video_analysis):
        """상세 수익 계산"""
        stats = channel_info['statistics']
        subscribers = int(stats.get('subscriberCount', 0))
        total_views = int(stats.get('viewCount', 0))
        video_count = int(stats.get('videoCount', 0))
        
        # 동영상 분석 데이터
        avg_views = video_analysis.get('avg_views', subscribers * 0.3)
        avg_engagement = video_analysis.get('avg_engagement', 3)
        
        # CPM 설정 (카테고리별)
        description = channel_info['snippet'].get('description', '').lower()
        if any(word in description for word in ['코딩', '프로그래밍', 'programming', 'coding']):
            category = '프로그래밍'
            cpm = 4000
        elif any(word in description for word in ['교육', 'education', '강의']):
            category = '교육'
            cpm = 3500
        else:
            category = '일반'
            cpm = 2500
        
        # 월 수익 계산
        monthly_videos = 8
        monthly_views = avg_views * monthly_videos
        monthly_ad_revenue = (monthly_views / 1000) * cpm
        
        # 스폰서십 (참여율 고려)
        base_sponsorship = subscribers * 50
        engagement_multiplier = min(2.0, avg_engagement / 5)  # 참여율 5% 기준으로 최대 2배
        monthly_sponsorship = (base_sponsorship * engagement_multiplier) / 12
        
        # 멤버십 수익
        membership_rate = 0.015 if avg_engagement > 5 else 0.01  # 참여율 높으면 멤버십 전환율 증가
        monthly_membership = subscribers * membership_rate * 4900 if subscribers >= 1000 else 0
        
        # 슈퍼챗/슈퍼땡스
        superchat_revenue = monthly_views * 0.001 * 200  # 조회수의 0.1%가 평균 200원
        
        # 총 수익
        total_monthly = int(monthly_ad_revenue + monthly_sponsorship + monthly_membership + superchat_revenue)
        
        return {
            'category': category,
            'cpm': cpm,
            'monthly_ad': int(monthly_ad_revenue),
            'monthly_sponsor': int(monthly_sponsorship),
            'monthly_membership': int(monthly_membership),
            'monthly_superchat': int(superchat_revenue),
            'total_monthly': total_monthly,
            'annual_potential': total_monthly * 12,
            'engagement_multiplier': round(engagement_multiplier, 2)
        }
    
    def full_analysis(self, query, max_videos=50):
        """완전 분석"""
        try:
            print(f"분석 시작: {query}")
            
            # 채널 검색
            if "@" in query:
                search_query = query.split("@")[-1]
            else:
                search_query = query
            
            channel_id = self.search_channel(search_query)
            if not channel_id:
                return {'error': '채널을 찾을 수 없습니다.'}
            
            print(f"채널 발견: {channel_id}")
            
            # 채널 정보
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return {'error': '채널 정보를 가져올 수 없습니다.'}
            
            print(f"채널 정보 수집 완료")
            
            # 모든 동영상 정보
            print(f"동영상 {max_videos}개 분석 중...")
            videos = self.get_all_videos(channel_id, max_videos)
            print(f"동영상 {len(videos)}개 수집 완료")
            
            # 동영상 분석
            video_analysis = self.analyze_videos(videos)
            print("동영상 분석 완료")
            
            # 수익 계산
            revenue_analysis = self.calculate_detailed_revenue(channel_info, video_analysis)
            print("수익 분석 완료")
            
            # 결과 통합
            stats = channel_info['statistics']
            result = {
                'success': True,
                'channel_id': channel_id,
                'channel_name': channel_info['snippet']['title'],
                'description': channel_info['snippet']['description'][:300],
                'subscribers': int(stats.get('subscriberCount', 0)),
                'total_views': int(stats.get('viewCount', 0)),
                'video_count': int(stats.get('videoCount', 0)),
                'analyzed_videos': len(videos),
                'video_analysis': video_analysis,
                'revenue_analysis': revenue_analysis,
                'created_date': channel_info['snippet']['publishedAt'][:10]
            }
            
            return result
            
        except HttpError as e:
            print(f"API 오류: {e}")
            return {'error': f'YouTube API 오류: {str(e)}'}
        except Exception as e:
            print(f"일반 오류: {e}")
            return {'error': f'분석 중 오류: {str(e)}'}

# Flask 앱
analyzer = CompleteYouTubeAnalyzer(API_KEY)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>완전한 YouTube 채널 분석</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1 { text-align: center; color: #2c3e50; }
        .input-group {
            margin: 20px 0;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], input[type="number"] {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        .btn {
            background: #3498db;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
        }
        .btn:hover { background: #2980b9; }
        .btn:disabled { background: #bdc3c7; cursor: not-allowed; }
        .result {
            margin-top: 30px;
            display: none;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #e74c3c;
        }
        .stat-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        .video-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .video-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            align-items: center;
        }
        .video-item:last-child {
            border-bottom: none;
        }
        .video-thumb {
            width: 120px;
            height: 90px;
            border-radius: 5px;
            margin-right: 15px;
        }
        .video-info {
            flex: 1;
        }
        .video-title {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .video-stats {
            color: #666;
            font-size: 0.9em;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .section h3 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>완전한 YouTube 채널 분석 도구</h1>
        <p style="text-align: center; color: #7f8c8d;">
            채널의 모든 동영상을 분석하여 상세한 사업성 리포트를 제공합니다
        </p>
        
        <form id="analysisForm">
            <div class="input-group">
                <label for="channelUrl">채널 URL 또는 채널명</label>
                <input type="text" id="channelUrl" value="로직알려주는남자" required>
            </div>
            
            <div class="input-group">
                <label for="maxVideos">분석할 동영상 수 (최대 200개)</label>
                <input type="number" id="maxVideos" value="50" min="10" max="200">
            </div>
            
            <button type="submit" class="btn" id="analyzeBtn">완전 분석 시작</button>
        </form>
        
        <div class="loading" id="loading">
            <h3>분석 진행 중...</h3>
            <p>채널 정보와 동영상들을 수집하고 있습니다. 잠시만 기다려주세요.</p>
        </div>
        
        <div class="result" id="result">
            <div id="resultContent"></div>
        </div>
    </div>

    <script>
        document.getElementById('analysisForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const channelUrl = document.getElementById('channelUrl').value;
            const maxVideos = document.getElementById('maxVideos').value;
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const resultContent = document.getElementById('resultContent');
            const analyzeBtn = document.getElementById('analyzeBtn');
            
            loading.style.display = 'block';
            result.style.display = 'none';
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = '분석 중...';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        channel_url: channelUrl,
                        max_videos: parseInt(maxVideos)
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    resultContent.innerHTML = `
                        <div class="error">
                            <h3>분석 실패</h3>
                            <p>${data.error}</p>
                        </div>
                    `;
                } else {
                    const va = data.video_analysis;
                    const ra = data.revenue_analysis;
                    
                    resultContent.innerHTML = `
                        <div class="section">
                            <h3>채널 기본 정보</h3>
                            <div class="stats-grid">
                                <div class="stat-card">
                                    <div class="stat-value">${data.channel_name}</div>
                                    <div class="stat-label">채널명</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${data.subscribers.toLocaleString()}명</div>
                                    <div class="stat-label">구독자</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${data.total_views.toLocaleString()}회</div>
                                    <div class="stat-label">총 조회수</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${data.video_count}개</div>
                                    <div class="stat-label">총 동영상</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h3>동영상 분석 결과 (${data.analyzed_videos}개 분석)</h3>
                            <div class="stats-grid">
                                <div class="stat-card">
                                    <div class="stat-value">${va.avg_views.toLocaleString()}회</div>
                                    <div class="stat-label">평균 조회수</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${va.avg_engagement}%</div>
                                    <div class="stat-label">평균 참여율</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${va.total_views.toLocaleString()}회</div>
                                    <div class="stat-label">분석된 총 조회수</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${va.total_likes.toLocaleString()}개</div>
                                    <div class="stat-label">총 좋아요</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h3>수익 분석</h3>
                            <div class="stats-grid">
                                <div class="stat-card">
                                    <div class="stat-value">${ra.monthly_ad.toLocaleString()}원</div>
                                    <div class="stat-label">월 광고 수익</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${ra.monthly_sponsor.toLocaleString()}원</div>
                                    <div class="stat-label">월 스폰서십</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${ra.monthly_membership.toLocaleString()}원</div>
                                    <div class="stat-label">월 멤버십</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${ra.total_monthly.toLocaleString()}원</div>
                                    <div class="stat-label">총 월 수익</div>
                                </div>
                            </div>
                            <div style="text-align: center; margin: 20px 0; padding: 20px; background: #e8f5e8; border-radius: 10px;">
                                <h3 style="color: #27ae60;">연 예상 수익: ${ra.annual_potential.toLocaleString()}원</h3>
                                <p>카테고리: ${ra.category} | CPM: ${ra.cpm}원 | 참여율 보정: ${ra.engagement_multiplier}배</p>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h3>인기 동영상 TOP 5</h3>
                            <div class="video-list">
                                ${va.top_videos.map((video, index) => `
                                    <div class="video-item">
                                        <div class="video-info">
                                            <div class="video-title">${index + 1}. ${video.title}</div>
                                            <div class="video-stats">
                                                조회수: ${video.view_count.toLocaleString()}회 | 
                                                좋아요: ${video.like_count.toLocaleString()}개 | 
                                                업로드: ${video.published_date.split('T')[0]}
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <div class="section">
                            <h3>최신 동영상 5개</h3>
                            <div class="video-list">
                                ${va.recent_videos.map((video, index) => `
                                    <div class="video-item">
                                        <div class="video-info">
                                            <div class="video-title">${index + 1}. ${video.title}</div>
                                            <div class="video-stats">
                                                조회수: ${video.view_count.toLocaleString()}회 | 
                                                좋아요: ${video.like_count.toLocaleString()}개 | 
                                                업로드: ${video.published_date.split('T')[0]}
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }
                
                loading.style.display = 'none';
                result.style.display = 'block';
                
            } catch (error) {
                loading.style.display = 'none';
                resultContent.innerHTML = `
                    <div class="error">
                        <h3>네트워크 오류</h3>
                        <p>${error.message}</p>
                    </div>
                `;
                result.style.display = 'block';
            } finally {
                analyzeBtn.disabled = false;
                analyzeBtn.textContent = '완전 분석 시작';
            }
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
        max_videos = int(data.get('max_videos', 50))
        
        if not channel_url:
            return jsonify({'error': '채널 URL을 입력해주세요'}), 400
        
        result = analyzer.full_analysis(channel_url, max_videos)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("완전한 YouTube 채널 분석 도구 시작")
    print("=" * 60)
    print("주소: http://localhost:8080")
    print("기능: 채널 + 모든 동영상 완전 분석")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)