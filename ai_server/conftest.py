import os

# 로컬 .env 가 EMOTION_BACKEND=ollama 여도 테스트는 실제 LLM 을 호출하지 않는다.
# (app 이 import 될 때 load_dotenv 가 실행되지만, 이미 설정된 환경 변수는 덮어쓰지 않는다.)
os.environ["EMOTION_BACKEND"] = "lexicon"
