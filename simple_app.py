# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re

app = Flask(__name__)
API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"
youtube = build('youtube', 'v3', developerKey=API_KEY)

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>YouTube 채널 분석기</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .form-group { margin: 20px 0; }
        input, select, button { padding: 10px; font-size: 16px; margin: 5px; }
        button { background: #ff0000; color: white; border: none; cursor: pointer; }
        #loading { display: none; color: #666; }
        #results { margin-top: 30px; border: 1px solid #ddd; padding: 20px; }
    </style>
</head>
<body>
    <h1>YouTube 채널 분석기</h1>
    
    <form onsubmit="analyzeChannel(event)">
        <div class="form-group">
            <input type="text" id="channelInput" placeholder="채널 URL 또는 채널명 입력" required style="width: 400px;">
        </div>
        <div class="form-group">
            <select id="videoCount">
                <option value="10">최근 10개 영상</option>
                <option value="20">최근 20개 영상</option>
                <option value="50">최근 50개 영상</option>
            </select>
        </div>
        <button type="submit">분석 시작</button>
    </form>
    
    <div id="loading">분석 중입니다... 잠시만 기다려주세요.</div>
    <div id="results" style="display:none;"></div>
    
    <script>
        async function analyzeChannel(event) {
            event.preventDefault();
            console.log('분석 시작 버튼 클릭됨');
            
            const channelInput = document.getElementById('channelInput').value.trim();
            const videoCount = document.getElementById('videoCount').value;
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            if (!channelInput) {
                alert('채널 정보를 입력해주세요.');
                return;
            }
            
            loading.style.display = 'block';
            results.style.display = 'none';
            
            try {
                console.log('서버에 요청 전송 중...');
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        channel_query: channelInput,
                        max_videos: parseInt(videoCount)
                    })
                });
                
                console.log('서버 응답 받음:', response.status);
                const data = await response.json();
                console.log('응답 데이터:', data);
                
                if (data.error) {
                    results.innerHTML = '<h3>오류</h3><p>' + data.error + '</p>';
                } else {
                    results.innerHTML = '<h3>분석 결과</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                }
                
                results.style.display = 'block';
                
            } catch (error) {
                console.error('오류:', error);
                results.innerHTML = '<h3>오류</h3><p>서버 연결 실패: ' + error.message + '</p>';
                results.style.display = 'block';
            }
            
            loading.style.display = 'none';
        }
    </script>
</body>
</html>'''

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        channel_query = data.get('channel_query', '')
        max_videos = data.get('max_videos', 10)
        
        print(f"분석 요청 받음: {channel_query}, 영상 수: {max_videos}")
        
        # 채널 ID 찾기
        channel_id = None
        if 'youtube.com' in channel_query or 'youtu.be' in channel_query:
            # URL에서 채널 ID 추출
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
            # 채널명으로 검색
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
        
        return jsonify({
            'channel_id': channel_id,
            'channel_name': channel_info['snippet']['title'],
            'subscriber_count': channel_info['statistics']['subscriberCount'],
            'view_count': channel_info['statistics']['viewCount'],
            'video_count': channel_info['statistics']['videoCount'],
            'description': channel_info['snippet']['description'][:200] + '...' if len(channel_info['snippet']['description']) > 200 else channel_info['snippet']['description']
        })
        
    except HttpError as e:
        print(f"YouTube API 오류: {e}")
        return jsonify({'error': f'YouTube API 오류: {e}'})
    except Exception as e:
        print(f"서버 오류: {e}")
        return jsonify({'error': f'서버 오류: {e}'})

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube 채널 분석기 - 간단 버전")
    print("=" * 60)
    print("주소: http://localhost:8081")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=8081)