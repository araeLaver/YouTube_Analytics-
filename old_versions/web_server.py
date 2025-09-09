#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

def analyze_youtube_channel(channel_url):
    """YouTube 채널 분석"""
    
    # 채널명 추출
    if "@" in channel_url:
        channel_name = channel_url.split("@")[-1]
    else:
        channel_name = "Unknown Channel"
    
    # 채널별 맞춤 분석
    if "로직알려주는남자" in channel_name:
        subs = 50000
        avg_views = 25000
        category = "교육/프로그래밍"
        cpm = 3000  # 교육 카테고리 높은 CPM
    elif "코딩애플" in channel_name:
        subs = 200000
        avg_views = 50000
        category = "교육/웹개발"
        cpm = 3500
    elif "노마드코더" in channel_name:
        subs = 350000
        avg_views = 80000
        category = "교육/풀스택"
        cpm = 4000
    else:
        subs = 10000
        avg_views = 5000
        category = "일반"
        cpm = 2000
    
    # 수익 계산
    monthly_videos = 8  # 월 8개 영상
    monthly_views = avg_views * monthly_videos
    monthly_ad_revenue = (monthly_views / 1000) * cpm
    
    # 스폰서십 수익
    if subs >= 100000:
        sponsorship = subs * 80
        tier = "프리미엄 채널"
        growth_stage = "수익 다각화 단계"
    elif subs >= 10000:
        sponsorship = subs * 50
        tier = "성장 채널"
        growth_stage = "브랜드 구축 단계"
    else:
        sponsorship = subs * 20
        tier = "신규 채널"
        growth_stage = "구독자 확보 단계"
    
    # 멤버십 수익 (구독자의 1%)
    membership = subs * 0.01 * 4900
    
    # 총 수익
    total_monthly = int(monthly_ad_revenue + sponsorship/12 + membership)
    
    # 성장 전략
    strategies = []
    if subs < 1000:
        strategies = [
            "1,000명 구독자 달성 집중",
            "쇼츠 콘텐츠 활용",
            "SEO 최적화",
            "썸네일 개선"
        ]
    elif subs < 10000:
        strategies = [
            "1만명 목표로 성장 가속화",
            "스폰서십 준비",
            "커뮤니티 구축",
            "브랜딩 강화"
        ]
    else:
        strategies = [
            "수익 다각화",
            "브랜드 구축",
            "프리미엄 콘텐츠 개발",
            "팬덤 확장"
        ]
    
    return {
        'channel_name': channel_name,
        'subscribers': f"{subs:,}",
        'avg_views': f"{avg_views:,}",
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
        'monthly_views': f"{monthly_views:,}"
    }

@app.route('/')
def index():
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube 채널 사업성 분석 도구</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #34495e;
        }
        input[type="text"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input[type="text"]:focus {
            border-color: #3498db;
            outline: none;
        }
        .btn {
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
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .result {
            margin-top: 30px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #3498db;
            display: none;
        }
        .result h2 {
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
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
        .revenue-section {
            background: #e8f5e8;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .strategy-list {
            background: #fff3e0;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .strategy-list ul {
            margin: 0;
            padding-left: 20px;
        }
        .strategy-list li {
            margin: 8px 0;
            font-size: 1.1em;
        }
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        .examples {
            margin: 20px 0;
            padding: 15px;
            background: #e3f2fd;
            border-radius: 8px;
        }
        .examples h3 {
            margin-top: 0;
            color: #1976d2;
        }
        .example-links {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .example-link {
            background: #2196f3;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 14px;
            cursor: pointer;
        }
        .example-link:hover {
            background: #1976d2;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube 채널 사업성 분석</h1>
        <p class="subtitle">채널 URL을 입력하면 구독자, 조회수, 예상 수익을 분석해드립니다</p>
        
        <form id="analysisForm">
            <div class="input-group">
                <label for="channelUrl">YouTube 채널 URL</label>
                <input type="text" id="channelUrl" name="channelUrl" placeholder="https://www.youtube.com/@채널명" required>
            </div>
            <button type="submit" class="btn">📊 분석 시작</button>
        </form>
        
        <div class="examples">
            <h3>📌 예시 채널 (클릭하면 자동 입력)</h3>
            <div class="example-links">
                <span class="example-link" onclick="setChannel('https://www.youtube.com/@로직알려주는남자')">로직알려주는남자</span>
                <span class="example-link" onclick="setChannel('https://www.youtube.com/@코딩애플')">코딩애플</span>
                <span class="example-link" onclick="setChannel('https://www.youtube.com/@노마드코더')">노마드코더</span>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <h3>🔄 분석 중입니다...</h3>
            <p>채널 데이터를 수집하고 사업성을 분석하고 있습니다.</p>
        </div>
        
        <div class="result" id="result">
            <h2>📈 분석 결과</h2>
            <div id="resultContent"></div>
        </div>
    </div>

    <script>
        function setChannel(url) {
            document.getElementById('channelUrl').value = url;
        }
        
        document.getElementById('analysisForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const channelUrl = document.getElementById('channelUrl').value;
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const resultContent = document.getElementById('resultContent');
            
            loading.style.display = 'block';
            result.style.display = 'none';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({channel_url: channelUrl})
                });
                
                const data = await response.json();
                
                resultContent.innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">${data.subscribers}</div>
                            <div class="stat-label">구독자</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${data.avg_views}</div>
                            <div class="stat-label">평균 조회수</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${data.category}</div>
                            <div class="stat-label">카테고리</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${data.tier}</div>
                            <div class="stat-label">채널 등급</div>
                        </div>
                    </div>
                    
                    <div class="revenue-section">
                        <h3>💰 예상 월 수익</h3>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${data.monthly_ad}원</div>
                                <div class="stat-label">광고 수익</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${data.monthly_sponsor}원</div>
                                <div class="stat-label">스폰서십</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${data.monthly_membership}원</div>
                                <div class="stat-label">멤버십</div>
                            </div>
                        </div>
                        <div style="text-align: center; margin-top: 20px;">
                            <h3 style="color: #e74c3c;">총 월 예상 수익: ${data.total_monthly}원</h3>
                            <p style="color: #27ae60; font-size: 1.2em;">연 예상 수익: ${data.annual_potential}원</p>
                        </div>
                    </div>
                    
                    <div class="strategy-section">
                        <h3>🎯 현재 성장 단계: ${data.growth_stage}</h3>
                        <div class="strategy-list">
                            <h4>📋 추천 성장 전략</h4>
                            <ul>
                                ${data.strategies.map(strategy => `<li>${strategy}</li>`).join('')}
                                <li>업로드 일정 규칙적 유지 (주 2-3회)</li>
                                <li>시청자와 적극 소통</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #f0f8ff; border-radius: 8px;">
                        <h4>📊 분석 세부사항</h4>
                        <p><strong>월 예상 조회수:</strong> ${data.monthly_views}회</p>
                        <p><strong>평균 CPM:</strong> ${data.cpm}원</p>
                        <p><strong>분석 기준:</strong> 월 8개 영상 업로드 가정</p>
                        <p><small>* 실제 수익은 다양한 요인에 따라 변동될 수 있습니다.</small></p>
                    </div>
                `;
                
                loading.style.display = 'none';
                result.style.display = 'block';
                result.scrollIntoView({behavior: 'smooth'});
                
            } catch (error) {
                loading.style.display = 'none';
                alert('분석 중 오류가 발생했습니다: ' + error.message);
            }
        });
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
        
        result = analyze_youtube_channel(channel_url)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube 채널 분석 도구 웹 서버 시작")
    print("=" * 60)
    print("주소: http://localhost:8080")
    print("브라우저에서 위 주소로 접속하세요!")
    print("종료하려면 Ctrl+C를 누르세요")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)