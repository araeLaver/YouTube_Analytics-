# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from googleapiclient.discovery import build

app = Flask(__name__)

API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

class SelectiveAnalyzer:
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
            print(f"검색 오류: {e}")
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
            print(f"채널 정보 오류: {e}")
            return None
    
    def get_video_list(self, channel_id, max_videos=50):
        """썸네일과 함께 동영상 목록 가져오기"""
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
            
            video_list = []
            for item in response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                video_list.append({
                    'video_id': video_id,
                    'title': item['snippet']['title'],
                    'published': item['snippet']['publishedAt'][:10],
                    'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                    'description': item['snippet']['description'][:150] + '...'
                })
            
            return video_list
            
        except Exception as e:
            print(f"동영상 목록 조회 오류: {e}")
            return []
    
    def analyze_selected_videos(self, video_ids, channel_info):
        """선택된 동영상들 분석"""
        try:
            # 선택된 동영상들의 상세 정보
            videos_response = self.youtube.videos().list(
                part='statistics,snippet',
                id=','.join(video_ids)
            ).execute()
            
            videos = []
            total_views = 0
            total_likes = 0
            total_comments = 0
            
            for video in videos_response['items']:
                views = int(video['statistics'].get('viewCount', 0))
                likes = int(video['statistics'].get('likeCount', 0))
                comments = int(video['statistics'].get('commentCount', 0))
                
                videos.append({
                    'title': video['snippet']['title'],
                    'published': video['snippet']['publishedAt'][:10],
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'engagement_rate': round((likes + comments) / views * 100, 2) if views > 0 else 0
                })
                
                total_views += views
                total_likes += likes
                total_comments += comments
            
            # 분석 결과
            avg_views = int(total_views / len(videos)) if videos else 0
            avg_engagement = round((total_likes + total_comments) / total_views * 100, 2) if total_views > 0 else 0
            
            # 채널 기본 정보
            stats = channel_info['statistics']
            subscribers = int(stats.get('subscriberCount', 0))
            
            # 수익 계산 (선택된 동영상들 기준)
            monthly_videos = 8  # 월 8개 업로드 가정
            monthly_views = avg_views * monthly_videos
            cpm = 3500  # 교육 채널 기준
            monthly_ad = (monthly_views / 1000) * cpm
            
            # 스폰서십 (참여율 고려)
            base_sponsorship = subscribers * 60
            engagement_multiplier = min(2.0, avg_engagement / 5)
            monthly_sponsor = (base_sponsorship * engagement_multiplier) / 12
            
            # 멤버십
            monthly_membership = subscribers * 0.015 * 4900 if subscribers >= 1000 else 0
            
            total_monthly = int(monthly_ad + monthly_sponsor + monthly_membership)
            
            return {
                'success': True,
                'analyzed_videos': len(videos),
                'selected_videos': videos,
                'total_views': total_views,
                'total_likes': total_likes,
                'avg_views': avg_views,
                'avg_engagement': avg_engagement,
                'monthly_ad': int(monthly_ad),
                'monthly_sponsor': int(monthly_sponsor),
                'monthly_membership': int(monthly_membership),
                'total_monthly': total_monthly,
                'annual_revenue': total_monthly * 12
            }
            
        except Exception as e:
            print(f"선택 분석 오류: {e}")
            return {'error': f'분석 중 오류: {str(e)}'}
    
    def get_channel_basic(self, query):
        """채널 기본 정보 + 동영상 목록 가져오기"""
        try:
            # 채널 검색
            channel_id = self.search_channel(query)
            if not channel_id:
                return {'error': '채널을 찾을 수 없습니다'}
            
            # 채널 정보
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return {'error': '채널 정보 없음'}
            
            # 동영상 목록 (썸네일 포함)
            video_list = self.get_video_list(channel_id, 50)
            
            # 기본 통계
            stats = channel_info['statistics']
            
            return {
                'success': True,
                'channel_id': channel_id,
                'channel_name': channel_info['snippet']['title'],
                'subscribers': int(stats.get('subscriberCount', 0)),
                'total_views': int(stats.get('viewCount', 0)),
                'video_count': int(stats.get('videoCount', 0)),
                'video_list': video_list,
                'channel_info': channel_info  # 나중에 분석할 때 사용
            }
            
        except Exception as e:
            print(f"기본 정보 오류: {e}")
            return {'error': f'채널 정보 오류: {str(e)}'}

analyzer = SelectiveAnalyzer()

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>YouTube 동영상 선택 분석</title>
    <style>
        body { font-family: Arial; max-width: 1400px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #333; text-align: center; }
        .step { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .step h3 { margin-top: 0; color: #007bff; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        
        .video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; margin: 20px 0; }
        .video-card { border: 2px solid #ddd; border-radius: 8px; padding: 10px; cursor: pointer; transition: all 0.3s; }
        .video-card:hover { border-color: #007bff; transform: translateY(-2px); }
        .video-card.selected { border-color: #28a745; background: #f0fff0; }
        .video-thumb { width: 100%; height: 150px; object-fit: cover; border-radius: 5px; }
        .video-title { font-weight: bold; margin: 8px 0; font-size: 14px; line-height: 1.3; }
        .video-date { color: #666; font-size: 12px; }
        .video-desc { color: #888; font-size: 12px; margin-top: 5px; }
        
        .selection-info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .channel-info { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-box { background: #fff; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ddd; }
        .stat-value { font-size: 20px; font-weight: bold; color: #007bff; }
        .stat-label { color: #666; margin-top: 5px; font-size: 12px; }
        
        .result { margin-top: 30px; display: none; }
        .error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }
        .loading { text-align: center; padding: 20px; display: none; }
        
        .selected-videos { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .video-item { padding: 10px; border-bottom: 1px solid #eee; }
        .video-item:last-child { border-bottom: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube 동영상 선택 분석</h1>
        <p style="text-align: center; color: #666;">원하는 동영상들을 선택해서 정확한 분석을 받아보세요</p>
        
        <!-- Step 1: 채널 검색 -->
        <div class="step" id="step1">
            <h3>1단계: 분석할 채널 입력</h3>
            <div class="form-group">
                <label>채널명 또는 URL</label>
                <input type="text" id="channelInput" value="로직알려주는남자" placeholder="채널명을 입력하세요">
            </div>
            <button class="btn" onclick="loadChannel()" id="loadBtn">채널 동영상 불러오기</button>
        </div>
        
        <!-- Step 2: 채널 정보 및 동영상 선택 -->
        <div class="step" id="step2" style="display: none;">
            <h3>2단계: 분석할 동영상 선택</h3>
            
            <div class="channel-info" id="channelInfo"></div>
            
            <div class="selection-info">
                <strong>선택된 동영상: <span id="selectedCount">0</span>개</strong>
                <button class="btn btn-success" onclick="analyzeSelected()" id="analyzeBtn" disabled>선택된 동영상 분석하기</button>
                <button class="btn" onclick="selectAll()">전체 선택</button>
                <button class="btn" onclick="clearAll()">선택 해제</button>
            </div>
            
            <div class="video-grid" id="videoGrid"></div>
        </div>
        
        <div class="loading" id="loading">
            <h3>분석 중...</h3>
            <p>선택된 동영상들을 분석하고 있습니다.</p>
        </div>
        
        <!-- Step 3: 분석 결과 -->
        <div class="result" id="result">
            <div id="resultContent"></div>
        </div>
    </div>

    <script>
        let selectedVideos = [];
        let channelData = null;
        
        async function loadChannel() {
            const channel = document.getElementById('channelInput').value;
            const loadBtn = document.getElementById('loadBtn');
            
            if (!channel) {
                alert('채널명을 입력하세요');
                return;
            }
            
            loadBtn.disabled = true;
            loadBtn.textContent = '불러오는 중...';
            
            try {
                const response = await fetch('/load_channel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: channel })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    alert('오류: ' + data.error);
                } else {
                    channelData = data;
                    displayChannelInfo(data);
                    displayVideos(data.video_list);
                    document.getElementById('step2').style.display = 'block';
                }
                
            } catch (error) {
                alert('네트워크 오류: ' + error.message);
            }
            
            loadBtn.disabled = false;
            loadBtn.textContent = '채널 동영상 불러오기';
        }
        
        function displayChannelInfo(data) {
            document.getElementById('channelInfo').innerHTML = `
                <h4>📺 ${data.channel_name}</h4>
                <div class="stats">
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
                    <div class="stat-box">
                        <div class="stat-value">${data.video_list.length}개</div>
                        <div class="stat-label">최근 동영상</div>
                    </div>
                </div>
            `;
        }
        
        function displayVideos(videos) {
            const grid = document.getElementById('videoGrid');
            grid.innerHTML = videos.map(video => `
                <div class="video-card" onclick="toggleVideo('${video.video_id}')" data-id="${video.video_id}">
                    <img src="${video.thumbnail}" alt="썸네일" class="video-thumb">
                    <div class="video-title">${video.title}</div>
                    <div class="video-date">업로드: ${video.published}</div>
                    <div class="video-desc">${video.description}</div>
                </div>
            `).join('');
        }
        
        function toggleVideo(videoId) {
            const card = document.querySelector(`[data-id="${videoId}"]`);
            const index = selectedVideos.indexOf(videoId);
            
            if (index > -1) {
                selectedVideos.splice(index, 1);
                card.classList.remove('selected');
            } else {
                selectedVideos.push(videoId);
                card.classList.add('selected');
            }
            
            updateSelectionInfo();
        }
        
        function selectAll() {
            const cards = document.querySelectorAll('.video-card');
            selectedVideos = [];
            cards.forEach(card => {
                const videoId = card.dataset.id;
                selectedVideos.push(videoId);
                card.classList.add('selected');
            });
            updateSelectionInfo();
        }
        
        function clearAll() {
            selectedVideos = [];
            document.querySelectorAll('.video-card').forEach(card => {
                card.classList.remove('selected');
            });
            updateSelectionInfo();
        }
        
        function updateSelectionInfo() {
            document.getElementById('selectedCount').textContent = selectedVideos.length;
            document.getElementById('analyzeBtn').disabled = selectedVideos.length === 0;
        }
        
        async function analyzeSelected() {
            if (selectedVideos.length === 0) {
                alert('분석할 동영상을 선택하세요');
                return;
            }
            
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const analyzeBtn = document.getElementById('analyzeBtn');
            
            loading.style.display = 'block';
            result.style.display = 'none';
            analyzeBtn.disabled = true;
            
            try {
                const response = await fetch('/analyze_selected', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        video_ids: selectedVideos,
                        channel_info: channelData.channel_info
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('resultContent').innerHTML = 
                        '<div class="error"><h3>분석 실패</h3><p>' + data.error + '</p></div>';
                } else {
                    displayAnalysisResult(data);
                }
                
            } catch (error) {
                document.getElementById('resultContent').innerHTML = 
                    '<div class="error"><h3>네트워크 오류</h3><p>' + error.message + '</p></div>';
            }
            
            loading.style.display = 'none';
            result.style.display = 'block';
            analyzeBtn.disabled = false;
        }
        
        function displayAnalysisResult(data) {
            document.getElementById('resultContent').innerHTML = `
                <div class="step">
                    <h3>📊 선택 분석 결과</h3>
                    
                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-value">${data.analyzed_videos}개</div>
                            <div class="stat-label">분석된 동영상</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${data.total_views.toLocaleString()}회</div>
                            <div class="stat-label">총 조회수</div>
                        </div>
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
                
                <div class="step">
                    <h3>💰 예상 수익 (선택 기준)</h3>
                    
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
                    
                    <div style="text-align: center; margin: 20px 0; padding: 20px; background: #d4edda; border-radius: 8px;">
                        <h3>연 예상 수익: ${data.annual_revenue.toLocaleString()}원</h3>
                        <p>선택된 ${data.analyzed_videos}개 동영상 성과 기준</p>
                    </div>
                </div>
                
                <div class="step">
                    <h3>📋 선택된 동영상 목록</h3>
                    ${data.selected_videos.map((video, i) => `
                        <div class="video-item">
                            <div style="font-weight: bold;">${i+1}. ${video.title}</div>
                            <div style="color: #666; font-size: 14px;">
                                조회수: ${video.views.toLocaleString()}회 | 
                                좋아요: ${video.likes.toLocaleString()}개 | 
                                참여율: ${video.engagement_rate}% | 
                                업로드: ${video.published}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    </script>
</body>
</html>
    '''

@app.route('/load_channel', methods=['POST'])
def load_channel():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        result = analyzer.get_channel_basic(query)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/analyze_selected', methods=['POST'])
def analyze_selected():
    try:
        data = request.get_json()
        video_ids = data.get('video_ids', [])
        channel_info = data.get('channel_info', {})
        
        result = analyzer.analyze_selected_videos(video_ids, channel_info)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube 동영상 선택 분석 도구")
    print("주소: http://localhost:8080")
    print("기능: 썸네일 보고 동영상 선택해서 분석")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)