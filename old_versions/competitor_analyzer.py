import pandas as pd
import numpy as np
from typing import Dict, List
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

class CompetitorAnalyzer:
    """YouTube 경쟁 채널 분석 도구"""
    
    def __init__(self):
        self.analysis_metrics = [
            'subscribers', 'views', 'videos', 'engagement_rate',
            'upload_frequency', 'avg_views_per_video', 'growth_rate'
        ]
    
    def analyze_competitor_channels(self, channels: List[Dict]) -> pd.DataFrame:
        """경쟁 채널 종합 분석"""
        df = pd.DataFrame(channels)
        
        # 효율성 점수 계산
        df['efficiency_score'] = (df['avg_views'] / df['subscribers'] * 100).round(2)
        
        # 성장 잠재력 점수
        df['growth_potential'] = (
            df['growth_rate'] * 0.4 + 
            df['engagement_rate'] * 0.3 + 
            df['upload_consistency'] * 0.3
        ).round(2)
        
        # 수익화 점수
        df['monetization_score'] = self._calculate_monetization_score(df)
        
        # 종합 순위
        df['overall_rank'] = df[['efficiency_score', 'growth_potential', 'monetization_score']].mean(axis=1).rank(ascending=False)
        
        return df.sort_values('overall_rank')
    
    def _calculate_monetization_score(self, df: pd.DataFrame) -> pd.Series:
        """수익화 가능성 점수 계산"""
        scores = []
        for _, row in df.iterrows():
            score = 0
            
            # 구독자 기준
            if row['subscribers'] >= 1000000:
                score += 40
            elif row['subscribers'] >= 100000:
                score += 30
            elif row['subscribers'] >= 10000:
                score += 20
            elif row['subscribers'] >= 1000:
                score += 10
            
            # 조회수 기준
            if row['avg_views'] >= 100000:
                score += 30
            elif row['avg_views'] >= 10000:
                score += 20
            elif row['avg_views'] >= 1000:
                score += 10
            
            # 참여율 기준
            if row['engagement_rate'] >= 10:
                score += 30
            elif row['engagement_rate'] >= 5:
                score += 20
            elif row['engagement_rate'] >= 2:
                score += 10
            
            scores.append(score)
        
        return pd.Series(scores)
    
    def identify_content_gaps(self, my_channel: Dict, competitors: List[Dict]) -> Dict:
        """콘텐츠 갭 분석"""
        gaps = {
            'untapped_topics': [],
            'underserved_formats': [],
            'timing_opportunities': [],
            'audience_gaps': []
        }
        
        # 경쟁사 콘텐츠 분석
        competitor_topics = set()
        competitor_formats = set()
        upload_times = []
        
        for comp in competitors:
            if 'topics' in comp:
                competitor_topics.update(comp['topics'])
            if 'formats' in comp:
                competitor_formats.update(comp['formats'])
            if 'upload_times' in comp:
                upload_times.extend(comp['upload_times'])
        
        # 내 채널과 비교
        my_topics = set(my_channel.get('topics', []))
        my_formats = set(my_channel.get('formats', []))
        
        # 갭 식별
        gaps['untapped_topics'] = list(competitor_topics - my_topics)
        gaps['underserved_formats'] = list(competitor_formats - my_formats)
        
        # 업로드 시간 분석
        if upload_times:
            time_analysis = pd.Series(upload_times).value_counts()
            least_competitive = time_analysis.nsmallest(3).index.tolist()
            gaps['timing_opportunities'] = least_competitive
        
        return gaps
    
    def benchmark_performance(self, my_channel: Dict, competitors: List[Dict]) -> Dict:
        """성과 벤치마킹"""
        # 경쟁사 평균 계산
        comp_df = pd.DataFrame(competitors)
        
        benchmarks = {
            'vs_average': {},
            'vs_top_performer': {},
            'percentile_rank': {},
            'improvement_targets': {}
        }
        
        metrics = ['subscribers', 'avg_views', 'engagement_rate', 'upload_frequency']
        
        for metric in metrics:
            if metric in comp_df.columns and metric in my_channel:
                avg_value = comp_df[metric].mean()
                top_value = comp_df[metric].max()
                my_value = my_channel[metric]
                
                # 평균 대비
                benchmarks['vs_average'][metric] = {
                    'my_value': my_value,
                    'average': round(avg_value, 2),
                    'difference': round(((my_value - avg_value) / avg_value * 100), 2)
                }
                
                # 톱 퍼포머 대비
                benchmarks['vs_top_performer'][metric] = {
                    'my_value': my_value,
                    'top_value': round(top_value, 2),
                    'gap': round(((top_value - my_value) / my_value * 100), 2)
                }
                
                # 백분위 순위
                percentile = (comp_df[metric] < my_value).sum() / len(comp_df) * 100
                benchmarks['percentile_rank'][metric] = round(percentile, 1)
                
                # 개선 목표
                if percentile < 50:
                    target = comp_df[metric].quantile(0.75)
                    benchmarks['improvement_targets'][metric] = {
                        'current': my_value,
                        'target': round(target, 2),
                        'required_growth': round(((target - my_value) / my_value * 100), 2)
                    }
        
        return benchmarks
    
    def analyze_best_practices(self, top_performers: List[Dict]) -> Dict:
        """상위 채널 베스트 프랙티스 분석"""
        practices = {
            'content_strategies': [],
            'engagement_tactics': [],
            'growth_patterns': [],
            'monetization_methods': []
        }
        
        for channel in top_performers:
            # 콘텐츠 전략
            if channel.get('upload_frequency') >= 3:
                practices['content_strategies'].append(
                    f"{channel['name']}: 주 {channel['upload_frequency']}회 규칙적 업로드"
                )
            
            # 참여 전략
            if channel.get('engagement_rate', 0) >= 5:
                practices['engagement_tactics'].append(
                    f"{channel['name']}: {channel['engagement_rate']}% 높은 참여율 - "
                    f"{channel.get('engagement_strategy', '커뮤니티 중심 운영')}"
                )
            
            # 성장 패턴
            if channel.get('growth_rate', 0) >= 20:
                practices['growth_patterns'].append(
                    f"{channel['name']}: 월 {channel['growth_rate']}% 성장 - "
                    f"{channel.get('growth_strategy', '트렌드 콘텐츠 활용')}"
                )
            
            # 수익화 방법
            if 'revenue_streams' in channel:
                practices['monetization_methods'].extend(channel['revenue_streams'])
        
        # 중복 제거 및 정렬
        for key in practices:
            practices[key] = list(set(practices[key]))
        
        return practices
    
    def generate_competitive_strategy(self, analysis_results: Dict) -> str:
        """경쟁 전략 생성"""
        strategy = """
╔══════════════════════════════════════════════════════════════╗
║              경쟁 채널 분석 및 차별화 전략                       ║
╚══════════════════════════════════════════════════════════════╝

🎯 포지셔닝 전략
────────────────────────────────────────────────────────────────
"""
        
        # 포지셔닝 매트릭스
        if 'benchmark' in analysis_results:
            percentiles = analysis_results['benchmark'].get('percentile_rank', {})
            
            if percentiles.get('engagement_rate', 0) > 70:
                strategy += "• 고참여율 프리미엄 채널 포지셔닝\n"
                strategy += "  → 충성도 높은 커뮤니티 기반 수익화\n"
            elif percentiles.get('avg_views', 0) > 70:
                strategy += "• 대중적 인기 채널 포지셔닝\n"
                strategy += "  → 광고 수익 최적화 집중\n"
            else:
                strategy += "• 니치 전문 채널 포지셔닝\n"
                strategy += "  → 특정 타겟층 공략으로 차별화\n"
        
        strategy += """
📊 경쟁 우위 확보 방안
────────────────────────────────────────────────────────────────
1. 콘텐츠 차별화
   • 미개척 주제 선점
   • 독특한 포맷 개발
   • 시리즈물 기획

2. 품질 우위
   • 프로덕션 퀄리티 향상
   • 전문적 편집 기술
   • 차별화된 시각 효과

3. 속도 우위
   • 트렌드 즉각 대응
   • 빠른 업로드 주기
   • 실시간 이슈 커버

🚀 실행 전략
────────────────────────────────────────────────────────────────
"""
        
        if 'gaps' in analysis_results:
            gaps = analysis_results['gaps']
            
            if gaps.get('untapped_topics'):
                strategy += f"1. 미개척 콘텐츠 영역\n"
                for topic in gaps['untapped_topics'][:3]:
                    strategy += f"   • {topic}\n"
            
            if gaps.get('timing_opportunities'):
                strategy += f"\n2. 최적 업로드 시간대\n"
                for time in gaps['timing_opportunities'][:3]:
                    strategy += f"   • {time}\n"
        
        strategy += """
💡 벤치마킹 포인트
────────────────────────────────────────────────────────────────
"""
        
        if 'best_practices' in analysis_results:
            practices = analysis_results['best_practices']
            
            if practices.get('content_strategies'):
                strategy += "• 콘텐츠 전략:\n"
                for practice in practices['content_strategies'][:3]:
                    strategy += f"  - {practice}\n"
            
            if practices.get('engagement_tactics'):
                strategy += "\n• 참여 유도 전략:\n"
                for tactic in practices['engagement_tactics'][:3]:
                    strategy += f"  - {tactic}\n"
        
        strategy += """
📈 성장 목표 설정
────────────────────────────────────────────────────────────────
"""
        
        if 'benchmark' in analysis_results:
            targets = analysis_results['benchmark'].get('improvement_targets', {})
            
            for metric, target_data in targets.items():
                strategy += f"• {metric}:\n"
                strategy += f"  현재: {target_data['current']:,}\n"
                strategy += f"  목표: {target_data['target']:,}\n"
                strategy += f"  필요 성장률: {target_data['required_growth']}%\n\n"
        
        strategy += """
╚══════════════════════════════════════════════════════════════╝
"""
        
        return strategy

# 샘플 데이터로 분석 실행
def run_competitor_analysis():
    analyzer = CompetitorAnalyzer()
    
    # 내 채널 데이터
    my_channel = {
        'name': '로직알려주는남자',
        'subscribers': 50000,
        'avg_views': 25000,
        'engagement_rate': 4.5,
        'upload_frequency': 2,
        'topics': ['프로그래밍', '알고리즘', '코딩'],
        'formats': ['튜토리얼', '강의', '라이브코딩']
    }
    
    # 경쟁 채널 데이터
    competitors = [
        {
            'name': '코딩애플',
            'subscribers': 200000,
            'avg_views': 50000,
            'videos': 500,
            'engagement_rate': 6.5,
            'upload_frequency': 3,
            'upload_consistency': 85,
            'growth_rate': 15,
            'topics': ['웹개발', '프론트엔드', '백엔드', '앱개발'],
            'formats': ['튜토리얼', '강의', '프로젝트'],
            'revenue_streams': ['광고', '온라인강의', '스폰서십']
        },
        {
            'name': '노마드코더',
            'subscribers': 350000,
            'avg_views': 80000,
            'videos': 800,
            'engagement_rate': 7.8,
            'upload_frequency': 4,
            'upload_consistency': 90,
            'growth_rate': 20,
            'topics': ['웹개발', '리액트', '자바스크립트', '파이썬'],
            'formats': ['강의', '챌린지', '라이브'],
            'revenue_streams': ['광고', '유료강의', '멤버십', '스폰서십']
        },
        {
            'name': '드림코딩',
            'subscribers': 150000,
            'avg_views': 40000,
            'videos': 300,
            'engagement_rate': 8.2,
            'upload_frequency': 2,
            'upload_consistency': 75,
            'growth_rate': 12,
            'topics': ['프론트엔드', 'UI/UX', '자바스크립트'],
            'formats': ['튜토리얼', '팁앤트릭', 'Q&A'],
            'revenue_streams': ['광고', '멤버십', '굿즈']
        }
    ]
    
    # 분석 실행
    competitor_df = analyzer.analyze_competitor_channels(competitors)
    gaps = analyzer.identify_content_gaps(my_channel, competitors)
    benchmark = analyzer.benchmark_performance(my_channel, competitors)
    best_practices = analyzer.analyze_best_practices(competitors[:2])  # 상위 2개 채널
    
    # 종합 결과
    analysis_results = {
        'competitor_analysis': competitor_df,
        'gaps': gaps,
        'benchmark': benchmark,
        'best_practices': best_practices
    }
    
    # 전략 생성
    strategy = analyzer.generate_competitive_strategy(analysis_results)
    
    # 결과 출력
    print("\n" + "="*60)
    print("경쟁 채널 분석 결과")
    print("="*60)
    
    print("\n📊 경쟁 채널 순위:")
    print(competitor_df[['name', 'overall_rank', 'efficiency_score', 'growth_potential']].to_string(index=False))
    
    print("\n🔍 콘텐츠 갭 분석:")
    print(f"미개척 주제: {', '.join(gaps['untapped_topics'][:5])}")
    print(f"미활용 포맷: {', '.join(gaps['underserved_formats'][:3])}")
    
    print("\n📈 벤치마크 (백분위 순위):")
    for metric, percentile in benchmark['percentile_rank'].items():
        print(f"{metric}: 상위 {100-percentile:.1f}%")
    
    print(strategy)
    
    # 파일 저장
    with open('competitor_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(strategy)
        f.write("\n\n상세 분석 데이터:\n")
        f.write(competitor_df.to_string())
    
    return analysis_results

if __name__ == "__main__":
    run_competitor_analysis()