# 4코너 보정 기능 개발 계획서

## 1. 프로젝트 개요

### 1.1 목적
블렌더 프로젝터 애드온에 4코너 보정 기능을 추가하여 더 사실적이고 유연한 프로젝션 시뮬레이션을 구현합니다. 이 기능은 사용자가 투사된 이미지의 각 모서리를 독립적으로 조정할 수 있게 하여 실제 프로젝터 설정과 유사한 환경을 제공합니다.

### 1.2 현재 상황 분석
- 기존 프로젝터 애드온은 렌즈 관리 시스템 등 기본 투사 기능을 지원함
- 기본 키스톤 접근 방식(수직/수평 조정)은 다음과 같은 문제점이 있었음:
  - 사다리꼴 효과 구현이 불완전하고 직관적이지 않음
  - 단순 매핑 노드 조작으로는 정확한 키스톤 효과 구현이 어려움
  - 회전, 스케일, 이동을 조합한 방식이 예상대로 작동하지 않음
  - 해상도 문제와 연동되어 더 복잡해짐
- 현재 시스템은 평면 투사에 최적화되어 있음

### 1.3 개발 목표
- 사용자가 각 모서리를 독립적으로 조정할 수 있는 4코너 보정 기능 구현
- 직관적인 UI로 모서리 위치 조정 가능
- 프리셋 시스템으로 편리한 설정 관리 지원
- 기존 코드 구조를 최대한 유지하면서 모듈식 확장

## 2. 새로운 접근 방식

### 2.1. 이전 접근 방식의 문제점
1. **변환 행렬 한계**: 단순 매핑 노드의 변환 행렬만으로는 복잡한 투영 왜곡을 정확하게 표현하기 어려움
2. **간접적인 제어**: 수직/수평 키스톤 값으로 복잡한 변환을 간접적으로 제어하는 방식은 직관적이지 않음
3. **호환성 문제**: 블렌더 버전별로 노드 속성 접근 방식이 다르면서 일관된 효과 구현이 어려움
4. **해상도 문제**: 이미지 텍스처 해상도와 프로젝터 설정 해상도가 동기화되지 않음
5. **노드 그룹 복잡성**: 커스텀 노드 그룹이 블렌더의 기본 기능과 충돌할 가능성 있음

### 2.2. 새로운 접근 방식의 장점
1. **직접적인 모서리 제어**: 사용자가 각 모서리를 직접 드래그하여 원하는 형태로 조정
2. **투영 행렬 사용**: 4개 점의 좌표를 바탕으로 정확한 투영 변환 행렬 계산
3. **단순화된 구현**: 한 번에 4코너 구현에 집중하여 복잡성 감소
4. **실제 프로젝터와 유사한 UI**: 대부분의 프로젝터 소프트웨어가 사용하는 방식과 일치
5. **UV 좌표 직접 변환**: 더 정밀한 텍스처 좌표 변환 가능

## 3. 시스템 설계

### 3.1 모듈 구조
```
projector/
├── (기존 파일들)
└── corner_pin/
    ├── __init__.py       # 모듈 초기화 및 등록
    ├── properties.py     # 4코너 속성 정의
    ├── nodes.py          # 4코너 노드 그룹 생성
    ├── panel.py          # 4코너 UI 패널
    ├── operators.py      # 4코너 관련 오퍼레이터
    └── presets.py        # 프리셋 관리 기능
```

### 3.2 데이터 구조
1. **코너 좌표 저장 방식**
   - 각 모서리(좌상, 우상, 좌하, 우하)의 (x, y) 좌표를 0~1 범위의 정규화된 값으로 저장
   - 기본값: 좌상(0,1), 우상(1,1), 좌하(0,0), 우하(1,0)

2. **변환 행렬 계산**
   - 4개의 코너 좌표를 바탕으로 투영 변환 행렬 계산
   - 변환된 UV 좌표 = 변환 행렬 × 원본 UV 좌표

3. **노드 구조**
   - 기존 매핑 노드 대신 커스텀 UV 변환 노드 그룹 사용
   - 4개의 코너 위치를 직접 입력으로 받는 노드 그룹 설계

### 3.3 기존 코드와의 통합
1. **최소한의 변경점**
   - 기존 keystone 모듈을 건드리지 않고 별도의 corner_pin 모듈로 구현
   - `projector.py` 파일에서 필요한 연결 지점만 추가

2. **모듈식 설계**
   - 4코너 모듈만 활성화/비활성화할 수 있는 독립적 구조
   - 기존 프로젝터 생성 및 관리 로직은 그대로 유지

## 4. 기술적 구현 방안

### 4.1 4코너 노드 그룹 설계
```python
def create_corner_pin_node_group():
    """4코너 보정 노드 그룹 생성"""
    name = 'CornerPinCorrection'
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])
    
    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    
    # 입력 소켓: 텍스처 좌표 + 4개 코너 좌표
    inputs = node_group.inputs
    inputs.new('NodeSocketVector', 'UV')
    inputs.new('NodeSocketVector', 'Top Left')
    inputs.new('NodeSocketVector', 'Top Right')
    inputs.new('NodeSocketVector', 'Bottom Left')
    inputs.new('NodeSocketVector', 'Bottom Right')
    
    # 출력 소켓: 변환된 텍스처 좌표
    outputs = node_group.outputs
    outputs.new('NodeSocketVector', 'UV')
    
    # 노드 생성 및 로직 구현
    # ...
    
    return node_group
```

### 4.2 투영 변환 구현
- 4코너 좌표를 바탕으로 투영 변환 행렬 계산
- 노드 조합으로 복잡한 수식 구현
- 또는 외부 수학 라이브러리를 사용한 계산 결과를 노드에 적용

### 4.3 UI 설계
- 각 모서리를 직접 드래그할 수 있는 시각적 인터페이스
- 또는 각 코너 좌표를 수치로 입력할 수 있는 컨트롤
- 프리셋 저장/로드 기능

## 5. 개발 단계

### 5.1 1단계: 기초 구조 및 속성 구현 (1주)
- Corner Pin 모듈 기본 구조 생성
- 코너 좌표 속성 및 기본 데이터 구조 정의
- 기존 프로젝터 코드와의 통합 지점 확인

### 5.2 2단계: 4코너 노드 그룹 구현 (2주)
- Corner Pin 변환 로직 구현
- 노드 그룹 생성 및 최적화
- 노드 트리 연결 및 기본 테스트

### 5.3 3단계: UI 및 사용자 경험 개선 (2주)
- 직관적인 4코너 조정 인터페이스 구현
- 프리셋 시스템 구현
- 사용성 테스트 및 개선

### 5.4 4단계: 테스트 및 최적화 (1주)
- 다양한 시나리오 테스트
- 성능 최적화
- 버그 수정 및 안정화

## 6. 기술적 도전 및 해결 방안

### 6.1 투영 변환 정확도
- **도전**: 4개 점으로 정의된 임의의 영역으로 텍스처 투영 시 왜곡 문제
- **해결 방안**: 바이큐빅 또는 투영 변환 알고리즘 연구, 외부 라이브러리 참고

### 6.2 노드 기반 구현의 한계
- **도전**: 복잡한 수학 계산을 노드만으로 구현하기 어려움
- **해결 방안**: 핵심 계산은 Python 스크립트로 처리하고 결과만 노드에 적용

### 6.3 해상도 및 텍스처 문제
- **도전**: 이미지 해상도 변경 시 코너 핀 효과가 깨질 가능성
- **해결 방안**: 텍스처 해상도 변경을 감지하고 자동으로 조정하는 메커니즘 구현

## 7. 향후 확장 계획

### 7.1 곡선 보정
- 코너 핀 보정 이후 렌즈 왜곡 같은 비선형 보정 추가

### 7.2 자동 보정
- 카메라로 캡처한 이미지를 분석하여 자동으로 코너 위치 계산

### 7.3 입체 투사
- 3D 오브젝트 표면에 텍스처 투사 기능 확장

## 8. 개발 일정 및 마일스톤

### 8.1 1주차: 기초 설계 및 계획
- 상세 설계 문서 작성
- 개발 환경 설정
- 모듈 구조 생성

### 8.2 2-3주차: 코어 기능 개발
- 4코너 속성 및 데이터 구조 구현
- 투영 변환 로직 구현
- 노드 그룹 생성 및 통합

### 8.3 4-5주차: UI 및 사용자 경험
- 사용자 인터페이스 구현
- 프리셋 시스템 추가
- 초기 테스트 및 피드백 수집

### 8.4 6주차: 테스트 및 안정화
- 다양한 환경에서 테스트
- 버그 수정 및 최적화
- 문서화 및 릴리스 준비

## 9. 결론

4코너 보정 기능은 이전의 키스톤 접근 방식보다 더 직관적이고 유연한 방식으로 프로젝션 왜곡을 제어할 수 있게 합니다. 사용자가 각 모서리를 독립적으로 조정할 수 있어 실제 프로젝터 설정과 더 유사한 환경을 제공하며, 더 복잡한 투사 상황에서도 정확한 시뮬레이션이 가능합니다.

이 프로젝트는 기존 프로젝터 애드온의 기능을 확장하면서, 모듈식 설계로 유지보수와 향후 확장을 용이하게 합니다. 각 개발 단계를 체계적으로 진행하고 지속적인 테스트를 통해 안정적인 기능을 제공할 것입니다.