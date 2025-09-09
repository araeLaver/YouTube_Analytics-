# -*- coding: utf-8 -*-
"""
YouTube 채널 사업성 분석 데모
"""

def analyze_youtube_channel(channel_url):
    """YouTube 채널 분석"""
    
    # 채널명 추출
    if "@" in channel_url:
        channel_name = channel_url.split("@")[-1]
    else:
        channel_name = "Unknown Channel"
    
    print("=" * 50)
    print("YouTube 채널 사업성 분석 결과")
    print("=" * 50)
    print(f"분석 대상: {channel_name}")
    print()
    
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
    elif subs >= 10000:
        sponsorship = subs * 50
        tier = "성장 채널"
    else:
        sponsorship = subs * 20
        tier = "신규 채널"
    
    # 결과 출력
    print(f"구독자: {subs:,}명")
    print(f"평균 조회수: {avg_views:,}회")
    print(f"카테고리: {category}")
    print(f"채널 등급: {tier}")
    print()
    
    print("== 예상 월 수익 ==")
    print(f"광고 수익: {int(monthly_ad_revenue):,}원")
    print(f"스폰서십: {int(sponsorship/12):,}원")
    print(f"총 예상 수익: {int(monthly_ad_revenue + sponsorship/12):,}원")
    print()
    
    print("== 성장 전략 ==")
    if subs < 1000:
        print("1. 1,000명 구독자 달성 집중")
        print("2. 쇼츠 콘텐츠 활용")
    elif subs < 10000:
        print("1. 1만명 목표로 성장 가속화")
        print("2. 스폰서십 준비")
    else:
        print("1. 수익 다각화")
        print("2. 브랜드 구축")
    
    print("3. 업로드 일정 규칙적 유지")
    print("4. 시청자와 적극 소통")
    print()
    
    # 파일 저장
    filename = f"analysis_{channel_name}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"""
YouTube 채널 분석 리포트
========================
채널명: {channel_name}
구독자: {subs:,}명
평균 조회수: {avg_views:,}회
카테고리: {category}

예상 월 수익
============
광고 수익: {int(monthly_ad_revenue):,}원
스폰서십: {int(sponsorship/12):,}원
총 수익: {int(monthly_ad_revenue + sponsorship/12):,}원

추천 전략
=========
1. 규칙적 업로드 (주 2-3회)
2. SEO 최적화
3. 썸네일 개선
4. 커뮤니티 구축
""")
    
    print(f"상세 리포트가 '{filename}'에 저장되었습니다.")
    return filename

# 실행
if __name__ == "__main__":
    print("YouTube 채널 사업성 분석 도구")
    print()
    
    test_channels = [
        "https://www.youtube.com/@로직알려주는남자",
        "https://www.youtube.com/@코딩애플"
    ]
    
    for channel in test_channels:
        try:
            analyze_youtube_channel(channel)
            print("\n" + "=" * 50 + "\n")
        except Exception as e:
            print(f"오류: {e}")
    
    print("분석 완료!")