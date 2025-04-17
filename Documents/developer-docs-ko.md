# 블렌더 프로젝터 애드온 개발자 문서

[English Version](developer-docs-en.md)

## 목차
1. [소개](#소개)
2. [프로젝트 구조](#프로젝트-구조)
3. [코어 모듈](#코어-모듈)
4. [렌즈 관리 시스템](#렌즈-관리-시스템)
5. [데이터 구조](#데이터-구조)
6. [API 문서](#api-문서)
7. [확장 가이드](#확장-가이드)
8. [테스트 및 디버깅](#테스트-및-디버깅)

## 소개

블렌더 프로젝터 애드온은 블렌더에서 실제 프로젝터의 물리적 특성을 시뮬레이션하는 도구입니다. 이 개발자 문서는 애드온의 내부 구조와 작동 방식을 이해하고 확장하는 데 필요한 정보를 제공합니다.

### 개발 환경

- 블렌더 버전 호환성: 2.8 이상
- 파이썬 버전: 3.7 이상
- 추가 종속성: 없음 (블렌더 내장 파이썬 환경만 사용)

## 프로젝트 구조

애드온의 전체 구조는 다음과 같습니다:

```
projector/
├── __init__.py           # 애드온 진입점
├── projector.py          # 핵심 프로젝터 기능
├── ui.py                 # 프로젝터 UI
├── operators.py          # 오퍼레이터 구현
├── helper.py             # 유틸리티 함수
├── tests.py              # 테스트 코드
└── lens_management/      # 렌즈 관리 시스템
    ├── __init__.py       # 렌즈 모듈 초기화
    ├── database.py       # 데이터 로드 및 관리
    ├── properties.py     # 렌즈 속성 정의
    ├── panel.py          # 프로젝터 탭용 패널
    ├── operators.py      # 렌즈 관련 오퍼레이터
    ├── manager_panel.py  # 렌즈 관리 탭용 패널
    └── database/         # 렌즈 데이터 파일
        ├── epson.json    # 엡손 렌즈 데이터
        ├── panasonic.json # 파나소닉 렌즈 데이터
        ├── christie.json # 크리스티 렌즈 데이터
        ├── barco.json    # 바코 렌즈 데이터
        └── sony.json     # 소니 렌즈 데이터
```

### 주요 파일 설명

- **`__init__.py`**: 애드온 메타데이터 및 등록/해제 함수
- **`projector.py`**: 프로젝터 생성, 설정 관리, 노드 트리 구성 등의 핵심 기능
- **`ui.py`**: 블렌더 UI 패널 및 관련 요소
- **`operators.py`**: 프로젝터 생성, 삭제 등의 오퍼레이터
- **`helper.py`**: 유틸리티 함수 모음
- **`lens_management/`**: 렌즈 관리 시스템 모듈
  - **`database.py`**: 렌즈 데이터베이스 로드 및 관리 기능
  - **`properties.py`**: 블렌더 속성 정의 및 업데이트 콜백
  - **`panel.py`**: 프로젝터 탭에 통합된 렌즈 선택 UI
  - **`operators.py`**: 렌즈 관련 오퍼레이터 (추가, 편집, 삭제 등)
  - **`manager_panel.py`**: 렌즈 관리 전용 탭 UI

## 코어 모듈

### 프로젝터 생성 및 설정

프로젝터는 `projector.py`의 `create_projector()` 함수로 생성됩니다. 이 함수는 다음 작업을 수행합니다:

1. 스포트라이트와 카메라 객체 생성
2. 스포트라이트를 카메라의 자식으로 설정
3. 스포트라이트에 커스텀 노드 트리 추가
4. 프로젝터 설정 초기화 (`init_projector()` 호출)

```python
def create_projector(context):
    # 스포트라이트 생성
    bpy.ops.object.light_add(type='SPOT', location=(0, 0, 0))
    spot = context.object
    # 설정...
    add_projector_node_tree_to_spot(spot)
    
    # 카메라 생성
    bpy.ops.object.camera_add(...)
    cam = context.object
    
    # 부모 설정
    spot.parent = cam
    
    return cam
```

### 노드 트리 시스템

프로젝터의 핵심 기능은 스포트라이트에 적용된 복잡한 노드 트리를 통해 구현됩니다:

- **텍스처 매핑**: 투영 이미지를 3D 공간에 매핑
- **픽셀 그리드**: 해상도 시각화를 위한 그리드 오버레이
- **이미지 믹싱**: 체커, 컬러 그리드, 커스텀 텍스처 간 전환

### 업데이트 함수

주요 프로젝터 설정은 해당 업데이트 함수에 의해 처리됩니다:

- `update_throw_ratio()`: throw ratio 및 관련 카메라 설정 업데이트
- `update_lens_shift()`: 렌즈 시프트 및 텍스처 매핑 업데이트
- `update_resolution()`: 해상도 변경 처리
- `update_projected_texture()`: 투사 텍스처 변경 처리
- `update_checker_color()`: 체커 텍스처 색상 업데이트
- `update_pixel_grid()`: 픽셀 그리드 표시 전환

## 렌즈 관리 시스템

렌즈 관리 시스템은 실제 제조사의 렌즈 데이터를 로드하고 프로젝터 설정에 적용하는 기능을 제공합니다.

### 데이터베이스 관리

`LensDatabase` 클래스(`database.py`)는 JSON 파일에서 렌즈 데이터를 로드하고 관리합니다:

```python
class LensDatabase:
    def __init__(self):
        self.manufacturers = {}
        self.cache = {}
        self.last_load_time = {}
        self.load_all_databases()
    
    def load_all_databases(self):
        # 모든 JSON 파일 로드
        
    def get_manufacturers(self):
        # 제조사 목록 반환
    
    def get_models(self, manufacturer):
        # 특정 제조사의 모델 목록 반환
    
    def get_lens_profile(self, manufacturer, model):
        # 특정 렌즈의 프로필 데이터 반환
```

### 속성 시스템

`properties.py`는 렌즈 선택을 위한 Blender 속성과 업데이트 콜백을 정의합니다:

```python
class LensManagerProperties(bpy.types.PropertyGroup):
    manufacturer: EnumProperty(
        name="Manufacturer",
        items=get_manufacturers,
        update=update_manufacturer
    )
    
    model: EnumProperty(
        name="Model",
        items=get_models,
        update=update_lens_settings
    )
```

### 프로젝터 연동

렌즈 데이터는 `update_from_lens_profile()` 함수를 통해 프로젝터 설정에 적용됩니다:

```python
def update_from_lens_profile(projector_obj, lens_profile):
    # 렌즈 프로필 데이터를 기반으로 프로젝터 설정 업데이트
    # throw ratio, 렌즈 시프트 등의 제한 값 설정
```

프로젝터 설정은 렌즈의 물리적 제한에 따라 조정됩니다:
- 슬라이더 범위 제한 (hard_min, hard_max)
- 범위를 벗어나는 값 조정 (force_within_limits)
- 시각적 피드백 제공 (UI 경고)

## 데이터 구조

### JSON 스키마

렌즈 데이터는 다음 구조의 JSON 파일로 저장됩니다:

```json
{
  "MODEL_NUMBER": {
    "specs": {
      "focal_length": {"min": 값, "max": 값, "default": 값},
      "throw_ratio": {"min": 값, "max": 값, "default": 값},
      "f_stop": {"min": 값, "max": 값, "default": 값},
      "lens_shift": {
        "h_shift_range": [최소%, 최대%],
        "v_shift_range": [최소%, 최대%]
      },
      "supported_resolutions": ["1920x1080", "3840x2160", ...],
      "notes": "부가 설명"
    },
    "optical_properties": {
      "distortion": 값,
      "chromatic_aberration": 값,
      "vignetting": 값
    }
  }
}
```

### 데이터 변환

데이터베이스에서 로드된 값은 다양한 변환 함수를 통해 블렌더에서 사용 가능한 형식으로 변환됩니다:

- `parse_throw_ratio()`: throw ratio 문자열을 최소/최대 값으로 파싱
- `percent_to_blender_shift()`: 퍼센트 단위 시프트를 블렌더 단위로 변환
- `throw_ratio_to_focal_length()`: throw ratio를 초점 거리로 변환

## API 문서

### 블렌더 통합

### 코어 API

#### 프로젝터 생성 및 관리

- `create_projector(context)`: 새 프로젝터 객체 생성 및 반환
- `init_projector(proj_settings, context)`: 프로젝터 설정 초기화
- `update_from_lens_profile(projector_obj, lens_profile)`: 렌즈 프로필 데이터를 프로젝터에 적용
- `is_within_lens_limits(projector_obj)`: 프로젝터 설정이 렌즈 제한 내에 있는지 확인

#### 유틸리티 함수

- `get_projectors(context, only_selected=False)`: 씬의 모든 또는 선택된 프로젝터 객체 가져오기
- `get_projector(context)`: 현재 선택된 프로젝터 가져오기
- `get_resolution(proj_settings, context)`: 현재 사용 중인 해상도 가져오기

### 렌즈 관리 API

#### 데이터베이스 접근

- `lens_db.get_manufacturers()`: 제조사 목록 가져오기
- `lens_db.get_models(manufacturer)`: 특정 제조사의 모델 목록 가져오기
- `lens_db.get_lens_profile(manufacturer, model)`: 특정 렌즈 프로필 가져오기
- `lens_db.get_throw_ratio_limits(manufacturer, model)`: throw ratio 제한 값 가져오기
- `lens_db.get_lens_shift_limits(manufacturer, model, is_horizontal=True)`: 렌즈 시프트 제한 값 가져오기

#### 데이터 관리

- `lens_db.add_manufacturer(name)`: 새 제조사 추가
- `lens_db.add_lens_model(manufacturer, model_id, specs)`: 새 렌즈 모델 추가
- `lens_db.update_lens_model(manufacturer, model_id, specs)`: 렌즈 모델 정보 업데이트
- `lens_db.delete_lens_model(manufacturer, model_id)`: 렌즈 모델 삭제
- `lens_db.import_database(filepath)`: JSON 파일에서 렌즈 데이터 가져오기
- `lens_db.export_database(filepath, manufacturer=None)`: 렌즈 데이터를 JSON 파일로 내보내기
- `lens_db.refresh_database()`: 데이터베이스 새로고침

## 확장 가이드

### 새 기능 추가하기

렌즈 관리 시스템을 확장하려면 다음 단계를 따르세요:

1. **새 데이터 필드 추가**:
   - `database.py`의 `standardize_lens_data()` 함수 수정
   - 새 필드가 포함된 JSON 스키마 업데이트
   - `properties.py`에 새 블렌더 속성 추가

2. **새 UI 요소 추가**:
   - `panel.py` 또는 `manager_panel.py`에 새 UI 요소 추가
   - 필요한 경우 새 패널 클래스 정의

3. **새 기능 로직 구현**:
   - 필요한 함수를 적절한 모듈에 추가
   - 업데이트 콜백 함수 구현

### 광학 시뮬레이션 확장

향후 구현될 광학 왜곡 시뮬레이션을 위한 확장 가이드:

1. **새 노드 그룹 생성**:
   ```python
   def create_optical_effects_node_group():
       # 왜곡, 색수차, 비네팅 효과를 위한 노드 그룹 생성
   ```

2. **렌즈 프로필 속성 연결**:
   ```python
   def apply_optical_properties(profile, projector_obj):
       # 렌즈 프로필의 광학 특성 속성을 노드 그룹에 연결
   ```

3. **UI 컨트롤 추가**:
   ```python
   class OPTICAL_PT_effects_panel(Panel):
       # 광학 효과 컨트롤을 위한 UI 패널
   ```

### 새 제조사 및 렌즈 데이터 추가

새 제조사나 렌즈 데이터를 영구적으로 추가하려면:

1. `lens_management/database/` 디렉토리에 `[manufacturer].json` 파일 생성
2. 다음과 같은 구조로 데이터 작성:
   ```json
   {
     "MODEL_ID": {
       "specs": {
         "focal_length": {"min": 18.0, "max": 25.0, "default": 21.0},
         "throw_ratio": {"min": 1.2, "max": 1.7, "default": 1.45},
         ...
       },
       "optical_properties": {
         ...
       }
     }
   }
   ```
3. 애드온 재시작 또는 `refresh_database()` 호출

## 테스트 및 디버깅

### 테스트 프레임워크

애드온은 기본 테스트 프레임워크를 포함하고 있습니다:
- `tests.py` 파일에 정의된 단위 테스트
- `cmd.py`를 통한 다양한 블렌더 버전 대상 테스트 실행

```python
# 테스트 실행
python cmd.py test
```

### 디버깅 팁

1. **콘솔 로그 활성화**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **데이터 검증 오류 확인**:
   ```python
   errors = lens_db.validate_database()
   if errors:
       print("Database validation errors:", errors)
   ```

3. **무한 재귀 방지**:
   업데이트 함수에서 무한 재귀를 방지하기 위한 플래그 사용:
   ```python
   if getattr(update_function, '_is_updating', False):
       return
   update_function._is_updating = True
   try:
       # 업데이트 로직
   finally:
       update_function._is_updating = False
   ```

4. **캐시 메커니즘**:
   문제 해결 시 캐시 초기화:
   ```python
   # 캐시 초기화
   clear_cache()
   ```
