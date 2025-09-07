import json
from typing import Dict, List, Tuple
from datetime import datetime
import pandas as pd

class YouTubeRevenueOptimizer:
    """YouTube 수익 최적화 전략 분석기"""
    
    def __init__(self):
        self.monetization_requirements = {
            'watch_time': 4000,  # 시간 (지난 12개월)
            'subscribers': 1000,  # 구독자 수
            'shorts_views': 10000000  # 쇼츠 조회수 (90일)
        }
        
        self.revenue_streams = {
            'ads': {'min_requirement': 'monetization', 'potential': 'high'},
            'channel_membership': {'min_requirement': 1000, 'potential': 'medium'},
            'super_chat': {'min_requirement': 'monetization', 'potential': 'low'},
            'super_thanks': {'min_requirement': 'monetization', 'potential': 'low'},
            'shopping': {'min_requirement': 1000, 'potential': 'medium'},
            'brand_sponsorship': {'min_requirement': 10000, 'potential': 'very_high'},
            'affiliate': {'min_requirement': 0, 'potential': 'medium'}
        }
    
    def check_monetization_eligibility(self, channel_stats: Dict) -> Dict:
        """수익화 자격 확인"""
        eligible_streams = []
        not_eligible = []
        recommendations = []
        
        # 기본 수익화 조건 체크
        basic_monetization = (
            channel_stats.get('watch_time_hours', 0) >= self.monetization_requirements['watch_time'] and
            channel_stats.get('subscribers', 0) >= self.monetization_requirements['subscribers']
        )
        
        # 쇼츠 수익화 조건 체크
        shorts_monetization = (
            channel_stats.get('shorts_views_90days', 0) >= self.monetization_requirements['shorts_views'] and
            channel_stats.get('subscribers', 0) >= self.monetization_requirements['subscribers']
        )
        
        current_subs = channel_stats.get('subscribers', 0)
        
        for stream, requirements in self.revenue_streams.items():
            min_req = requirements['min_requirement']
            
            if min_req == 'monetization':
                if basic_monetization or shorts_monetization:
                    eligible_streams.append(stream)
                else:
                    not_eligible.append(stream)
            elif isinstance(min_req, int):
                if current_subs >= min_req:
                    eligible_streams.append(stream)
                else:
                    not_eligible.append(stream)
                    if min_req > 0:
                        recommendations.append(
                            f"{stream}: {min_req - current_subs:,}명 더 필요"
                        )
            else:
                eligible_streams.append(stream)
        
        return {
            'eligible': eligible_streams,
            'not_eligible': not_eligible,
            'recommendations': recommendations,
            'basic_monetization': basic_monetization,
            'shorts_monetization': shorts_monetization
        }
    
    def calculate_cpm_by_category(self, category: str, country: str = 'KR') -> Tuple[float, float]:
        """카테고리별 CPM 범위 계산 (원화)"""
        cpm_ranges = {
            'education': (3000, 8000),
            'tech': (2500, 7000),
            'finance': (5000, 15000),
            'gaming': (1500, 4000),
            'entertainment': (1000, 3000),
            'vlog': (800, 2500),
            'music': (500, 2000),
            'kids': (1000, 5000),
            'beauty': (2000, 6000),
            'food': (1500, 4500)
        }
        
        # 국가별 조정 계수
        country_multiplier = {
            'KR': 1.0,
            'US': 2.5,
            'JP': 1.8,
            'UK': 2.2,
            'DE': 2.0,
            'CN': 0.5
        }
        
        base_range = cpm_ranges.get(category.lower(), (1000, 3000))
        multiplier = country_multiplier.get(country, 1.0)
        
        return (base_range[0] * multiplier, base_range[1] * multiplier)
    
    def optimize_upload_schedule(self, target_audience: str = 'KR') -> Dict:
        """최적 업로드 시간대 추천"""
        optimal_times = {
            'KR': {
                'weekday': {
                    'prime_time': '19:00-22:00',
                    'secondary': '12:00-13:00',
                    'description': '직장인/학생 퇴근·하교 후 시간대'
                },
                'weekend': {
                    'prime_time': '10:00-12:00, 20:00-23:00',
                    'secondary': '14:00-17:00',
                    'description': '주말 오전 브런치 타임 & 저녁 휴식 시간'
                }
            },
            'Global': {
                'weekday': {
                    'prime_time': '14:00-16:00 KST',
                    'secondary': '03:00-05:00 KST',
                    'description': '미국 저녁/유럽 오후 시간대'
                },
                'weekend': {
                    'prime_time': '03:00-06:00 KST',
                    'secondary': '14:00-17:00 KST',
                    'description': '글로벌 주말 피크 시간'
                }
            }
        }
        
        return optimal_times.get(target_audience, optimal_times['KR'])
    
    def suggest_content_optimization(self, current_performance: Dict) -> List[Dict]:
        """콘텐츠 최적화 제안"""
        suggestions = []
        
        avg_duration = current_performance.get('avg_video_duration_minutes', 10)
        avg_retention = current_performance.get('avg_retention_rate', 50)
        ctr = current_performance.get('click_through_rate', 2)
        
        # 영상 길이 최적화
        if avg_duration < 8:
            suggestions.append({
                'area': '영상 길이',
                'issue': '영상이 너무 짧음',
                'recommendation': '8-12분 길이로 확장하여 중간 광고 삽입 가능',
                'impact': '광고 수익 2-3배 증가 가능'
            })
        elif avg_duration > 20:
            suggestions.append({
                'area': '영상 길이',
                'issue': '영상이 너무 긴 편',
                'recommendation': '핵심 콘텐츠는 10-15분, 심화는 별도 영상으로',
                'impact': '시청 완료율 향상으로 추천 알고리즘 우선순위 상승'
            })
        
        # 시청 유지율 최적화
        if avg_retention < 40:
            suggestions.append({
                'area': '시청 유지율',
                'issue': '낮은 시청 유지율',
                'recommendation': '처음 15초 후킹 강화, 챕터 마커 추가',
                'impact': '유지율 10% 상승 시 조회수 30% 증가 예상'
            })
        
        # CTR 최적화
        if ctr < 4:
            suggestions.append({
                'area': '클릭률(CTR)',
                'issue': '낮은 썸네일 클릭률',
                'recommendation': '썸네일 A/B 테스트, 제목 키워드 최적화',
                'impact': 'CTR 1% 상승 시 노출 수 20% 증가'
            })
        
        # 쇼츠 활용
        suggestions.append({
            'area': '쇼츠 전략',
            'issue': '추가 성장 동력 필요',
            'recommendation': '주요 콘텐츠 하이라이트를 쇼츠로 제작',
            'impact': '신규 구독자 유입 30-50% 증가 가능'
        })
        
        return suggestions
    
    def calculate_sponsorship_rate(self, channel_metrics: Dict) -> Dict:
        """스폰서십 단가 계산"""
        subscribers = channel_metrics.get('subscribers', 0)
        avg_views = channel_metrics.get('avg_views', 0)
        engagement_rate = channel_metrics.get('engagement_rate', 0)
        
        # 기본 단가 계산 (구독자 기준)
        base_rate = subscribers * 50  # 구독자당 50원
        
        # 조회수 보정
        view_multiplier = min(avg_views / subscribers, 1.5) if subscribers > 0 else 0
        
        # 참여율 보정
        engagement_multiplier = 1 + (engagement_rate / 10) if engagement_rate > 5 else 0.8
        
        # 최종 단가
        sponsorship_rate = base_rate * view_multiplier * engagement_multiplier
        
        return {
            'integration': int(sponsorship_rate),  # 통합 스폰서십
            'dedicated': int(sponsorship_rate * 2.5),  # 전용 영상
            'mention': int(sponsorship_rate * 0.3),  # 단순 언급
            'recommendation': self._get_sponsorship_tips(subscribers)
        }
    
    def _get_sponsorship_tips(self, subscribers: int) -> str:
        """구독자 수에 따른 스폰서십 팁"""
        if subscribers < 10000:
            return "마이크로 인플루언서로서 니치 브랜드와 협업 추천"
        elif subscribers < 100000:
            return "미드티어 인플루언서로서 카테고리 관련 브랜드 적극 접근"
        elif subscribers < 1000000:
            return "메이저 브랜드와 장기 파트너십 체결 가능"
        else:
            return "독점 계약 및 브랜드 앰배서더 기회 모색"
    
    def create_revenue_projection(self, current_metrics: Dict, months: int = 12) -> pd.DataFrame:
        """수익 예측 모델"""
        projections = []
        
        current_subs = current_metrics.get('subscribers', 1000)
        current_views = current_metrics.get('monthly_views', 10000)
        growth_rate = current_metrics.get('growth_rate', 0.1)  # 월 10% 성장
        
        for month in range(1, months + 1):
            # 성장 예측
            projected_subs = int(current_subs * ((1 + growth_rate) ** month))
            projected_views = int(current_views * ((1 + growth_rate * 0.8) ** month))
            
            # CPM 기반 광고 수익
            cpm = 2000  # 평균 CPM 2000원
            ad_revenue = (projected_views / 1000) * cpm
            
            # 멤버십 수익 (구독자의 1%)
            membership_revenue = projected_subs * 0.01 * 4900
            
            # 스폰서십 (10만 구독자 이상)
            sponsorship = 0
            if projected_subs >= 100000:
                sponsorship = projected_subs * 30  # 월 1건 기준
            elif projected_subs >= 10000:
                sponsorship = projected_subs * 15
            
            projections.append({
                'month': month,
                'subscribers': projected_subs,
                'views': projected_views,
                'ad_revenue': int(ad_revenue),
                'membership': int(membership_revenue),
                'sponsorship': int(sponsorship),
                'total': int(ad_revenue + membership_revenue + sponsorship)
            })
        
        return pd.DataFrame(projections)
    
    def generate_action_plan(self, channel_analysis: Dict) -> str:
        """실행 계획 생성"""
        plan = """
╔══════════════════════════════════════════════════════════════╗
║           YouTube 수익 창출 실행 계획                           ║
╚══════════════════════════════════════════════════════════════╝

🎯 즉시 실행 과제 (1-2주)
────────────────────────────────────────────────────────────────
1. 채널 기초 설정
   □ 채널 아트 및 로고 전문적으로 디자인
   □ 채널 설명 SEO 최적화 (주요 키워드 포함)
   □ 재생목록 구성 및 추천 영상 설정
   □ 커뮤니티 가이드라인 작성

2. 콘텐츠 최적화
   □ 기존 영상 제목/설명/태그 SEO 재최적화
   □ 종료 화면 및 카드 추가
   □ 썸네일 리디자인 (CTR 향상)
   □ 커뮤니티 탭 활성화

📈 단기 목표 (1-3개월)
────────────────────────────────────────────────────────────────
1. 콘텐츠 제작 시스템 구축
   □ 주간 콘텐츠 캘린더 작성
   □ 배치 촬영으로 효율성 향상
   □ 템플릿 및 프리셋 제작
   □ 자동화 도구 도입 (자막, 썸네일 등)

2. 성장 가속화
   □ 쇼츠 일일 1개 업로드 시작
   □ 트렌드 키워드 활용 콘텐츠 제작
   □ 다른 크리에이터와 콜라보
   □ SNS 크로스 프로모션

3. 커뮤니티 구축
   □ 댓글 100% 응답
   □ 주간 커뮤니티 포스트
   □ 구독자 이벤트 기획
   □ Discord/카톡 채널 개설

🚀 중기 목표 (3-6개월)
────────────────────────────────────────────────────────────────
1. 수익화 달성
   □ 4,000시간 시청 시간 확보
   □ 1,000명 구독자 달성
   □ AdSense 계정 연동
   □ 채널 멤버십 활성화

2. 수익 다각화
   □ 브랜드 미디어킷 제작
   □ 스폰서십 제안서 발송
   □ 제휴 마케팅 시작
   □ 디지털 상품 개발

3. 콘텐츠 확장
   □ 시리즈물 기획 및 제작
   □ 라이브 스트리밍 정기 진행
   □ 팟캐스트 동시 운영
   □ 온라인 강의/코스 제작

💎 장기 전략 (6-12개월)
────────────────────────────────────────────────────────────────
1. 브랜드 확립
   □ 독자적인 콘텐츠 스타일 확립
   □ 시그니처 콘텐츠 개발
   □ 굿즈 및 머천다이즈 출시
   □ 오프라인 팬미팅/워크샵

2. 비즈니스 확장
   □ MCN 가입 검토
   □ 매니지먼트 계약
   □ 도서 출판 기회
   □ 기업 강연/컨설팅

3. 지속 가능한 성장
   □ 팀 구축 (편집자, 기획자)
   □ 스튜디오 구축
   □ 해외 시장 진출
   □ 투자 및 사업 확장

📊 핵심 성과 지표 (KPI)
────────────────────────────────────────────────────────────────
• 월간 구독자 증가율: 20% 이상
• 평균 시청 지속 시간: 50% 이상
• CTR: 5% 이상
• 월간 업로드: 8개 이상
• 참여율: 5% 이상

💡 성공 팁
────────────────────────────────────────────────────────────────
1. 일관성이 핵심 - 정해진 시간에 정기 업로드
2. 품질 > 수량 - 하지만 최소 주 2회는 유지
3. 데이터 분석 - YouTube Analytics 매일 확인
4. 커뮤니티 - 구독자와의 소통을 최우선으로
5. 학습 - 성공한 크리에이터들의 전략 연구

╚══════════════════════════════════════════════════════════════╝
"""
        return plan

# 메인 실행 함수
def analyze_and_optimize():
    optimizer = YouTubeRevenueOptimizer()
    
    # 샘플 채널 데이터
    channel_data = {
        'subscribers': 5000,
        'monthly_views': 100000,
        'watch_time_hours': 2000,
        'avg_views': 5000,
        'engagement_rate': 4.5,
        'growth_rate': 0.15,
        'category': 'education'
    }
    
    # 수익화 자격 확인
    eligibility = optimizer.check_monetization_eligibility(channel_data)
    
    # CPM 계산
    cpm_range = optimizer.calculate_cpm_by_category('education')
    
    # 최적 업로드 시간
    upload_schedule = optimizer.optimize_upload_schedule('KR')
    
    # 스폰서십 단가
    sponsorship_rates = optimizer.calculate_sponsorship_rate(channel_data)
    
    # 수익 예측
    projections = optimizer.create_revenue_projection(channel_data, 12)
    
    # 실행 계획
    action_plan = optimizer.generate_action_plan(channel_data)
    
    # 결과 출력
    print("\n" + "="*60)
    print("YouTube 수익 최적화 분석 결과")
    print("="*60)
    
    print("\n📊 수익화 자격 상태:")
    print(f"✅ 가능한 수익원: {', '.join(eligibility['eligible'])}")
    print(f"❌ 불가능한 수익원: {', '.join(eligibility['not_eligible'])}")
    
    print(f"\n💰 예상 CPM: {cpm_range[0]:,}원 ~ {cpm_range[1]:,}원")
    
    print("\n⏰ 최적 업로드 시간:")
    print(f"평일: {upload_schedule['weekday']['prime_time']}")
    print(f"주말: {upload_schedule['weekend']['prime_time']}")
    
    print("\n💼 스폰서십 예상 단가:")
    print(f"통합 광고: {sponsorship_rates['integration']:,}원")
    print(f"전용 영상: {sponsorship_rates['dedicated']:,}원")
    
    print("\n📈 12개월 수익 예측:")
    print(projections[['month', 'subscribers', 'total']].to_string(index=False))
    
    print(action_plan)
    
    # 파일 저장
    with open('revenue_optimization_report.txt', 'w', encoding='utf-8') as f:
        f.write(action_plan)
        f.write("\n\n수익 예측 데이터:\n")
        f.write(projections.to_string())
    
    return projections

if __name__ == "__main__":
    analyze_and_optimize()