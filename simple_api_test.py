# -*- coding: utf-8 -*-
from googleapiclient.discovery import build

API_KEY = "AIzaSyB-QbLMxVL-RmGK9j21HkIGrg3bjRs871E"

def test_api():
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        
        # 채널 검색
        search_response = youtube.search().list(
            q="로직알려주는남자",
            part='snippet',
            type='channel',
            maxResults=1
        ).execute()
        
        if search_response['items']:
            channel_id = search_response['items'][0]['snippet']['channelId']
            print(f"채널 발견: {channel_id}")
            
            # 채널 상세 정보
            channel_response = youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            ).execute()
            
            if channel_response['items']:
                channel = channel_response['items'][0]
                stats = channel['statistics']
                
                print("=== 실제 채널 데이터 ===")
                print(f"채널명: {channel['snippet']['title']}")
                print(f"구독자: {int(stats.get('subscriberCount', 0)):,}명")
                print(f"총 조회수: {int(stats.get('viewCount', 0)):,}회")
                print(f"동영상 수: {int(stats.get('videoCount', 0)):,}개")
                
                # 간단한 수익 계산
                subs = int(stats.get('subscriberCount', 0))
                monthly_ad = (subs * 0.3 * 8 / 1000) * 3000  # 구독자*30%*8영상*CPM
                sponsorship = subs * 50 / 12  # 월 스폰서십
                
                print("=== 예상 월 수익 ===")
                print(f"광고 수익: {int(monthly_ad):,}원")
                print(f"스폰서십: {int(sponsorship):,}원")
                print(f"총 예상: {int(monthly_ad + sponsorship):,}원")
                
                return True
        else:
            print("채널을 찾을 수 없습니다")
            
    except Exception as e:
        print(f"오류: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    if success:
        print("\nAPI 테스트 성공!")
    else:
        print("\nAPI 테스트 실패")