#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube 채널 종합 분석 도구
- 채널 콘텐츠 수집
- 사업성 분석
- 종합 리포트 생성
"""

import sys
import os
from typing import Dict
from youtube_channel_scraper import YouTubeChannelScraper
from content_analyzer import YouTubeContentAnalyzer
import argparse
from datetime import datetime

class YouTubeBusinessAnalyzer:
    """YouTube 채널 사업성 분석 통합 도구"""
    
    def __init__(self, api_key=None):
        self.scraper = YouTubeChannelScraper(api_key)
        self.analyzer = YouTubeContentAnalyzer()
        
    def analyze_channel(self, channel_url: str, max_videos: int = 50):
        """채널 종합 분석 실행"""
        print("=" * 80)
        print("YouTube 채널 사업성 분석 도구")
        print("=" * 80)
        print(f"분석 대상: {channel_url}")
        print(f"분석 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 1: 채널 기본 정보 수집
        print("📊 1단계: 채널 정보 수집 중...")
        channel_id = self.scraper.extract_channel_id(channel_url)
        
        if not channel_id:
            # URL이 채널 ID가 아닌 경우, 직접 스크래핑 시도
            channel_data = self.scraper.get_channel_info_via_scraping(channel_url)
            if not channel_data:
                print("❌ 유효한 YouTube 채널을 찾을 수 없습니다.")
                return None
            channel_data['channel_url'] = channel_url
        else:
            channel_data = self.scraper.get_channel_info_via_api(channel_id)
            if not channel_data:
                print("❌ 채널 정보를 가져올 수 없습니다.")
                return None
                
        print(f"✅ 채널명: {channel_data.get('channel_name', 'Unknown')}")
        print(f"✅ 구독자: {channel_data.get('subscriber_count', 0):,}명")
        print()
        
        # Step 2: 최근 동영상 수집
        print("🎬 2단계: 최근 동영상 분석 중...")
        videos = channel_data.get('recent_videos', [])
        
        if not videos:
            print("⚠️  동영상 데이터를 가져올 수 없어 기본 분석만 실행합니다.")
            videos = []
        else:
            print(f"✅ {len(videos)}개 동영상 데이터 수집 완료")
        print()
        
        # Step 3: 콘텐츠 패턴 분석
        print("📈 3단계: 콘텐츠 패턴 분석 중...")
        if videos:
            content_patterns = self.scraper.analyze_content_pattern(videos)
            print(f"✅ 평균 조회수: {content_patterns.get('average_views', 0):,}회")
            print(f"✅ 참여율: {content_patterns.get('engagement_rate', 0):.2f}%")
        else:
            content_patterns = {}
        print()
        
        # Step 4: 종합 사업성 분석
        print("💰 4단계: 사업성 분석 중...")
        if videos:
            business_report = self.analyzer.generate_comprehensive_report(channel_data, videos)
        else:
            business_report = self._generate_basic_report(channel_data)
        print("✅ 사업성 분석 완료")
        print()
        
        # Step 5: 결과 저장
        print("💾 5단계: 분석 결과 저장 중...")
        channel_name = channel_data.get('channel_name', 'unknown_channel')
        safe_name = "".join(c for c in channel_name if c.isalnum() or c in (' ', '_')).rstrip()
        
        # 리포트 파일 저장
        report_filename = f"youtube_analysis_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(business_report)
        
        print(f"✅ 분석 리포트 저장: {report_filename}")
        print()
        
        # 결과 화면 출력
        print("📋 분석 결과 미리보기:")
        print("-" * 80)
        print(business_report[:2000])  # 처음 2000자만 미리보기
        if len(business_report) > 2000:
            print(f"\n... (총 {len(business_report):,}자, 전체 내용은 파일 참조)")
        print("-" * 80)
        
        return {
            'channel_data': channel_data,
            'videos': videos,
            'content_patterns': content_patterns,
            'report': business_report,
            'report_file': report_filename
        }
    
    def _generate_basic_report(self, channel_data: Dict) -> str:
        """동영상 데이터 없을 때 기본 리포트"""
        subscribers = channel_data.get('subscriber_count', 0)
        total_views = channel_data.get('total_views', 0)
        
        # 기본 수익 추정
        est_monthly_revenue = 0
        if subscribers >= 1000:
            # 월 평균 조회수 추정 (구독자 * 0.1 * 8회)
            est_monthly_views = subscribers * 0.1 * 8
            est_monthly_revenue = (est_monthly_views / 1000) * 2000  # CPM 2000원
        
        report = f"""
════════════════════════════════════════════════════════════════════════
                    YouTube 채널 기본 사업성 분석
════════════════════════════════════════════════════════════════════════

📺 채널 정보
────────────────────────────────────────────────────────────────────────
채널명: {channel_data.get('channel_name', 'Unknown')}
구독자: {subscribers:,}명
총 조회수: {total_views:,}회
총 동영상: {channel_data.get('video_count', 0)}개

💰 예상 수익 (기본 추정)
────────────────────────────────────────────────────────────────────────
월 예상 광고 수익: {int(est_monthly_revenue):,}원
수익화 상태: {"가능" if subscribers >= 1000 else "불가능 (1,000명 미만)"}

📊 시장 포지션
────────────────────────────────────────────────────────────────────────"""
        
        if subscribers >= 1000000:
            report += "\n등급: 메가 인플루언서 (100만+명)"
            report += "\n기회: 프리미엄 브랜드 협업, 자체 브랜드 론칭"
        elif subscribers >= 100000:
            report += "\n등급: 매크로 인플루언서 (10-100만명)"  
            report += "\n기회: 대형 브랜드 스폰서십, 자체 상품 개발"
        elif subscribers >= 10000:
            report += "\n등급: 마이크로 인플루언서 (1-10만명)"
            report += "\n기회: 중소 브랜드 협업, 제휴 마케팅"
        elif subscribers >= 1000:
            report += "\n등급: 나노 인플루언서 (1천-1만명)"
            report += "\n기회: 로컬 브랜드 협업, 기본 수익화"
        else:
            report += "\n등급: 신규 크리에이터 (1천명 미만)"
            report += "\n우선순위: 1,000명 구독자 달성 필요"
        
        report += f"""

⚠️ 제한사항
────────────────────────────────────────────────────────────────────────
• 상세 동영상 데이터 수집 불가능
• 정확한 성과 분석을 위해서는 YouTube API 키 필요
• 또는 채널의 최근 동영상 목록에 접근 권한 필요

📞 추가 분석 방법
────────────────────────────────────────────────────────────────────────
1. YouTube API 키 발급 후 재분석
2. Social Blade 등 외부 도구 활용
3. 채널 소유자의 YouTube Analytics 데이터 확인

════════════════════════════════════════════════════════════════════════
분석일: {datetime.now().strftime('%Y년 %m월 %d일')}
════════════════════════════════════════════════════════════════════════
"""
        
        return report

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='YouTube 채널 사업성 분석 도구')
    parser.add_argument('channel_url', help='분석할 YouTube 채널 URL')
    parser.add_argument('--api-key', help='YouTube API 키 (선택사항)')
    parser.add_argument('--max-videos', type=int, default=50, help='분석할 최대 동영상 수')
    
    # 인자가 없으면 대화형 모드
    if len(sys.argv) == 1:
        print("=" * 80)
        print("YouTube 채널 사업성 분석 도구")
        print("=" * 80)
        
        # 채널 URL 입력
        channel_url = input("분석할 YouTube 채널 URL을 입력하세요: ").strip()
        if not channel_url:
            print("❌ 유효한 URL을 입력해주세요.")
            return
        
        # API 키 입력 (선택사항)
        api_key = input("YouTube API 키 (없으면 Enter): ").strip()
        if not api_key:
            api_key = None
        
        max_videos = 50
        
    else:
        args = parser.parse_args()
        channel_url = args.channel_url
        api_key = args.api_key
        max_videos = args.max_videos
    
    # 분석 실행
    analyzer = YouTubeBusinessAnalyzer(api_key)
    
    try:
        result = analyzer.analyze_channel(channel_url, max_videos)
        
        if result:
            print("\n🎉 분석이 성공적으로 완료되었습니다!")
            print(f"📄 상세 리포트: {result['report_file']}")
            
            # 간단한 요약 출력
            channel_data = result['channel_data']
            print(f"\n📊 요약:")
            print(f"   채널명: {channel_data.get('channel_name')}")
            print(f"   구독자: {channel_data.get('subscriber_count', 0):,}명")
            print(f"   분석 영상: {len(result['videos'])}개")
        else:
            print("\n❌ 분석에 실패했습니다.")
            
    except KeyboardInterrupt:
        print("\n\n분석이 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()