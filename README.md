# 블렌더 프로젝터 애드온 (Blender Projector Add-on)

블렌더에서 물리 기반 프로젝터를 쉽게 생성하고 관리할 수 있는 애드온입니다. 실제 제조사 렌즈 데이터를 사용하여 현실적인 프로젝션 시뮬레이션을 구현합니다.

[English](readme-en.md) | 한국어

![Projector Add-on for Blender title image](/.github/gifs/title.jpg)

## 기능

* 실제 물리 기반 프로젝터 쉽게 생성 및 조작
* Throw Ratio, 해상도, 렌즈 시프트 등 실제 프로젝터 설정 적용
* 다양한 제조사(Epson, Christie, Sony, Panasonic, Barco 등)의 실제 렌즈 데이터 지원
* 테스트 텍스처 또는 사용자 정의 이미지/비디오 투사
* 사이클 렌더 모드에서 프로젝션 미리보기

## 렌즈 데이터베이스

* 다양한 제조사(Epson, Christie, Sony, Panasonic, Barco, NEC, BenQ, JVC, Optoma, Digital Projection 등)의 실제 렌즈 데이터 포함
* 렌즈 데이터는 공개 자료를 기반으로 작성되었으며, 일부 값은 근사치일 수 있습니다
* **주의사항**: 포함된 JSON 파일의 렌즈 데이터는 참고용으로만 사용하세요. 실제 프로젝트에 적용하기 전에 각 제조사의 최신 기술 사양서를 확인하고 필요한 경우 데이터를 수정하여 사용하세요.

## 레퍼런스

* 이 애드온은 Jonas Schell의 [Blender Projector 애드온](https://github.com/Ocupe/Projectors)을 기반으로 제작되었으며, 실제 프로젝터 렌즈 데이터를 시뮬레이션할 수 있는 렌즈 관리 시스템이 추가되었습니다.

## 미리보기

### Throw Ratio
![Throw Ratio](/.github/gifs/throw_ratio.gif)

### 렌즈 시프트
![Lens Shift](/.github/gifs/lens_shift.gif)

### 이미지 텍스처 & 해상도
![Image Texture & Resolutions](/.github/gifs/image_textures_resolution.gif)

## 호환성
* 블렌더 2.8 이상 버전 지원

## 설치 방법

1. 이 저장소를 ZIP 파일로 다운로드합니다.
2. 블렌더를 실행합니다.
3. `편집 > 기본 설정 > 애드온` 탭으로 이동합니다.
4. `파일에서 설치` 버튼을 클릭하고 다운로드한 ZIP 파일을 선택합니다.
5. 목록에서 "Lighting: Projector" 애드온을 찾아 체크박스를 활성화합니다.

## 문서

* [사용자 매뉴얼](Documents/user-manual-ko.md) - 애드온 사용법 상세 가이드
* [개발자 문서](Documents/developer-docs-ko.md) - 개발자를 위한 기술 문서

## 기여하기

이슈 및 기능 요청은 언제든지 환영합니다. 이 프로젝트에 기여하고 싶다면:

1. 이 저장소를 포크합니다.
2. 새 브랜치를 생성합니다. (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다. (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다. (`git push origin feature/amazing-feature`)
5. Pull Request를 오픈합니다.

## 라이센스

이 프로젝트는 GNU GPL v3 라이센스로 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 연락처

문의사항이나 제안이 있으시면 이슈를 생성하거나 저장소 관리자에게 연락해주세요.

---

P.S. 독일어로는 프로젝터를 'Beamer'라고 부릅니다.
