# K-Food Timer

<div align="center">
  <h3>한국 간편식품 조리 타이머 애플리케이션</h3>
</div>

---

## 📝 소개

K-Food Timer는 한국 간편식품의 조리 시간을 쉽고 편리하게 관리할 수 있는 타이머 애플리케이션입니다. 라면, 냉동식품, 즉석밥 등 다양한 한국 간편식품의 정확한 조리 시간을 관리하고 알림을 받을 수 있습니다.

## ✨ 주요 기능

- 📋 다양한 한국 간편식품 데이터베이스
- ⏱️ 각 제품별 맞춤형 타이머
- 📝 조리 방법 단계별 안내
- ⭐ 즐겨찾기 및 최근 사용 제품 관리
- ⏸️ 타이머 일시정지 및 재개 기능
- 🔔 타이머 완료 시 소리 알림

## 🚀 시작하기

### 필수 조건

- Python 3.6 이상
- 필요한 패키지 (requirements.txt 참조)

### 설치 방법

1. 저장소 클론하기

```bash
git clone https://github.com/yourusername/k-food-timer.git
cd k-food-timer
```

2. 가상 환경 생성 및 활성화 (선택사항)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 실행 방법

```bash
python main.py
```

## 💻 사용법

### 메인 메뉴

애플리케이션을 실행하면 다음과 같은 메인 메뉴가 표시됩니다:

1. 제품 목록 보기
2. 카테고리별 제품 보기
3. 즐겨찾기 제품
4. 최근 사용한 제품
5. 타이머 관리
6. 설정
0. 종료

### 제품 선택 및 타이머 시작

1. 메인 메뉴에서 원하는 옵션을 선택하여 제품 목록을 탐색합니다.
2. 제품을 선택하면 상세 정보가 표시됩니다.
3. "타이머 시작" 옵션을 선택하여 타이머를 시작합니다.
4. 타이머가 완료되면 알림이 표시됩니다.

### 타이머 관리

메인 메뉴의 "타이머 관리" 옵션을 통해 실행 중인 타이머를 관리할 수 있습니다:

- 타이머 일시정지/재개
- 타이머 정지

## 📂 프로젝트 구조

```
K-Food Timer/
├── main.py                  # 앱 진입점
├── modules/                 # 모듈 디렉토리
│   ├── timer_module.py      # 타이머 기능 모듈
│   ├── product_module.py    # 제품 데이터 관리 모듈
│   ├── settings_module.py   # 앱 설정 모듈
│   └── ui_module.py         # UI 관련 모듈
├── data/                    # 데이터 디렉토리
│   ├── products.json        # 제품 데이터
│   └── settings.json        # 앱 설정 데이터
├── tests/                   # 단위 테스트 디렉토리
├── docs/                    # 문서화 디렉토리
└── requirements.txt         # 의존성 패키지 목록
```

## 🧪 테스트

단위 테스트 실행:

```bash
python -m unittest discover tests
```

## 📚 문서화

더 자세한 문서는 [docs/README.md](docs/README.md) 파일을 참조하세요.

## 🔧 설정

설정 메뉴에서 다음과 같은 옵션을 변경할 수 있습니다:

- 소리 알림: 타이머 완료 시 소리 알림 켜기/끄기
- 알림: 타이머 완료 시 화면 알림 켜기/끄기
- 테마: 라이트/다크 테마 선택
- 언어: 한국어/영어 선택

## 📋 제품 데이터

기본 제공되는 제품 데이터:

- 신라면 (라면 카테고리)
- 햇반 (즉석밥 카테고리)
- 비비고 만두 (냉동식품 카테고리)

추가 제품 데이터는 `data/products.json` 파일을 직접 편집하거나, 애플리케이션 내에서 추가할 수 있습니다.

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요. 