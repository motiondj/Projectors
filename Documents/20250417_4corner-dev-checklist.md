# 4코너 보정 기능 개발 체크리스트

## 1. 프로젝트 준비 단계
- [ ] 4코너 보정 기능 관련 개념 및 참고 자료 정리
- [ ] 프로젝터 노드 트리 구조 상세 분석
- [ ] corner_pin 모듈 폴더 구조 생성
- [ ] 개발 환경 설정 (블렌더 버전, 디버깅 환경)
- [ ] 기존 코드베이스 분석 및 코너 핀 적용 지점 파악

## 2. 기본 구조 구현 (1단계)
- [ ] corner_pin 모듈 기본 파일 생성
  - [ ] `__init__.py` - 모듈 초기화
  - [ ] `properties.py` - 코너 좌표 속성 정의
  - [ ] `nodes.py` - 코너 핀 노드 그룹 정의
  - [ ] `panel.py` - UI 패널 구현
  - [ ] `operators.py` - 코너 핀 오퍼레이터 구현
- [ ] 코너 좌표 속성 정의
  - [ ] 활성화 토글 속성 구현
  - [ ] 각 코너 좌표 (좌상, 우상, 좌하, 우하) 속성 구현
  - [ ] 프리셋 관리 속성 구현
- [ ] 코너 핀 UI 패널 기본 구조 구현
  - [ ] 코너 핀 탭 등록
  - [ ] 활성화 토글 버튼 구현
  - [ ] 코너 좌표 입력 필드 구현
- [ ] 기존 코드 수정 최소화하면서 코너 핀 모듈 등록
  - [ ] `__init__.py`에 코너 핀 모듈 등록
  - [ ] `projector.py` 필요한 부분만 연동 지점 추가

## 3. 코너 핀 변환 구현 (2단계)
- [ ] 코너 핀 계산 로직 구현
  - [ ] 4개 코너 좌표를 기반으로 투영 변환 행렬 계산 함수 구현
  - [ ] UV 좌표 변환 함수 구현
  - [ ] 해상도 변화에 대응하는 기능 구현
- [ ] 코너 핀 노드 그룹 구현
  - [ ] 기본 노드 그룹 구조 생성
  - [ ] 입출력 소켓 설정 (UV 좌표 및 코너 위치)
  - [ ] 변환 로직을 노드로 구현
- [ ] 노드 트리 통합
  - [ ] 기존 프로젝터 노드 트리에 코너 핀 노드 삽입 기능
  - [ ] 텍스처 매핑 파이프라인 연결
  - [ ] 기존 노드와의 호환성 확인

## 4. UI 및 사용자 경험 개선 (3단계)
- [ ] 코너 핀 제어 인터페이스 구현
  - [ ] 직관적인 코너 드래그 핸들 구현
  - [ ] 시각적 피드백 시스템 구현
  - [ ] 코너 좌표 수치 입력 필드 개선
- [ ] 프리셋 시스템 구현
  - [ ] 프리셋 저장 기능
  - [ ] 프리셋 불러오기 기능
  - [ ] 기본 프리셋 제공
- [ ] 사용성 개선
  - [ ] 코너 위치 리셋 기능
  - [ ] 화면 비율에 맞춘 조정 기능
  - [ ] 도움말 및 툴팁 추가

## 5. 테스트 및 최적화 (4단계)
- [ ] 다양한 시나리오 테스트
  - [ ] 여러 해상도 테스트
  - [ ] 다양한 코너 위치 조합 테스트
  - [ ] 프리셋 저장/로드 테스트
- [ ] 성능 최적화
  - [ ] 노드 그룹 계산 효율 최적화
  - [ ] 메모리 사용량 최적화
  - [ ] UI 반응성 개선
- [ ] 오류 처리 및 안정성 개선
  - [ ] 예외 상황 처리
  - [ ] 값 범위 검증 및 제한
  - [ ] 잘못된 입력 처리

## 6. 기존 코드 통합 및 최종 조정
- [ ] 관련 모듈 통합 확인
  - [ ] 렌즈 관리 시스템과의 연동
  - [ ] 프로젝터 설정과의 통합
  - [ ] 해상도 설정과의 동기화
- [ ] UI 일관성 확인
  - [ ] 패널 위치 및 스타일 통일
  - [ ] 컨트롤 이름 및 레이블 일관성
  - [ ] 아이콘 및 시각적 요소 확인
- [ ] 문서화
  - [ ] 코드 주석 추가
  - [ ] 사용자 가이드 작성
  - [ ] README 업데이트

## 7. 릴리스 준비
- [ ] 최종 테스트
  - [ ] 다양한 블렌더 버전 테스트
  - [ ] 다양한 OS 환경 테스트
  - [ ] 이전 버전과의 호환성 확인
- [ ] 코드 정리
  - [ ] 디버깅 코드 제거
  - [ ] 코드 스타일 통일
  - [ ] 미사용 코드 정리
- [ ] 릴리스 패키지 준비
  - [ ] 버전 번호 업데이트
  - [ ] 릴리스 노트 작성
  - [ ] 최종 배포 파일 준비

## 8. 향후 개선 계획
- [ ] 곡선 보정 기능 추가 가능성 검토
- [ ] 자동 보정 기능 연구
- [ ] 3D 오브젝트 표면 투사 확장 계획 수립