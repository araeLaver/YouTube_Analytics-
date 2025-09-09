import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List
from datetime import datetime
import pandas as pd
from googleapiclient.discovery import build
import os

class YouTubeChannelScraper:
    """YouTube 채널 콘텐츠 수집 및 분석 도구"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        if api_key:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
        else:
            self.youtube = None
            
    def extract_channel_id(self, channel_url: str) -> str:
        """채널 URL에서 채널 ID 추출"""
        # 다양한 YouTube URL 형식 처리
        patterns = [
            r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'youtube\.com/c/([a-zA-Z0-9_-]+)',
            r'youtube\.com/@([a-zA-Z0-9_-]+)',
            r'youtube\.com/user/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, channel_url)
            if match:
                return match.group(1)
        
        return None
    
    def get_channel_info_via_api(self, channel_id: str) -> Dict:
        """YouTube API를 통한 채널 정보 수집"""
        if not self.youtube:
            return self.get_channel_info_via_scraping(channel_id)
        
        try:
            # 채널 기본 정보
            channel_response = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response['items']:
                return None
            
            channel_data = channel_response['items'][0]
            
            # 최근 동영상 목록
            videos = self.get_recent_videos(channel_id, max_results=50)
            
            return {
                'channel_id': channel_id,
                'channel_name': channel_data['snippet']['title'],
                'description': channel_data['snippet']['description'],
                'subscriber_count': int(channel_data['statistics'].get('subscriberCount', 0)),
                'total_views': int(channel_data['statistics'].get('viewCount', 0)),
                'video_count': int(channel_data['statistics'].get('videoCount', 0)),
                'created_date': channel_data['snippet']['publishedAt'],
                'country': channel_data['snippet'].get('country', 'Unknown'),
                'recent_videos': videos
            }
            
        except Exception as e:
            print(f"API 오류: {e}")
            return self.get_channel_info_via_scraping(channel_id)
    
    def get_channel_info_via_scraping(self, channel_url: str) -> Dict:
        """웹 스크래핑을 통한 채널 정보 수집 (API 키 없을 때)"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(channel_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # YouTube 페이지의 JSON 데이터 추출
            scripts = soup.find_all('script')
            channel_data = {}
            
            for script in scripts:
                if 'var ytInitialData' in script.text:
                    json_text = script.text.split('var ytInitialData = ')[1].split(';</script>')[0]
                    data = json.loads(json_text)
                    
                    # 채널 정보 파싱
                    header = data.get('header', {}).get('c4TabbedHeaderRenderer', {})
                    if header:
                        channel_data = {
                            'channel_name': header.get('title', ''),
                            'subscriber_count': self.parse_subscriber_count(header.get('subscriberCountText', {}).get('simpleText', '0')),
                            'video_count': self.extract_video_count(data),
                            'description': self.extract_description(data)
                        }
                    break
            
            return channel_data
            
        except Exception as e:
            print(f"스크래핑 오류: {e}")
            return {}
    
    def get_recent_videos(self, channel_id: str, max_results: int = 50) -> List[Dict]:
        """최근 업로드된 동영상 목록 가져오기"""
        if not self.youtube:
            return []
        
        try:
            # 채널의 업로드 재생목록 ID 가져오기
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # 재생목록에서 동영상 가져오기
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                ).execute()
                
                for item in playlist_response['items']:
                    video_id = item['snippet']['resourceId']['videoId']
                    video_details = self.get_video_details(video_id)
                    videos.append(video_details)
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return videos
            
        except Exception as e:
            print(f"동영상 목록 가져오기 오류: {e}")
            return []
    
    def get_video_details(self, video_id: str) -> Dict:
        """개별 동영상 상세 정보 가져오기"""
        if not self.youtube:
            return {}
        
        try:
            video_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            ).execute()
            
            if not video_response['items']:
                return {}
            
            video = video_response['items'][0]
            
            return {
                'video_id': video_id,
                'title': video['snippet']['title'],
                'description': video['snippet']['description'][:500],
                'published_date': video['snippet']['publishedAt'],
                'duration': self.parse_duration(video['contentDetails']['duration']),
                'view_count': int(video['statistics'].get('viewCount', 0)),
                'like_count': int(video['statistics'].get('likeCount', 0)),
                'comment_count': int(video['statistics'].get('commentCount', 0)),
                'tags': video['snippet'].get('tags', [])[:10],
                'category_id': video['snippet'].get('categoryId', ''),
                'thumbnail_url': video['snippet']['thumbnails']['high']['url']
            }
            
        except Exception as e:
            print(f"동영상 상세 정보 오류: {e}")
            return {}
    
    def parse_duration(self, duration: str) -> int:
        """ISO 8601 기간을 초 단위로 변환"""
        import isodate
        try:
            return int(isodate.parse_duration(duration).total_seconds())
        except:
            return 0
    
    def parse_subscriber_count(self, text: str) -> int:
        """구독자 수 텍스트를 숫자로 변환"""
        text = text.replace('subscribers', '').replace('구독자', '').strip()
        
        multipliers = {
            'K': 1000,
            'M': 1000000,
            '천': 1000,
            '만': 10000,
            '억': 100000000
        }
        
        for suffix, multiplier in multipliers.items():
            if suffix in text:
                number = float(re.findall(r'[\d.]+', text)[0])
                return int(number * multiplier)
        
        # 일반 숫자
        numbers = re.findall(r'\d+', text.replace(',', ''))
        return int(numbers[0]) if numbers else 0
    
    def extract_video_count(self, data: Dict) -> int:
        """YouTube 데이터에서 동영상 수 추출"""
        try:
            tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
            for tab in tabs:
                if 'tabRenderer' in tab:
                    if 'Videos' in tab['tabRenderer'].get('title', ''):
                        text = tab['tabRenderer'].get('content', {}).get('sectionListRenderer', {})
                        # 동영상 수 추출 로직
                        return 0  # 실제 구현 필요
        except:
            pass
        return 0
    
    def extract_description(self, data: Dict) -> str:
        """채널 설명 추출"""
        try:
            about_data = data.get('metadata', {}).get('channelMetadataRenderer', {})
            return about_data.get('description', '')
        except:
            return ''
    
    def analyze_content_pattern(self, videos: List[Dict]) -> Dict:
        """콘텐츠 패턴 분석"""
        if not videos:
            return {}
        
        df = pd.DataFrame(videos)
        
        # 업로드 패턴
        df['published_date'] = pd.to_datetime(df['published_date'])
        df['day_of_week'] = df['published_date'].dt.day_name()
        df['hour'] = df['published_date'].dt.hour
        
        # 콘텐츠 성과 분석
        avg_views = df['view_count'].mean()
        avg_likes = df['like_count'].mean()
        avg_comments = df['comment_count'].mean()
        
        # 인기 동영상 (상위 10%)
        top_10_percent = int(len(df) * 0.1) or 1
        top_videos = df.nlargest(top_10_percent, 'view_count')
        
        # 제목 키워드 분석
        all_titles = ' '.join(df['title'].tolist())
        common_words = self.extract_common_words(all_titles)
        
        # 최적 업로드 시간
        best_time = df.groupby('hour')['view_count'].mean().idxmax()
        best_day = df.groupby('day_of_week')['view_count'].mean().idxmax()
        
        # 동영상 길이 분석
        df['duration_minutes'] = df['duration'] / 60
        optimal_duration = df.loc[df['view_count'] > avg_views, 'duration_minutes'].median()
        
        return {
            'total_videos_analyzed': len(videos),
            'average_views': int(avg_views),
            'average_likes': int(avg_likes),
            'average_comments': int(avg_comments),
            'engagement_rate': (avg_likes + avg_comments) / avg_views * 100 if avg_views > 0 else 0,
            'top_videos': top_videos[['title', 'view_count', 'like_count']].to_dict('records'),
            'common_keywords': common_words[:10],
            'best_upload_time': f"{best_day} {best_time}:00",
            'optimal_video_duration': f"{optimal_duration:.1f} minutes",
            'upload_frequency': self.calculate_upload_frequency(df),
            'growth_trend': self.analyze_growth_trend(df)
        }
    
    def extract_common_words(self, text: str, min_length: int = 3) -> List[str]:
        """텍스트에서 자주 사용되는 단어 추출"""
        import collections
        
        # 불용어 제거
        stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 
                     'was', 'were', 'of', 'to', 'in', 'for', 'with', '의', '를', '을', '이', '가'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        words = [w for w in words if len(w) >= min_length and w not in stop_words]
        
        word_counts = collections.Counter(words)
        return [word for word, count in word_counts.most_common(20)]
    
    def calculate_upload_frequency(self, df: pd.DataFrame) -> str:
        """업로드 빈도 계산"""
        date_diff = (df['published_date'].max() - df['published_date'].min()).days
        if date_diff == 0:
            return "일일 업로드"
        
        videos_per_day = len(df) / date_diff
        
        if videos_per_day >= 1:
            return f"일 {videos_per_day:.1f}개"
        elif videos_per_day >= 0.3:
            return f"주 {videos_per_day * 7:.1f}개"
        else:
            return f"월 {videos_per_day * 30:.1f}개"
    
    def analyze_growth_trend(self, df: pd.DataFrame) -> str:
        """성장 트렌드 분석"""
        # 최근 10개 vs 이전 10개 비교
        if len(df) < 20:
            return "데이터 부족"
        
        recent = df.head(10)['view_count'].mean()
        older = df.iloc[10:20]['view_count'].mean()
        
        if older == 0:
            return "급성장"
        
        growth_rate = ((recent - older) / older) * 100
        
        if growth_rate > 50:
            return f"급성장 (↑{growth_rate:.0f}%)"
        elif growth_rate > 20:
            return f"성장중 (↑{growth_rate:.0f}%)"
        elif growth_rate > -20:
            return "안정적"
        else:
            return f"하락중 (↓{abs(growth_rate):.0f}%)"
    
    def generate_business_analysis(self, channel_data: Dict, content_analysis: Dict) -> str:
        """사업성 분석 리포트 생성"""
        report = f"""
================================================================================
                        YouTube 채널 사업성 분석 보고서
================================================================================

📺 채널 정보
--------------------------------------------------------------------------------
채널명: {channel_data.get('channel_name', 'Unknown')}
구독자: {channel_data.get('subscriber_count', 0):,}명
총 조회수: {channel_data.get('total_views', 0):,}회
동영상 수: {channel_data.get('video_count', 0):,}개
채널 생성일: {channel_data.get('created_date', 'Unknown')[:10]}

📊 콘텐츠 성과 분석
--------------------------------------------------------------------------------
평균 조회수: {content_analysis.get('average_views', 0):,}회
평균 좋아요: {content_analysis.get('average_likes', 0):,}개
평균 댓글: {content_analysis.get('average_comments', 0):,}개
참여율: {content_analysis.get('engagement_rate', 0):.2f}%
업로드 빈도: {content_analysis.get('upload_frequency', 'Unknown')}
성장 트렌드: {content_analysis.get('growth_trend', 'Unknown')}

🎯 콘텐츠 전략 분석
--------------------------------------------------------------------------------
최적 업로드 시간: {content_analysis.get('best_upload_time', 'Unknown')}
최적 동영상 길이: {content_analysis.get('optimal_video_duration', 'Unknown')}
주요 키워드: {', '.join(content_analysis.get('common_keywords', [])[:5])}

💰 예상 수익 분석
--------------------------------------------------------------------------------
"""
        
        # 수익 계산
        monthly_views = content_analysis.get('average_views', 0) * 8  # 월 8개 영상 가정
        cpm = 2000  # 평균 CPM (원)
        monthly_ad_revenue = (monthly_views / 1000) * cpm
        
        # 스폰서십 가능성
        subscribers = channel_data.get('subscriber_count', 0)
        if subscribers >= 100000:
            sponsorship = subscribers * 50  # 구독자당 50원
            sponsorship_tier = "프리미엄"
        elif subscribers >= 10000:
            sponsorship = subscribers * 30
            sponsorship_tier = "중급"
        else:
            sponsorship = subscribers * 10
            sponsorship_tier = "초급"
        
        report += f"""월 예상 광고 수익: {int(monthly_ad_revenue):,}원
월 예상 스폰서십 (1건): {int(sponsorship):,}원 ({sponsorship_tier})
총 월 예상 수익: {int(monthly_ad_revenue + sponsorship):,}원

🏆 인기 콘텐츠 TOP 3
--------------------------------------------------------------------------------"""
        
        top_videos = content_analysis.get('top_videos', [])[:3]
        for i, video in enumerate(top_videos, 1):
            report += f"""
{i}. {video['title']}
   조회수: {video['view_count']:,} | 좋아요: {video['like_count']:,}"""
        
        # 사업 기회 평가
        report += """

📈 사업 기회 평가
--------------------------------------------------------------------------------"""
        
        opportunities = []
        risks = []
        
        # 기회 분석
        if content_analysis.get('engagement_rate', 0) > 5:
            opportunities.append("높은 참여율 - 충성 고객층 보유")
        if 'growth' in content_analysis.get('growth_trend', '').lower():
            opportunities.append("성장 추세 - 확장 가능성 높음")
        if subscribers > 10000:
            opportunities.append("수익화 가능 - 다양한 수익원 활용 가능")
        
        # 리스크 분석
        if content_analysis.get('engagement_rate', 0) < 2:
            risks.append("낮은 참여율 - 콘텐츠 개선 필요")
        if '하락' in content_analysis.get('growth_trend', ''):
            risks.append("하락 추세 - 전략 재검토 필요")
        if subscribers < 1000:
            risks.append("수익화 미달 - 성장 전략 필요")
        
        report += f"""
✅ 기회 요인:
{chr(10).join([f'  • {opp}' for opp in opportunities]) if opportunities else '  • 추가 분석 필요'}

⚠️ 리스크 요인:
{chr(10).join([f'  • {risk}' for risk in risks]) if risks else '  • 특별한 리스크 없음'}

🎬 추천 전략
--------------------------------------------------------------------------------"""
        
        # 전략 추천
        if subscribers < 1000:
            report += """
1. 구독자 확보 집중
   - 쇼츠 콘텐츠 활용
   - 키워드 최적화
   - 썸네일 개선
"""
        elif subscribers < 10000:
            report += """
1. 성장 가속화
   - 업로드 빈도 증가
   - 시리즈물 제작
   - 커뮤니티 활성화
"""
        else:
            report += """
1. 수익 다각화
   - 스폰서십 적극 유치
   - 멤버십 도입
   - 굿즈/상품 개발
"""
        
        report += """
================================================================================
"""
        
        return report

# 사용 예제
def analyze_channel(channel_url: str, api_key: str = None):
    """채널 분석 실행"""
    scraper = YouTubeChannelScraper(api_key)
    
    print(f"채널 분석 시작: {channel_url}")
    
    # 채널 ID 추출
    channel_id = scraper.extract_channel_id(channel_url)
    if not channel_id:
        print("유효한 채널 URL이 아닙니다.")
        return
    
    # 채널 정보 수집
    if api_key:
        channel_data = scraper.get_channel_info_via_api(channel_id)
    else:
        channel_data = scraper.get_channel_info_via_scraping(channel_url)
    
    if not channel_data:
        print("채널 정보를 가져올 수 없습니다.")
        return
    
    # 콘텐츠 패턴 분석
    videos = channel_data.get('recent_videos', [])
    content_analysis = scraper.analyze_content_pattern(videos) if videos else {}
    
    # 사업성 분석 리포트 생성
    report = scraper.generate_business_analysis(channel_data, content_analysis)
    
    # 리포트 저장
    filename = f"channel_analysis_{channel_data.get('channel_name', 'unknown').replace(' ', '_')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n분석 결과가 '{filename}'에 저장되었습니다.")
    
    return channel_data, content_analysis

if __name__ == "__main__":
    # API 키가 있는 경우 (선택사항)
    # API_KEY = "YOUR_YOUTUBE_API_KEY"
    
    # API 키 없이 분석 (제한적)
    channel_url = "https://www.youtube.com/@로직알려주는남자"
    
    # 분석 실행
    analyze_channel(channel_url, api_key=None)