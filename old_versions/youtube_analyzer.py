import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import re

@dataclass
class VideoMetrics:
    title: str
    views: int
    likes: int
    comments: int
    duration: str
    upload_date: str
    thumbnail_url: str
    engagement_rate: float

@dataclass
class ChannelAnalysis:
    channel_name: str
    subscriber_count: int
    total_views: int
    video_count: int
    avg_views_per_video: float
    upload_frequency: str
    content_categories: List[str]
    estimated_monthly_revenue: tuple

class YouTubeAnalyzer:
    def __init__(self):
        self.revenue_factors = {
            'cpm_range': (1000, 7000),  # KRW per 1000 views
            'sponsorship_multiplier': 2.5,
            'membership_conversion': 0.02,
            'membership_fee': 4900  # KRW
        }
    
    def analyze_channel_type(self, channel_info: Dict) -> str:
        """채널 타입 분석 (교육, 엔터테인먼트, 리뷰 등)"""
        keywords = {
            '교육': ['강의', '튜토리얼', '설명', '알려', '배우', '공부', '로직'],
            '엔터테인먼트': ['웃긴', '재밌는', '몰카', '리액션'],
            '게임': ['게임', '플레이', '공략'],
            '리뷰': ['리뷰', '개봉기', '사용기'],
            'VLOG': ['일상', '브이로그', 'vlog'],
            '먹방': ['먹방', '맛집', '요리']
        }
        
        # 제목과 설명에서 키워드 분석
        content_type = '일반'
        max_count = 0
        
        for category, words in keywords.items():
            count = sum(1 for word in words if word in channel_info.get('description', '').lower())
            if count > max_count:
                max_count = count
                content_type = category
        
        return content_type
    
    def calculate_engagement_rate(self, views: int, likes: int, comments: int) -> float:
        """참여율 계산"""
        if views == 0:
            return 0
        return ((likes + comments) / views) * 100
    
    def estimate_revenue(self, monthly_views: int, subscriber_count: int, engagement_rate: float) -> Dict:
        """예상 수익 계산"""
        # 광고 수익
        avg_cpm = sum(self.revenue_factors['cpm_range']) / 2
        ad_revenue = (monthly_views / 1000) * avg_cpm
        
        # 스폰서십 예상 수익 (참여율이 높을수록 증가)
        if subscriber_count > 10000 and engagement_rate > 3:
            sponsorship = ad_revenue * self.revenue_factors['sponsorship_multiplier']
        else:
            sponsorship = 0
        
        # 멤버십 수익
        if subscriber_count > 1000:
            members = subscriber_count * self.revenue_factors['membership_conversion']
            membership_revenue = members * self.revenue_factors['membership_fee']
        else:
            membership_revenue = 0
        
        return {
            'ad_revenue': int(ad_revenue),
            'sponsorship': int(sponsorship),
            'membership': int(membership_revenue),
            'total': int(ad_revenue + sponsorship + membership_revenue),
            'breakdown': {
                '광고 수익': f"{int(ad_revenue):,}원",
                '예상 스폰서십': f"{int(sponsorship):,}원",
                '멤버십 수익': f"{int(membership_revenue):,}원"
            }
        }
    
    def analyze_upload_pattern(self, upload_dates: List[str]) -> Dict:
        """업로드 패턴 분석"""
        if not upload_dates:
            return {'frequency': '데이터 없음', 'consistency': 0}
        
        dates = [datetime.strptime(date, '%Y-%m-%d') for date in upload_dates]
        dates.sort()
        
        # 업로드 간격 계산
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        
        if not intervals:
            return {'frequency': '단일 업로드', 'consistency': 0}
        
        avg_interval = sum(intervals) / len(intervals)
        
        # 빈도 판단
        if avg_interval <= 1:
            frequency = '매일'
        elif avg_interval <= 3:
            frequency = '주 2-3회'
        elif avg_interval <= 7:
            frequency = '주 1회'
        elif avg_interval <= 14:
            frequency = '격주'
        else:
            frequency = '월 1-2회'
        
        # 일관성 점수 (0-100)
        std_dev = pd.Series(intervals).std()
        consistency = max(0, 100 - (std_dev * 10))
        
        return {
            'frequency': frequency,
            'consistency': round(consistency, 1),
            'avg_interval_days': round(avg_interval, 1)
        }
    
    def generate_content_strategy(self, channel_type: str, current_metrics: Dict) -> List[str]:
        """콘텐츠 전략 제안"""
        strategies = []
        
        # 기본 전략
        base_strategies = {
            '교육': [
                "시리즈물 제작으로 구독자 유지율 향상",
                "Q&A 콘텐츠로 커뮤니티 참여 유도",
                "단계별 난이도 구성으로 타겟층 확대",
                "실습 자료 제공으로 부가가치 창출"
            ],
            '엔터테인먼트': [
                "트렌드 반영 콘텐츠 빠른 제작",
                "시청자 참여 이벤트 정기 개최",
                "콜라보레이션으로 새로운 시청자 유입",
                "쇼츠 활용한 바이럴 마케팅"
            ]
        }
        
        strategies.extend(base_strategies.get(channel_type, [
            "일관된 업로드 스케줄 유지",
            "썸네일과 제목 최적화",
            "커뮤니티 탭 적극 활용",
            "분석 데이터 기반 콘텐츠 개선"
        ]))
        
        # 지표 기반 추가 전략
        if current_metrics.get('engagement_rate', 0) < 5:
            strategies.append("CTA(Call-to-Action) 강화로 참여율 향상")
        
        if current_metrics.get('upload_consistency', 0) < 70:
            strategies.append("콘텐츠 뱅크 구축으로 업로드 일정 안정화")
        
        return strategies
    
    def create_growth_roadmap(self, current_state: Dict, target_months: int = 6) -> Dict:
        """성장 로드맵 생성"""
        roadmap = {}
        current_subs = current_state.get('subscribers', 1000)
        growth_rate = 1.15  # 월 15% 성장 목표
        
        for month in range(1, target_months + 1):
            projected_subs = int(current_subs * (growth_rate ** month))
            
            milestones = []
            if month == 1:
                milestones = [
                    "채널 아트와 소개 최적화",
                    "업로드 일정 수립",
                    "키워드 리서치 및 SEO 최적화"
                ]
            elif month <= 3:
                milestones = [
                    "콘텐츠 품질 개선",
                    "커뮤니티 구축 시작",
                    "분석 도구 활용 시작"
                ]
            elif month <= 6:
                milestones = [
                    "수익화 조건 달성",
                    "스폰서십 협상 시작",
                    "콘텐츠 다각화"
                ]
            
            roadmap[f"{month}개월차"] = {
                'target_subscribers': projected_subs,
                'milestones': milestones,
                'focus_area': self._get_focus_area(month)
            }
        
        return roadmap
    
    def _get_focus_area(self, month: int) -> str:
        """월별 집중 영역"""
        focus_areas = {
            1: "기초 설정 및 브랜딩",
            2: "콘텐츠 품질 향상",
            3: "SEO 및 검색 최적화",
            4: "커뮤니티 활성화",
            5: "수익화 준비",
            6: "성장 가속화"
        }
        return focus_areas.get(month, "지속적 개선")
    
    def competitor_analysis(self, competitors: List[Dict]) -> pd.DataFrame:
        """경쟁 채널 분석"""
        df = pd.DataFrame(competitors)
        
        # 벤치마크 지표 계산
        df['efficiency_score'] = (df['avg_views'] / df['subscribers']) * 100
        df['growth_potential'] = df['engagement_rate'] * df['upload_frequency_score']
        
        return df.sort_values('efficiency_score', ascending=False)
    
    def generate_report(self, analysis_data: Dict) -> str:
        """종합 리포트 생성"""
        report = f"""
═══════════════════════════════════════════════════════════════
                    YouTube 채널 분석 리포트
═══════════════════════════════════════════════════════════════

📊 채널 개요
───────────────────────────────────────────────────────────────
채널명: {analysis_data.get('channel_name', '분석 대상 채널')}
채널 유형: {analysis_data.get('channel_type', '일반')}
구독자: {analysis_data.get('subscribers', 0):,}명
총 조회수: {analysis_data.get('total_views', 0):,}회
평균 조회수: {analysis_data.get('avg_views', 0):,}회/영상

💰 예상 월 수익
───────────────────────────────────────────────────────────────
총 예상 수익: {analysis_data.get('revenue', {}).get('total', 0):,}원
- 광고 수익: {analysis_data.get('revenue', {}).get('ad_revenue', 0):,}원
- 스폰서십: {analysis_data.get('revenue', {}).get('sponsorship', 0):,}원
- 멤버십: {analysis_data.get('revenue', {}).get('membership', 0):,}원

📈 성장 지표
───────────────────────────────────────────────────────────────
참여율: {analysis_data.get('engagement_rate', 0):.2f}%
업로드 빈도: {analysis_data.get('upload_frequency', '알 수 없음')}
일관성 점수: {analysis_data.get('consistency_score', 0):.1f}/100

🎯 추천 전략
───────────────────────────────────────────────────────────────
"""
        
        strategies = analysis_data.get('strategies', [])
        for i, strategy in enumerate(strategies, 1):
            report += f"{i}. {strategy}\n"
        
        report += """
🗓️ 6개월 성장 로드맵
───────────────────────────────────────────────────────────────
"""
        roadmap = analysis_data.get('roadmap', {})
        for period, details in roadmap.items():
            report += f"\n【{period}】\n"
            report += f"목표 구독자: {details['target_subscribers']:,}명\n"
            report += f"집중 영역: {details['focus_area']}\n"
            report += "주요 과제:\n"
            for task in details['milestones']:
                report += f"  • {task}\n"
        
        report += """
═══════════════════════════════════════════════════════════════
"""
        return report

# 실행 예제
def main():
    analyzer = YouTubeAnalyzer()
    
    # 샘플 데이터 (실제로는 YouTube API나 웹 스크래핑으로 수집)
    sample_data = {
        'channel_name': '로직알려주는남자',
        'channel_type': '교육',
        'subscribers': 50000,
        'total_views': 5000000,
        'avg_views': 25000,
        'monthly_views': 500000,
        'engagement_rate': 4.5,
        'upload_frequency': '주 2-3회',
        'consistency_score': 85.0
    }
    
    # 수익 분석
    revenue = analyzer.estimate_revenue(
        sample_data['monthly_views'],
        sample_data['subscribers'],
        sample_data['engagement_rate']
    )
    
    # 전략 생성
    strategies = analyzer.generate_content_strategy(
        sample_data['channel_type'],
        sample_data
    )
    
    # 로드맵 생성
    roadmap = analyzer.generate_growth_roadmap(
        {'subscribers': sample_data['subscribers']},
        6
    )
    
    # 종합 분석
    analysis_data = {
        **sample_data,
        'revenue': revenue,
        'strategies': strategies,
        'roadmap': roadmap
    }
    
    # 리포트 출력
    report = analyzer.generate_report(analysis_data)
    print(report)
    
    # 리포트 저장
    with open('youtube_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("분석이 완료되었습니다. 'youtube_analysis_report.txt' 파일을 확인하세요.")

if __name__ == "__main__":
    main()