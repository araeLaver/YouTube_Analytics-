#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube Data API 직접 테스트
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
from urllib.parse import unquote

API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

def test_youtube_api():
    """API 직접 테스트"""
    
    print("=" * 50)
    print("YouTube Data API 테스트")
    print("=" * 50)
    
    try:
        # YouTube 서비스 생성
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        
        print("✓ API 연결 성공")
        
        # 채널 검색 테스트
        channel_url = "https://www.youtube.com/@로직알려주는남자"
        print(f"분석 채널: {channel_url}")
        
        # 채널명으로 검색
        search_response = youtube.search().list(
            q="로직알려주는남자",
            part='snippet',
            type='channel',
            maxResults=5
        ).execute()
        
        if search_response['items']:
            channel_id = search_response['items'][0]['snippet']['channelId']
            channel_title = search_response['items'][0]['snippet']['title']
            
            print(f"✓ 채널 발견: {channel_title}")
            print(f"✓ 채널 ID: {channel_id}")
            
            # 채널 상세 정보
            channel_response = youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            ).execute()
            
            if channel_response['items']:
                channel = channel_response['items'][0]
                stats = channel['statistics']
                
                print("\n📊 실제 채널 데이터:")
                print(f"구독자: {int(stats.get('subscriberCount', 0)):,}명")
                print(f"총 조회수: {int(stats.get('viewCount', 0)):,}회")
                print(f"동영상 수: {int(stats.get('videoCount', 0)):,}개")
                print(f"채널명: {channel['snippet']['title']}")
                print(f"설명: {channel['snippet']['description'][:100]}...")
                
                # 수익 추정
                subscribers = int(stats.get('subscriberCount', 0))
                avg_views = subscribers * 0.3  # 구독자의 30% 추정
                
                monthly_videos = 8
                monthly_views = avg_views * monthly_videos
                cpm = 3000  # 교육 채널
                monthly_ad_revenue = (monthly_views / 1000) * cpm
                
                if subscribers >= 10000:
                    sponsorship = subscribers * 50
                    tier = "마이크로 인플루언서"
                else:
                    sponsorship = 0
                    tier = "성장 크리에이터"
                
                membership = subscribers * 0.01 * 4900 if subscribers >= 1000 else 0
                total_monthly = int(monthly_ad_revenue + sponsorship/12 + membership)
                
                print(f"\n💰 수익 분석:")
                print(f"채널 등급: {tier}")
                print(f"월 광고 수익: {int(monthly_ad_revenue):,}원")
                print(f"월 스폰서십: {int(sponsorship/12):,}원")
                print(f"월 멤버십: {int(membership):,}원")
                print(f"총 월 예상 수익: {total_monthly:,}원")
                print(f"연 예상 수익: {total_monthly * 12:,}원")
                
                return True
            else:
                print("❌ 채널 상세 정보 없음")
        else:
            print("❌ 채널을 찾을 수 없음")
            
        return False
        
    except HttpError as e:
        print(f"❌ API 오류: {e}")
        if "quotaExceeded" in str(e):
            print("API 할당량 초과. 내일 다시 시도하세요.")
        elif "keyInvalid" in str(e):
            print("API 키가 잘못되었습니다.")
        return False
        
    except Exception as e:
        print(f"❌ 일반 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_youtube_api()
    
    if success:
        print("\n🎉 API 테스트 성공!")
        print("웹 서버에서도 정상 작동할 것입니다.")
    else:
        print("\n💥 API 테스트 실패")
        print("설정을 다시 확인해주세요.")