# K-Food Timer 테스트 가이드

이 디렉토리에는 K-Food Timer 애플리케이션의 자동화된 테스트가 포함되어 있습니다.

## 테스트 구조

- `test_product_module.py`: 제품 데이터 모델 및 관리 기능에 대한 단위 테스트

## 테스트 실행 방법

### 모든 테스트 실행

프로젝트 루트 디렉토리에서 다음 명령어를 실행합니다:

```bash
python -m unittest discover tests
```

### 특정 테스트 모듈 실행

```bash
python -m unittest tests.test_product_module
```

### 특정 테스트 클래스 실행

```bash
python -m unittest tests.test_product_module.TestProduct
```

### 특정 테스트 메서드 실행

```bash
python -m unittest tests.test_product_module.TestProduct.test_product_validation
```

## 테스트 커버리지 확인

테스트 커버리지를 확인하려면 먼저 `coverage` 패키지를 설치해야 합니다:

```bash
pip install coverage
```

다음 명령어로 커버리지 보고서를 생성할 수 있습니다:

```bash
# 커버리지 측정과 함께 테스트 실행
coverage run -m unittest discover tests

# HTML 보고서 생성
coverage html

# 커버리지 요약 확인
coverage report
```

HTML 보고서는 `htmlcov` 디렉토리에 생성되며, 웹 브라우저에서 확인할 수 있습니다.

## 테스트 작성 가이드

새로운 테스트를 작성할 때는 다음 가이드라인을 따라주세요:

1. 테스트 이름은 명확하게 작성하고, 테스트하려는 기능이나 시나리오를 이름에 반영합니다.
2. 각 테스트는 독립적이어야 하며, 다른 테스트의 실행 결과에 영향을 받지 않아야 합니다.
3. `setUp()` 메서드에서 테스트에 필요한 환경을 구성하고, `tearDown()` 메서드에서 정리합니다.
4. `self.assert*` 메서드를 사용하여 테스트 결과를 검증합니다.
5. 테스트 코드에도 주석을 달아 다른 개발자가 테스트의 목적과 방법을 이해할 수 있게 합니다.

## 고급 테스트 기법

### 모의 객체 (Mock) 사용

외부 시스템에 의존하는 테스트의 경우 `unittest.mock` 모듈을 사용하여 모의 객체를 생성할 수 있습니다:

```python
from unittest.mock import Mock, patch

# 외부 함수나 메서드를 모킹
@patch('modules.product_module.os.path.exists')
def test_something_with_mock(mock_exists):
    # 모의 객체 설정
    mock_exists.return_value = True
    
    # 테스트 실행
    result = some_function_that_uses_os_path_exists()
    
    # 검증
    self.assertTrue(result)
    mock_exists.assert_called_once_with('/expected/path')
```

### 매개변수화된 테스트

여러 입력 값에 대해 동일한 테스트를 실행해야 하는 경우, `parameterized` 패키지를 사용할 수 있습니다:

```bash
pip install parameterized
```

```python
from parameterized import parameterized

class TestExample(unittest.TestCase):
    @parameterized.expand([
        ("case1", 1, 2, 3),
        ("case2", 4, 5, 9),
        ("case3", -1, 1, 0),
    ])
    def test_add(self, name, a, b, expected):
        self.assertEqual(a + b, expected)
``` 