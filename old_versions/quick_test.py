# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from googleapiclient.discovery import build

app = Flask(__name__)
API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

def search_channel(query):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        response = youtube.search().list(
            q=query,
            part='snippet',
            type='channel',
            maxResults=1
        ).execute()
        
        if response['items']:
            return response['items'][0]['snippet']['channelId']
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def index():
    return '''
    <h1>YouTube 채널 검색 테스트</h1>
    <button onclick="test()">테스트</button>
    <div id="result"></div>
    
    <script>
    async function test() {
        try {
            const response = await fetch('/test');
            const data = await response.json();
            document.getElementById('result').innerHTML = 
                '<p>결과: ' + JSON.stringify(data) + '</p>';
        } catch (e) {
            document.getElementById('result').innerHTML = '<p>오류: ' + e.message + '</p>';
        }
    }
    </script>
    '''

@app.route('/test')
def test():
    channel_id = search_channel("로직알려주는남자")
    return jsonify({'channel_id': channel_id, 'status': 'ok' if channel_id else 'fail'})

if __name__ == '__main__':
    print("Quick Test Server: http://localhost:9000")
    app.run(debug=True, host='0.0.0.0', port=9000)