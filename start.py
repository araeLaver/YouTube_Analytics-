#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YouTube Analytics Studio - 메인 실행 파일
premium_analyzer.py를 실행하는 간단한 런처
"""

import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("YouTube Analytics Studio - 메인 서버 시작")
    print("=" * 60)
    print("주소: http://localhost:8080")
    print("메인 애플리케이션: premium_analyzer.py")
    print("로딩 중...")
    print("=" * 60)
    
    # premium_analyzer.py 실행
    try:
        subprocess.run([sys.executable, "premium_analyzer.py"], check=True)
    except KeyboardInterrupt:
        print("\n서버를 종료합니다...")
    except FileNotFoundError:
        print("premium_analyzer.py 파일을 찾을 수 없습니다.")
        return 1
    except Exception as e:
        print(f"서버 실행 중 오류 발생: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())