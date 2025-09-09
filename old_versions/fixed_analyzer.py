# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from googleapiclient.discovery import build

app = Flask(__name__)
API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

class FixedAnalyzer:
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    def search_channel(self, query):
        try:
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
            
            response = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_id,
                maxResults=max_videos
            ).execute()
            
            video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
            
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
            print(f"Analysis Start: {query}")
            
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
                'recent_videos': recent_videos
            }
            
        except Exception as e:
            print(f"Analysis Error: {e}")
            return {'error': f'Analysis Error: {str(e)}'}

analyzer = FixedAnalyzer()

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>YouTube 채널 완전 분석</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #333; text-align: center; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .btn { background: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .result { margin-top: 20px; display: none; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-box { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .stat-label { color: #666; margin-top: 5px; }
        .section { background: #f8f9fa; margin: 20px 0; padding: 20px; border-radius: 8px; }
        .video-item { padding: 10px; border-bottom: 1px solid #eee; }
        .video-title { font-weight: bold; }
        .video-stats { color: #666; font-size: 14px; }
        .error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }
        .loading { text-align: center; padding: 20px; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube 채널 완전 분석 도구</h1>
        
        <div class="form-group">
            <label>채널명 또는 URL</label>
            <input type="text" id="channelInput" value="로직알려주는남자" placeholder="채널명 입력">
        </div>
        
        <div class="form-group">
            <label>분석할 동영상 수</label>
            <input type="number" id="videoCount" value="30" min="10" max="300">
        </div>
        
        <button class="btn" onclick="analyze()" id="analyzeBtn">완전 분석 시작</button>
        
        <div class="loading" id="loading">
            <h3>분석 중...</h3>
            <p>채널과 동영상을 분석하고 있습니다.</p>
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
            alert('채널명을 입력하세요');
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
                content.innerHTML = '<div class="error"><h3>분석 실패</h3><p>' + data.error + '</p></div>';
            } else {
                content.innerHTML = `
                    <div class="section">
                        <h2>📺 채널 정보</h2>
                        <div class="stats">
                            <div class="stat-box">
                                <div class="stat-value">${data.channel_name}</div>
                                <div class="stat-label">채널명</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">${data.subscribers.toLocaleString()}명</div>
                                <div class="stat-label">구독자</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">${data.total_views.toLocaleString()}회</div>
                                <div class="stat-label">총 조회수</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">${data.video_count}개</div>
                                <div class="stat-label">총 동영상</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>📊 동영상 분석 (${data.analyzed_videos}개)</h2>
                        <div class="stats">
                            <div class="stat-box">
                                <div class="stat-value">${data.avg_views.toLocaleString()}회</div>
                                <div class="stat-label">평균 조회수</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">${data.avg_engagement}%</div>
                                <div class="stat-label">평균 참여율</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>💰 예상 수익</h2>
                        <div class="stats">
                            <div class="stat-box">
                                <div class="stat-value">${data.monthly_ad.toLocaleString()}원</div>
                                <div class="stat-label">월 광고 수익</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">${data.monthly_sponsor.toLocaleString()}원</div>
                                <div class="stat-label">월 스폰서십</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">${data.monthly_membership.toLocaleString()}원</div>
                                <div class="stat-label">월 멤버십</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">${data.total_monthly.toLocaleString()}원</div>
                                <div class="stat-label">총 월 수익</div>
                            </div>
                        </div>
                        <div style="text-align: center; margin: 20px 0; padding: 15px; background: #d4edda; border-radius: 5px;">
                            <h3>연 예상 수익: ${data.annual_revenue.toLocaleString()}원</h3>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>🏆 인기 동영상 TOP 5</h2>
                        ${data.top_videos.map((video, i) => `
                            <div class="video-item">
                                <div class="video-title">${i+1}. ${video.title}</div>
                                <div class="video-stats">
                                    조회수: ${video.views.toLocaleString()}회 | 좋아요: ${video.likes.toLocaleString()}개 | 업로드: ${video.published}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="section">
                        <h2>🆕 최신 동영상 5개</h2>
                        ${data.recent_videos.map((video, i) => `
                            <div class="video-item">
                                <div class="video-title">${i+1}. ${video.title}</div>
                                <div class="video-stats">
                                    조회수: ${video.views.toLocaleString()}회 | 좋아요: ${video.likes.toLocaleString()}개 | 업로드: ${video.published}
                                </div>
                            </div>
                        `).join('')}
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
    print("YouTube Fixed Analyzer")
    print("Address: http://localhost:8080")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=8080)