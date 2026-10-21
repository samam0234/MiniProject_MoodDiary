# 서버 연결·포트 이슈 기록 — 2026-10-22

## 1. Reflex 와 Django 의 기본 포트 충돌 (설계 단계에서 방지)
- **상황**: 인수인계 문서는 Reflex 3000 / Django 8000 이라고 하지만, Reflex 는 프론트(3000) 외에 **내부 백엔드를 기본 8000** 으로 띄운다.
- **영향**: 둘을 함께 실행하면 한쪽이 기동에 실패한다.
- **조치**: `frontend/rxconfig.py` 에서 `backend_port=8001` 로 분리. 인수인계 §4 와 README, 실행 가이드에 반영.

## 2. `reflex run` 종료 후에도 8001 포트가 점유됨 (실제 발생)
- **증상**: 사용자가 `reflex run` 을 실행했더니 기동이 안 됨.
- **원인**: 작업자(에이전트)가 기동 확인용으로 띄운 `reflex run` 을 끌 때 부모 프로세스만 종료했고, 8001 을 잡은 자식 워커(`multiprocessing.spawn` 프로세스)가 남았다. 부모가 사라진 뒤에도 소켓이 유지됨.
- **확인 방법**
  ```powershell
  Get-NetTCPConnection -LocalPort 8001 -State Listen   # OwningProcess 가 이미 사라진 부모 PID 로 보일 수 있다
  Get-CimInstance Win32_Process | ? { $_.ParentProcessId -eq <그 PID> }   # 자식 워커 찾기
  ```
- **조치**: `taskkill /PID <자식 PID> /T /F`. 이후 `reflex run` 이 3000/8001 에서 정상 기동하고 종료 후 점유 0 임을 확인.
- **재발 방지**: Reflex 를 종료할 때는 항상 프로세스 트리 전체(`/T`)를 종료한다. 기동 확인 후에는 3000/8001 점유와 잔여 프로세스를 점검한다.

## 3. `.venv` 미활성화로 인한 실행 실패
- **증상**: `ModuleNotFoundError: flask` 등, `flask`/`reflex` 명령 없음.
- **원인**: 의존성은 프로젝트 `.venv` 에만 설치되어 있고 시스템 Python 에는 없다.
- **조치/예방**: 터미널마다 `.\.venv\Scripts\Activate.ps1` 선행. `Docs/guidance/RUN_GUIDE.md` 의 문제 해결 표에 정리.
