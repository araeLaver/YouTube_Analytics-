import pandas as pd
import numpy as np
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
import re
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import json

class YouTubeContentAnalyzer:
    """YouTube 콘텐츠 깊이 분석 및 사업성 평가"""
    
    def __init__(self):
        self.categories = {
            1: 'Film & Animation', 2: 'Autos & Vehicles', 10: 'Music',
            15: 'Pets & Animals', 17: 'Sports', 19: 'Travel & Events',
            20: 'Gaming', 22: 'People & Blogs', 23: 'Comedy',
            24: 'Entertainment', 25: 'News & Politics', 26: 'Howto & Style',
            27: 'Education', 28: 'Science & Technology', 29: 'Nonprofits & Activism'
        }
        
    def analyze_content_performance(self, videos: List[Dict]) -> Dict:
        """콘텐츠 성과 분석"""
        if not videos:
            return {}
            
        df = pd.DataFrame(videos)
        
        # 기본 통계
        stats = {
            'total_videos': len(videos),
            'total_views': df['view_count'].sum(),
            'avg_views': df['view_count'].mean(),
            'median_views': df['view_count'].median(),
            'max_views': df['view_count'].max(),
            'min_views': df['view_count'].min(),
            'std_views': df['view_count'].std(),
            'avg_duration': df['duration'].mean() / 60,  # 분 단위
            'total_watch_time': df['view_count'].sum() * df['duration'].mean() / 3600  # 시간 단위
        }
        
        # 참여율 분석
        df['engagement_rate'] = ((df['like_count'] + df['comment_count']) / df['view_count'] * 100)
        stats['avg_engagement_rate'] = df['engagement_rate'].mean()
        
        # 성과 구간별 분석
        df['performance_tier'] = pd.cut(df['view_count'], 
                                       bins=[-1, df['view_count'].quantile(0.25), 
                                            df['view_count'].quantile(0.75), float('inf')],
                                       labels=['Low', 'Medium', 'High'])
        
        tier_analysis = {}
        for tier in ['Low', 'Medium', 'High']:
            tier_data = df[df['performance_tier'] == tier]
            if not tier_data.empty:
                tier_analysis[tier] = {
                    'count': len(tier_data),
                    'avg_views': tier_data['view_count'].mean(),
                    'avg_engagement': tier_data['engagement_rate'].mean(),
                    'avg_duration': tier_data['duration'].mean() / 60
                }
        
        stats['performance_tiers'] = tier_analysis
        
        return stats
    
    def analyze_title_patterns(self, videos: List[Dict]) -> Dict:
        """제목 패턴 및 키워드 분석"""
        if not videos:
            return {}
            
        titles = [video['title'] for video in videos]
        
        # 제목 길이 분석
        title_lengths = [len(title) for title in titles]
        
        # 키워드 추출
        all_text = ' '.join(titles)
        
        # 한국어 키워드 추출
        korean_words = re.findall(r'[가-힣]+', all_text)
        english_words = re.findall(r'[a-zA-Z]+', all_text.lower())
        numbers = re.findall(r'\d+', all_text)
        
        # 특수 패턴 분석
        patterns = {
            'question_marks': len(re.findall(r'\?', all_text)),
            'exclamation_marks': len(re.findall(r'!', all_text)),
            'brackets': len(re.findall(r'[\[\](){}]', all_text)),
            'numbers_in_titles': len([title for title in titles if re.search(r'\d', title)]),
            'caps_titles': len([title for title in titles if any(c.isupper() for c in title)])
        }
        
        # 감정 분석 (영어 제목에 대해)
        english_titles = [title for title in titles if re.search(r'[a-zA-Z]', title)]
        sentiments = []
        for title in english_titles:
            try:
                sentiment = TextBlob(title).sentiment.polarity
                sentiments.append(sentiment)
            except:
                sentiments.append(0)
        
        return {
            'avg_title_length': np.mean(title_lengths),
            'title_length_range': [min(title_lengths), max(title_lengths)],
            'top_korean_words': Counter(korean_words).most_common(10),
            'top_english_words': Counter(english_words).most_common(10),
            'common_numbers': Counter(numbers).most_common(5),
            'special_patterns': patterns,
            'avg_sentiment': np.mean(sentiments) if sentiments else 0,
            'positive_titles_ratio': len([s for s in sentiments if s > 0.1]) / len(sentiments) if sentiments else 0
        }
    
    def analyze_upload_patterns(self, videos: List[Dict]) -> Dict:
        """업로드 패턴 분석"""
        if not videos:
            return {}
            
        df = pd.DataFrame(videos)
        df['published_date'] = pd.to_datetime(df['published_date'])
        
        # 시간별 분석
        df['hour'] = df['published_date'].dt.hour
        df['day_of_week'] = df['published_date'].dt.day_name()
        df['month'] = df['published_date'].dt.month
        df['day_of_month'] = df['published_date'].dt.day
        
        # 업로드 빈도 계산
        date_range = (df['published_date'].max() - df['published_date'].min()).days
        upload_frequency = len(videos) / max(date_range, 1)
        
        # 성과가 좋은 업로드 시간 분석
        hourly_performance = df.groupby('hour').agg({
            'view_count': ['mean', 'count'],
            'like_count': 'mean',
            'comment_count': 'mean'
        }).round(0)
        
        daily_performance = df.groupby('day_of_week').agg({
            'view_count': ['mean', 'count'],
            'like_count': 'mean'
        }).round(0)
        
        # 업로드 일관성 분석
        upload_dates = df['published_date'].dt.date
        date_diffs = [(upload_dates.iloc[i] - upload_dates.iloc[i+1]).days 
                     for i in range(len(upload_dates)-1)]
        consistency_score = 100 - (np.std(date_diffs) / np.mean(date_diffs) * 50) if date_diffs else 0
        
        return {
            'total_days_analyzed': date_range,
            'videos_per_day': upload_frequency,
            'upload_consistency_score': max(0, consistency_score),
            'best_upload_hours': hourly_performance.nlargest(3, ('view_count', 'mean')),
            'best_upload_days': daily_performance.nlargest(3, ('view_count', 'mean')),
            'upload_distribution': {
                'hourly': df['hour'].value_counts().to_dict(),
                'daily': df['day_of_week'].value_counts().to_dict(),
                'monthly': df['month'].value_counts().to_dict()
            }
        }
    
    def analyze_content_topics(self, videos: List[Dict]) -> Dict:
        """콘텐츠 주제 분석"""
        if not videos:
            return {}
        
        # 제목과 설명에서 키워드 추출
        all_content = []
        for video in videos:
            content = f"{video.get('title', '')} {video.get('description', '')}"
            all_content.append(content)
        
        # 주제별 키워드 분류
        topic_keywords = {
            '교육/튜토리얼': ['배우', '방법', '강의', '설명', '가이드', 'how', 'tutorial', 'learn', '알려', '공부'],
            '리뷰/분석': ['리뷰', '분석', '비교', '테스트', '후기', 'review', 'test', '평가', '체험'],
            '엔터테인먼트': ['웃긴', '재밌는', '놀라운', '신기한', 'funny', 'amazing', '몰카', '개그'],
            '뉴스/정보': ['뉴스', '소식', '정보', '발표', '출시', 'news', '업데이트', '공지'],
            'VLOG/일상': ['일상', '브이로그', 'vlog', '하루', '데일리', 'daily', '생활'],
            '게임': ['게임', '플레이', '공략', 'game', 'play', '겜', '스트리밍'],
            '기술/IT': ['기술', '프로그래밍', '코딩', '개발', 'tech', 'code', '앱', '소프트웨어']
        }
        
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = 0
            for content in all_content:
                content_lower = content.lower()
                for keyword in keywords:
                    score += content_lower.count(keyword.lower())
            topic_scores[topic] = score
        
        # 주제별 성과 분석
        topic_performance = {}
        for video in videos:
            content = f"{video.get('title', '')} {video.get('description', '')}".lower()
            best_topic = None
            max_score = 0
            
            for topic, keywords in topic_keywords.items():
                score = sum(content.count(keyword.lower()) for keyword in keywords)
                if score > max_score:
                    max_score = score
                    best_topic = topic
            
            if best_topic and max_score > 0:
                if best_topic not in topic_performance:
                    topic_performance[best_topic] = []
                topic_performance[best_topic].append(video['view_count'])
        
        # 주제별 평균 성과 계산
        topic_avg_views = {}
        for topic, views in topic_performance.items():
            topic_avg_views[topic] = np.mean(views)
        
        return {
            'topic_distribution': topic_scores,
            'most_common_topic': max(topic_scores, key=topic_scores.get),
            'topic_performance': topic_avg_views,
            'best_performing_topic': max(topic_avg_views, key=topic_avg_views.get) if topic_avg_views else None
        }
    
    def calculate_business_metrics(self, channel_data: Dict, content_stats: Dict) -> Dict:
        """사업성 지표 계산"""
        subscribers = channel_data.get('subscriber_count', 0)
        avg_views = content_stats.get('avg_views', 0)
        total_views = content_stats.get('total_views', 0)
        avg_engagement = content_stats.get('avg_engagement_rate', 0)
        
        # CPM 기반 수익 계산 (한국 기준)
        base_cpm = 2000  # 기본 CPM (원)
        
        # 카테고리별 CPM 조정
        category_multiplier = {
            'Education': 1.5,
            'Technology': 1.4,
            'Finance': 2.0,
            'Gaming': 0.8,
            'Entertainment': 0.7,
            'Music': 0.6
        }
        
        # 월 수익 예측 (주 2회 업로드 가정)
        monthly_videos = 8
        monthly_views = avg_views * monthly_videos
        monthly_ad_revenue = (monthly_views / 1000) * base_cpm
        
        # 스폰서십 수익 예측
        if subscribers >= 100000:
            sponsorship_rate = subscribers * 100  # 구독자당 100원
            sponsorship_tier = "A급 (대형 브랜드)"
        elif subscribers >= 50000:
            sponsorship_rate = subscribers * 70
            sponsorship_tier = "B급 (중견 브랜드)"  
        elif subscribers >= 10000:
            sponsorship_rate = subscribers * 40
            sponsorship_tier = "C급 (소규모 브랜드)"
        else:
            sponsorship_rate = subscribers * 15
            sponsorship_tier = "D급 (로컬 브랜드)"
        
        # 기타 수익원
        membership_revenue = subscribers * 0.01 * 4900  # 구독자의 1%가 멤버십 가입
        superchat_revenue = monthly_views * 0.001 * 500  # 조회수의 0.1%가 슈퍼챗
        
        # 총 예상 수익
        total_monthly_revenue = monthly_ad_revenue + (sponsorship_rate / 12) + membership_revenue + superchat_revenue
        
        # ROI 지표
        metrics = {
            'monthly_revenue_estimate': {
                'advertising': int(monthly_ad_revenue),
                'sponsorship_monthly': int(sponsorship_rate / 12),
                'membership': int(membership_revenue),
                'superchat': int(superchat_revenue),
                'total': int(total_monthly_revenue)
            },
            'sponsorship_info': {
                'per_video_rate': int(sponsorship_rate),
                'tier': sponsorship_tier,
                'annual_potential': int(sponsorship_rate * 6)  # 년 6건 가정
            },
            'growth_metrics': {
                'views_per_subscriber': avg_views / subscribers if subscribers > 0 else 0,
                'engagement_quality_score': min(100, avg_engagement * 20),
                'content_consistency': content_stats.get('upload_consistency_score', 0),
                'monetization_readiness': self._calculate_monetization_readiness(subscribers, total_views, avg_engagement)
            },
            'market_position': {
                'subscriber_tier': self._get_subscriber_tier(subscribers),
                'growth_stage': self._determine_growth_stage(subscribers, avg_views),
                'competition_level': self._assess_competition_level(channel_data, content_stats)
            }
        }
        
        return metrics
    
    def _calculate_monetization_readiness(self, subscribers: int, total_views: int, engagement: float) -> int:
        """수익화 준비도 점수 (0-100)"""
        score = 0
        
        # 구독자 점수 (40점)
        if subscribers >= 100000:
            score += 40
        elif subscribers >= 10000:
            score += 30
        elif subscribers >= 1000:
            score += 20
        elif subscribers >= 100:
            score += 10
        
        # 조회수 점수 (30점)
        if total_views >= 10000000:
            score += 30
        elif total_views >= 1000000:
            score += 20
        elif total_views >= 100000:
            score += 15
        elif total_views >= 10000:
            score += 10
        
        # 참여율 점수 (30점)
        if engagement >= 10:
            score += 30
        elif engagement >= 5:
            score += 20
        elif engagement >= 2:
            score += 10
        elif engagement >= 1:
            score += 5
        
        return min(100, score)
    
    def _get_subscriber_tier(self, subscribers: int) -> str:
        """구독자 등급 분류"""
        if subscribers >= 1000000:
            return "메가 인플루언서 (100만+)"
        elif subscribers >= 100000:
            return "매크로 인플루언서 (10-100만)"
        elif subscribers >= 10000:
            return "마이크로 인플루언서 (1-10만)"
        elif subscribers >= 1000:
            return "나노 인플루언서 (1천-1만)"
        else:
            return "신규 크리에이터 (1천 미만)"
    
    def _determine_growth_stage(self, subscribers: int, avg_views: int) -> str:
        """성장 단계 판단"""
        view_to_sub_ratio = avg_views / subscribers if subscribers > 0 else 0
        
        if view_to_sub_ratio >= 0.5:
            return "급성장 단계"
        elif view_to_sub_ratio >= 0.2:
            return "성장 단계"  
        elif view_to_sub_ratio >= 0.1:
            return "안정 단계"
        else:
            return "정체 단계"
    
    def _assess_competition_level(self, channel_data: Dict, content_stats: Dict) -> str:
        """경쟁 강도 평가"""
        # 간단한 휴리스틱 기반 평가
        avg_views = content_stats.get('avg_views', 0)
        subscribers = channel_data.get('subscriber_count', 0)
        
        if avg_views > subscribers * 0.3:
            return "저경쟁 (블루오션)"
        elif avg_views > subscribers * 0.1:
            return "중간경쟁 (성장 가능)"
        else:
            return "고경쟁 (레드오션)"
    
    def generate_comprehensive_report(self, channel_data: Dict, videos: List[Dict]) -> str:
        """종합 분석 리포트 생성"""
        
        # 각종 분석 실행
        content_stats = self.analyze_content_performance(videos)
        title_analysis = self.analyze_title_patterns(videos)
        upload_patterns = self.analyze_upload_patterns(videos)
        topic_analysis = self.analyze_content_topics(videos)
        business_metrics = self.calculate_business_metrics(channel_data, content_stats)
        
        report = f"""
████████████████████████████████████████████████████████████████████████
                    YouTube 채널 종합 사업성 분석 보고서
████████████████████████████████████████████████████████████████████████

📺 채널 기본 정보
════════════════════════════════════════════════════════════════════════
채널명: {channel_data.get('channel_name', 'Unknown')}
구독자: {channel_data.get('subscriber_count', 0):,}명
총 조회수: {channel_data.get('total_views', 0):,}회
총 동영상: {channel_data.get('video_count', 0)}개
개설일: {channel_data.get('created_date', 'Unknown')[:10]}

📊 콘텐츠 성과 분석
════════════════════════════════════════════════════════════════════════
분석 대상 영상: {content_stats.get('total_videos', 0)}개
평균 조회수: {content_stats.get('avg_views', 0):,.0f}회
최고 조회수: {content_stats.get('max_views', 0):,}회
평균 참여율: {content_stats.get('avg_engagement_rate', 0):.2f}%
평균 영상 길이: {content_stats.get('avg_duration', 0):.1f}분
총 시청 시간: {content_stats.get('total_watch_time', 0):,.0f}시간

🎯 콘텐츠 주제 분석  
════════════════════════════════════════════════════════════════════════
주요 콘텐츠 유형: {topic_analysis.get('most_common_topic', 'Unknown')}
최고 성과 주제: {topic_analysis.get('best_performing_topic', 'Unknown')}

주제별 분포:"""
        
        # 주제 분포 추가
        topic_dist = topic_analysis.get('topic_distribution', {})
        for topic, score in sorted(topic_dist.items(), key=lambda x: x[1], reverse=True)[:5]:
            if score > 0:
                report += f"\n  • {topic}: {score}개 키워드"
        
        report += f"""

📝 제목 패턴 분석
════════════════════════════════════════════════════════════════════════
평균 제목 길이: {title_analysis.get('avg_title_length', 0):.0f}자
긍정적 제목 비율: {title_analysis.get('positive_titles_ratio', 0)*100:.1f}%
숫자 포함 제목: {title_analysis.get('special_patterns', {}).get('numbers_in_titles', 0)}개

인기 키워드 TOP 5:"""
        
        # 인기 키워드 추가
        top_words = title_analysis.get('top_korean_words', [])[:5]
        for i, (word, count) in enumerate(top_words, 1):
            report += f"\n  {i}. {word} ({count}회)"
        
        report += f"""

⏰ 업로드 패턴 분석
════════════════════════════════════════════════════════════════════════
업로드 빈도: 일 {upload_patterns.get('videos_per_day', 0):.2f}개
업로드 일관성: {upload_patterns.get('upload_consistency_score', 0):.1f}/100점

최적 업로드 시간대:"""
        
        # 시간대별 성과는 복잡하므로 간단히 표시
        upload_dist = upload_patterns.get('upload_distribution', {}).get('hourly', {})
        if upload_dist:
            best_hours = sorted(upload_dist.items(), key=lambda x: x[1], reverse=True)[:3]
            for hour, count in best_hours:
                report += f"\n  • {hour}시: {count}개 업로드"
        
        report += f"""

💰 예상 수익 분석
════════════════════════════════════════════════════════════════════════
월 예상 총 수익: {business_metrics['monthly_revenue_estimate']['total']:,}원

수익 구성:
  • 광고 수익: {business_metrics['monthly_revenue_estimate']['advertising']:,}원
  • 스폰서십: {business_metrics['monthly_revenue_estimate']['sponsorship_monthly']:,}원/월
  • 멤버십: {business_metrics['monthly_revenue_estimate']['membership']:,}원
  • 슈퍼챗: {business_metrics['monthly_revenue_estimate']['superchat']:,}원

스폰서십 정보:
  • 영상당 단가: {business_metrics['sponsorship_info']['per_video_rate']:,}원
  • 브랜드 등급: {business_metrics['sponsorship_info']['tier']}
  • 연 예상 수익: {business_metrics['sponsorship_info']['annual_potential']:,}원

📈 성장 지표
════════════════════════════════════════════════════════════════════════
구독자 등급: {business_metrics['market_position']['subscriber_tier']}
성장 단계: {business_metrics['market_position']['growth_stage']}
시장 경쟁도: {business_metrics['market_position']['competition_level']}
수익화 준비도: {business_metrics['growth_metrics']['monetization_readiness']}/100점
콘텐츠 일관성: {business_metrics['growth_metrics']['content_consistency']:.1f}/100점

🎬 콘텐츠 성과 등급별 분석
════════════════════════════════════════════════════════════════════════"""
        
        # 성과 등급별 분석
        tiers = content_stats.get('performance_tiers', {})
        for tier, data in tiers.items():
            report += f"""
【{tier} 성과 영상】
  • 개수: {data['count']}개
  • 평균 조회수: {data['avg_views']:,.0f}회
  • 평균 참여율: {data['avg_engagement']:.2f}%
  • 평균 길이: {data['avg_duration']:.1f}분"""
        
        report += f"""

💡 사업 기회 및 추천사항
════════════════════════════════════════════════════════════════════════"""
        
        # 추천사항 생성
        recommendations = []
        
        # 구독자 기준 추천
        subs = channel_data.get('subscriber_count', 0)
        if subs < 1000:
            recommendations.append("🎯 우선순위: 1,000명 구독자 달성 (수익화 조건)")
            recommendations.append("  - 쇼츠 콘텐츠 활용하여 노출 극대화")
            recommendations.append("  - 트렌드 키워드 적극 활용")
        elif subs < 10000:
            recommendations.append("🎯 우선순위: 1만명 돌파 (마이크로 인플루언서)")
            recommendations.append("  - 스폰서십 기회 탐색 시작")
            recommendations.append("  - 커뮤니티 구축 및 참여율 향상")
        else:
            recommendations.append("🎯 우선순위: 수익 다각화 및 브랜드 구축")
            recommendations.append("  - 프리미엄 스폰서십 적극 유치")
            recommendations.append("  - 자체 상품/서비스 개발 검토")
        
        # 참여율 기준 추천
        engagement = content_stats.get('avg_engagement_rate', 0)
        if engagement < 2:
            recommendations.append("📢 참여율 개선 필요")
            recommendations.append("  - CTA 강화 및 커뮤니티 소통 증대")
        elif engagement > 5:
            recommendations.append("⭐ 높은 참여율 활용")
            recommendations.append("  - 라이브 스트리밍 및 실시간 소통 확대")
        
        # 콘텐츠 전략 추천
        best_topic = topic_analysis.get('best_performing_topic')
        if best_topic:
            recommendations.append(f"🎬 '{best_topic}' 콘텐츠 확대 권장")
        
        for rec in recommendations:
            report += f"\n{rec}"
        
        report += f"""

⚠️ 주의사항 및 리스크
════════════════════════════════════════════════════════════════════════
• 수익 예측은 평균값 기준이며 실제와 차이 있을 수 있음
• YouTube 정책 변화에 따른 수익 변동 가능성
• 경쟁 심화로 인한 성장률 둔화 리스크
• 콘텐츠 트렌드 변화 대응 필요성

📊 데이터 기준
════════════════════════════════════════════════════════════════════════
분석일: {datetime.now().strftime('%Y년 %m월 %d일')}
분석 영상 수: {len(videos)}개
데이터 수집 방법: YouTube API/웹 크롤링

████████████████████████████████████████████████████████████████████████
                              보고서 끝
████████████████████████████████████████████████████████████████████████
"""
        
        return report
    
    def save_analysis_results(self, channel_name: str, report: str, data: Dict):
        """분석 결과 저장"""
        # 텍스트 리포트 저장
        filename = f"business_analysis_{channel_name.replace(' ', '_')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # JSON 데이터 저장
        json_filename = f"analysis_data_{channel_name.replace(' ', '_')}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"분석 완료: {filename}, {json_filename} 저장됨")

# 사용 예제
if __name__ == "__main__":
    analyzer = YouTubeContentAnalyzer()
    
    # 샘플 데이터로 테스트
    sample_channel = {
        'channel_name': '로직알려주는남자',
        'subscriber_count': 50000,
        'total_views': 5000000,
        'video_count': 200,
        'created_date': '2022-01-01'
    }
    
    sample_videos = [
        {
            'title': '파이썬 기초 강의 1편',
            'view_count': 25000,
            'like_count': 800,
            'comment_count': 150,
            'duration': 600,
            'published_date': '2024-01-15T10:00:00Z',
            'description': '파이썬 프로그래밍 기초를 배워보세요'
        }
        # 더 많은 샘플 데이터...
    ]
    
    report = analyzer.generate_comprehensive_report(sample_channel, sample_videos)
    print(report)