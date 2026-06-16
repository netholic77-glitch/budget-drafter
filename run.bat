@echo off
chcp 65001 > nul
cd /d "%~dp0"

REM 가상환경이 없으면 생성
if not exist ".venv\Scripts\python.exe" (
    echo [*] 최초 실행 - 가상환경을 생성합니다...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERROR] Python이 설치되어 있지 않거나 PATH에 없습니다.
        echo https://www.python.org/downloads/ 에서 Python 3.11+ 설치 필요.
        pause
        exit /b 1
    )
)

REM 가상환경 활성화 후 의존성 설치 (최초 1회만)
call ".venv\Scripts\activate.bat"

if not exist ".venv\installed.flag" (
    echo [*] 필요 패키지를 설치합니다 (1~2분 소요)...
    pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] 패키지 설치 실패. 인터넷 연결을 확인하세요.
        pause
        exit /b 1
    )
    echo. > ".venv\installed.flag"
)

echo.
echo ==========================================================
echo  예산분석보고서 초안 작성기 실행 중...
echo  브라우저가 자동으로 열립니다. (http://localhost:8501)
echo  종료하려면 이 창을 닫거나 Ctrl+C 를 누르세요.
echo ==========================================================
echo.

streamlit run app.py
pause
