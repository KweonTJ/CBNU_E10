# CBNU E10 영상 기반 Isaac Sim 월드 제작

- 날짜: 2026-11-09 (Asia/Seoul)
- 상태: USD 제작, headless 렌더, 정적·PhysX 지지면 검증 완료
- 상위: [README](../README.md)
- 입력: [CBNU-E10.mp4](/home/a/Downloads/CBNU-E10.mp4), 사용자 제공 치수 210cm·250cm·150cm·약 16cm
- 제작 방식 참고: [기존 E9 README](/home/a/Isaac_Worlds_CBNU_E9/README.md). E9 원본은 수정하지 않았다.

## 영상 관찰과 모델 결정

| 영상 시간 | 확인한 내용 | 모델 반영 |
| --- | --- | --- |
| 0초, 6–32초 | 좁고 긴 직선 복도, 양쪽 연구실 문, 녹색 바닥 테두리, 소화기 | 폭 2.1m·높이 2.5m, 문·천장등·테라조·걸레받이 |
| 2–4초 | 시작부 오른쪽 계단실, 왼쪽 상승·오른쪽 하강, 금속 난간 | 상승 13단 추정, 1.5m 폭·16cm 높이, 하강 및 끝참은 추정 완성 |
| 34–38초 | 진행 오른쪽으로 들어가는 창가 화분 공간과 정수기 | 복도 외측 3×3m 공간, 식물·정수기·창 |
| 40–46초 | 왼쪽 계단 출입구, 오른쪽 엘리베이터와 목재 마감, 점자 블록 | 두 번째 계단실, 엘리베이터, 노란 점자 타일 |
| 48초 | E10 3F 안내판, 돌아보는 긴 복도 | 촬영층은 3층으로 기록하되 로컬 바닥 z=0 |
| 76–80초 | 처음 계단 주변으로 복귀, 반대편 창과 가드 | 복도 왕복 동선과 끝 창·실내측 난간 |

대표 근거: [시작 계단 2초](../reference/frame_002s.jpg), [직선 복도 16초](../reference/frame_016s.jpg), [화분 공간 36초](../reference/frame_036s.jpg), [끝부분 40초](../reference/frame_040s.jpg), [3층 안내판 48초](../reference/frame_048s.jpg).

복도 전체 길이 38.4m, 디딤판 깊이 28cm, 13단, 계단실 깊이와 문 배치는 **실측되지 않은 모델링 값**이다. 단안 영상으로 건물의 정확한 치수나 전체 평면도를 복원했다고 해석하지 않는다. 끝 계단과 하강 구간의 가려진 내부는 시작 계단 치수를 재사용했다. 상하층 실내·방 내부·문 및 엘리베이터 작동은 범위 밖이다.

## 수정 파일과 함수

| 파일 | 주요 함수·역할 | 이유 |
| --- | --- | --- |
| [layout.json](../worlds/cbnu_e10/config/layout.json) | `measured`, `estimated`, `stairs`, `doors`, `evidence` | 제공 치수와 추정을 구분하고 수정 위치를 하나로 모음 |
| [build_world.py](../scripts/build_world.py) | `Builder.floor`, `ceiling`, `walls`, `door`, `stairs`, `lobby`, `cameras` | 상대경로 재질과 정적 충돌을 가진 USD 생성 |
| [make_textures.py](../scripts/make_textures.py) | `main` | 반복 가능한 테라조·천장·안내판 재질 |
| [extract_reference.py](../scripts/extract_reference.py) | `main` | 원본 영상의 2초 간격 증거 프레임 추출 |
| [validate_world.py](../scripts/validate_world.py) | `main`, `contains` | 합성 Stage의 실제 치수, 의존성, 보행 공간 검사; 경사 메시의 실제 내부 검사 |
| [capture_and_check.py](../scripts/capture_and_check.py) | `main` | 실제 Isaac Sim 6시점 렌더·동적 구체 지지면·PhysX raycast 검사 |
| [open_world.py](../scripts/open_world.py) | `open_world` | GUI에서 복도 카메라·렌더와 같은 노출로 열기 |
| [usd_python.sh](../scripts/usd_python.sh), [render_headless.sh](../scripts/render_headless.sh), [open_world.sh](../scripts/open_world.sh) | 실행 진입점 | 로컬 Isaac Sim 경로를 환경변수로 변경 가능하게 함 |

기존 사용자 파일 `.vscode/settings.json`은 변경하지 않았다. 생성물은 [기본 USD](../worlds/cbnu_e10/cbnu_e10.usda), [구조 확인 USD](../worlds/cbnu_e10/cbnu_e10_overview.usda), `assets/textures/`다.

## 검증

- 정적 검사 **67개 PASS**: 미터·Z축·기본 prim, 복도 폭/높이, 계단 52개 디딤판의 폭/깊이/높이, 끝참 접속, 유효 collider와 재질, 중앙 1.3m 통행 공간, 계단 중심선 위 2m 여유, 외부 참조 누락 없음, PhysicsScene 1개, 불필요한 동적 강체 없음.
- Isaac Sim 5.1.0 / RTX 3080에서 실제 렌더 **6시점**을 저장했다. 첫 렌더의 부족한 조도를 보정하고 원본 영상과 복도·계단·끝부분 배치를 육안 비교했다.
- 지지면 14곳에 반지름 5.5cm·질량 0.1kg 구체를 놓고 낙하 안정 위치를 확인했다. 같은 지지면의 raycast 14개도 검사했다. 테스트 구체는 session layer에만 추가해 배포 USD에 남지 않는다.
- [정적 검증 결과](../outputs/validation/static_validation.json), [PhysX·렌더 결과](../outputs/preview/capture_status.json)는 해당 USD의 SHA-256을 함께 기록한다.
- 설치된 Isaac Sim의 무관한 HTTP 확장에서 `click` 모듈 누락, ROS2 `rclpy` 경고가 있었으나 월드 로드·6시점 렌더·28개 물리 검사는 완료했다. 해당 확장은 수정하지 않았다.

첫 정적 검사에서 경사 지지 슬래브의 축 정렬 경계 상자가 빈 공간까지 포함하는 오탐을 발견했다. 폐합 메시의 실제 내부를 검사하도록 수정한 후 통과했다. 형상을 지워 검사를 우회하지 않았다.

**이번 작업에 Go2 로봇 정책, 실제 계단 주행, LiDAR/카메라 센서 출력 검증은 포함하지 않았다.**

## 다음에 보정할 값

1. 복도 전체 길이와 각 문 위치를 실측하면 JSON의 절대 좌표를 보정한다.
2. 시작 계단 단수·디딤판 깊이와 반대편 계단 치수를 확인한다.
3. 상하층 동선이 필요하면 추가 영상 또는 치수에 맞춰 끝참 이후를 확장한다.
4. 실제 로봇 asset과 정책을 선택한 뒤 평지 왕복·계단 상승·하강을 별도로 검증한다.

원본 영상은 `/home/a/Downloads/CBNU-E10.mp4`에 보존한다. Obsidian에는 영상 복사 없이 이 변경 기록과 정지 화면 링크만 연결한다.
