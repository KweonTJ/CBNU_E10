# CBNU E10 Isaac Sim 월드

`CBNU-E10.mp4`, 사용자 제공 치수, **충북대 공식 E10 외관 사진**으로 만든 월드다. 사용자 요청에 따라 **1–6층 모두 3층의 복도·문·방 구획·계단·소품을 반복**하고 모든 층과 문 뒤 공간에 조명을 배치했다. 촬영된 3층 바닥은 `z=0`이며, E9 저장소 없이 독립적으로 사용할 수 있다.

**[Isaac Sim에서 열 월드: cbnu_e10.usda](worlds/cbnu_e10/cbnu_e10.usda)**

![Isaac Sim E10 외관 렌더](outputs/preview/ExteriorFront.png)

## 열기

Isaac Sim의 `File > Open`에서 다음 파일을 연다.

```text
/home/a/Isaac_Worlds_CBNU_E10/worlds/cbnu_e10/cbnu_e10.usda
```

외관을 보는 기본 viewport와 미리보기 노출 설정으로 새 Isaac Sim 창을 열려면:

```bash
cd /home/a/Isaac_Worlds_CBNU_E10
bash scripts/open_world.sh
```

복도에서 시작하려면 `E10_VIEW=Corridor bash scripts/open_world.sh`를 사용한다. 이 환경변수는 미리보기 시점 데이터만 선택하며 저장 카메라를 추가하지 않는다.

각 층 복도는 `E10_VIEW=CorridorLevel1`부터 `CorridorLevel6`까지 선택한다. 방 안쪽은 `E10_VIEW=RoomFront` 또는 `RoomRear`로 확인할 수 있다. 조명은 USD에 저장되어 있으므로 기본 월드를 다시 열어도 유지된다.

각 층 엘리베이터 옆에 **1F / 1층–6F / 6층 번호판**을 붙였다. 남색 바탕·흰색 큰 글씨이며, 판 크기는 50×70cm, 중심 높이는 해당 층 바닥에서 1.62m다. `E10_VIEW=ElevatorLevel1`부터 `ElevatorLevel6`까지 번호판 앞 시점을 선택할 수 있다.

설치 위치 기본값은 `/home/a/isaacsim`이다. 다른 설치는 `E10_ISAAC_ROOT` 환경변수로 지정한다. GUI 실행 스크립트의 실제 창 실행은 이번 검증에 포함하지 않았으며, 동일 Stage는 Isaac Sim 5.1.0의 headless viewport에서 열고 렌더링했다.

## 치수와 추정 범위

| 항목 | 값 | 근거 |
| --- | --- | --- |
| 복도 벽 사이 폭 | **2.10m** | 사용자 제공 |
| 복도 바닥–천장 높이 | **2.50m** | 사용자 제공 |
| 계단 한 경사 구간의 좌우 폭 | **1.50m** | 사용자 제공 |
| 단높이 | **0.16m** | 사용자 제공 약 16cm |
| 복도 전체 길이 | 38.40m | 영상 배치에 맞춘 모델 추정값; 실측·영상 측량값 아님 |
| 첫 상승 계단 | 13단 | 2–4초 영상에서 추정한 단수 |
| 디딤판 깊이 | 0.28m | 추정값 |
| 계단 도착참 높이 | 상승 +2.08m / 하강 −2.08m | 13 × 0.16m로 계산한 모델값 |
| 입구참·끝참 깊이 | 각 1.20m | 추정값 |
| 건물 외피 | 6층, 본체 약 38.8×15.5m | 공식 사진의 형상에 맞춘 추정 모델 |
| 층간 모듈 | 4.16m | 13단×16cm×2와 맞춘 모델링 가정, 실측 아님 |
| 1층 바닥 / 3층 바닥 / 본체 지붕 | −8.32m / 0m / +16.64m | 위 층간 모듈로 계산; 파라펫은 지붕 위에 추가 |

실측 제약과 추정값은 [layout.json](worlds/cbnu_e10/config/layout.json)의 `measured`, `estimated`로 분리했다. 문 간격·문 개수·화분 공간·엘리베이터 치수도 영상 기반 근사다. 전체 길이를 바꾸면 `doors`, `stairs`, `alcove_x_range` 등 절대 좌표도 함께 조정한다.

각 층에 같은 복도·문 16조(문짝 32개)·방 구획 17곳·화분 공간·계단실 2곳이 있다. 바닥 높이는 1층부터 **−8.32, −4.16, 0, 4.16, 8.32, 12.48m**다. 3층을 제외한 층은 사용자가 요청한 동일 구조 복제이며, 해당 층을 개별 조사해 복원한 것이 아니다. 방 내부는 바닥·천장·구획벽을 갖춘 빈 공간이고 문은 닫힌 정적 형상이다.

## 공식 사진 기반 외관

[충북대 공식 캠퍼스 지도](https://chungbuk.ac.kr/english/selectWebCampusList.do?key=736)의 E10 항목이 연결하는 [건물 사진](https://chungbuk.ac.kr/DATA/campus/20240405022354947_F3Rt.jpg)을 확인했다. 해당 항목의 명칭은 `Electrical & Computer Engineering the 2nd Hall`이며, [로보틱스연구실 공식 홈페이지](https://robotics.cbnu.ac.kr/index.php)에서도 E10을 전자정보2관으로 표기한다.

복도 양옆을 건물 폭으로 연결하고 붉은 벽돌 외벽, 흰색 수평 띠장, 반복 창호, 단부 수직 유리창, 평지붕·파라펫·E10 표지와 출입구 캐노피를 추가했다. 기존 계단실과 화분 공간은 이 건물 외피 안에 들어간다. 원래의 복도·계단 치수와 실내 충돌 형상은 유지한다.


## 모든 공간의 조명

월드에는 활성 광원 **336개**가 있다. 방 구획 102곳에 천장 패널등 180개, 복도·화분 공간·엘리베이터 앞에 90개, 계단에 64개, 외부 태양광과 환경광 2개를 배치했다. 문과 구획벽을 통과하는 빛에 의존하지 않고 각 방 안에 광원을 둔다. 계단은 입구·상승·하강·중간참의 벽등으로 비춘다.

밝기는 [lighting.json](worlds/cbnu_e10/config/lighting.json)에서 조절한다. 수치는 USD 조명 강도이며 실측 조도(lux)가 아니다. 기존 카메라 노출을 유지한 렌더로 밝기를 확인한다.

## 영상에서 반영한 구성

- 긴 직선 복도, 흰 벽, 검정 걸레받이, 테라조 바닥과 녹색 테두리.
- 청록색·흰색 양개문과 세로 창, 끝부분의 유리 분할문, 출입 카드 리더와 방 표시판.
- 작은 원형 천장등, 천장 패널 줄눈, 감지기·배선, 소화기 13개와 소화전함.
- 시작 오른쪽 계단실과 반대편 왼쪽 계단실, 녹색 벽·금속 난간·석재 디딤판.
- 끝부분 오른쪽의 화분 6개·정수기·창문 공간, 목재 마감 엘리베이터와 점자 블록.
- 복도 양 끝 창과 실내측 금속 가드, E10 3F 안내판과 정숙 표지.

| 실제 Isaac Sim 미리보기 | 파일 |
| --- | --- |
| 전체 건물 정면 | [ExteriorFront.png](outputs/preview/ExteriorFront.png) |
| 전체 건물 후면 | [ExteriorRear.png](outputs/preview/ExteriorRear.png) |
| 직선 복도 | [Corridor.png](outputs/preview/Corridor.png) |
| 문 창문 음각 근접 | [DoorRecess.png](outputs/preview/DoorRecess.png) |
| 시작 계단 | [StartStairs.png](outputs/preview/StartStairs.png) |
| 반대편 계단·엘리베이터 앞 | [FarLobby.png](outputs/preview/FarLobby.png) |
| 화분 공간 | [PlantAlcove.png](outputs/preview/PlantAlcove.png) |
| 돌아보는 복도 | [Return.png](outputs/preview/Return.png) |
| 천장을 숨긴 전체 구조 | [Overview.png](outputs/preview/Overview.png) |
| 외벽을 숨긴 6층 내부 | [AllFloors.png](outputs/preview/AllFloors.png) |
| 문 뒤 앞쪽 방 / 뒤쪽 방 | [RoomFront.png](outputs/preview/RoomFront.png) · [RoomRear.png](outputs/preview/RoomRear.png) |
| 1층 / 6층 복도 | [CorridorLevel1.png](outputs/preview/CorridorLevel1.png) · [CorridorLevel6.png](outputs/preview/CorridorLevel6.png) |
| 1층 / 6층 방 조명 | [LightingLevel1.png](outputs/preview/LightingLevel1.png) · [LightingLevel6.png](outputs/preview/LightingLevel6.png) |
| 양 끝 계단 하강 방향 | [StairDownStart.png](outputs/preview/StairDownStart.png) · [StairDownFar.png](outputs/preview/StairDownFar.png) |
| 엘리베이터 옆 층 번호판 | [1층](outputs/preview/ElevatorLevel1.png) · [3층](outputs/preview/ElevatorLevel3.png) · [6층](outputs/preview/ElevatorLevel6.png) |

## 물리와 좌표

단위는 미터, 위쪽은 Z, 복도 진행 방향은 +X다. 영상 시작에서 앞을 보면 왼쪽이 +Y, 오른쪽이 −Y다. 중력은 −Z 방향 9.81m/s²이며 바닥·벽·천장·문·계단·난간·주요 소품은 정적 collider를 갖는다. 계단실 바닥을 통짜 평면으로 덮지 않아 하강 구간이 실제로 열린다.

복도 2.10m는 벽면 기준이며 걸레받이·손잡이·소화기 등은 벽 앞에 돌출된다. 중앙 **폭 1.30m, z=0.15–2.00m** 범위의 통행 공간과 계단 중심선 위 2m 여유를 검사했다.

`/World/SpawnPoints`는 로봇을 배치할 기준 Xform이며 로봇 자체는 포함하지 않는다.

기존 `/World/Floor`, `/World/Doors` 등의 경로는 3층 원본이다. 다른 층은 `/World/Levels/Level_N` 아래에서 이를 내부 참조하므로 같은 형상을 유지한다. 해당 층의 `SpawnPoints`에는 층 높이가 적용된다.

| Spawn | 위치 (x, y, z), m | 방향 |
| --- | --- | --- |
| CorridorStart | (4.4, 0, 0.55) | +X |
| CorridorReturn | (31.0, 0, 0.55) | −X |
| StartStairApproach | (3.24, −1.65, 0.55) | −Y |
| FarStairApproach | (35.16, 1.65, 0.55) | +Y |

0.55m는 로봇 기준점의 예시 높이이므로 실제 로봇의 초기 자세에 맞춰 조정한다.

## 재생성과 검증

```bash
python3 -B scripts/make_textures.py
bash scripts/usd_python.sh scripts/build_world.py
bash scripts/usd_python.sh scripts/validate_world.py
bash scripts/render_headless.sh
```

텍스처 생성에는 시스템 Python의 NumPy·Pillow, USD 생성·정적 검사에는 Isaac Sim에 포함된 OpenUSD를 사용한다. Isaac Sim을 실행하는 마지막 명령은 GPU가 필요하며 미리보기와 PhysX 검사 결과를 갱신한다. 생성된 USD를 직접 고치면 재생성 때 덮어써지므로 치수는 JSON, 형상은 생성 스크립트에서 수정한다.

2026-11-09 KST 확인:

- USD 합성, 제공 치수, 6층 복도·문·방 조명, 문 상부 틈, 계단·층간 연결, 통행 공간, 2m 머리 위 여유, 재질·의존성, 카메라 제거·소품 경계: **정적 검사 95개 PASS**.
- Isaac Sim 실제 Stage 렌더: **26개 시점 저장**. 6개 층의 복도·방을 포함한다.
- 번호판 추가 후에는 1–6층 엘리베이터와 복도에서 **7개 시점을 재촬영**하고 층별 번호·텍스처 연결을 확인했다. 신규 시점 6개를 합쳐 미리보기 파일은 32개다.
- 각 층 복도·양쪽 방, 중간참 연결 10곳, 3층 계단 대표 디딤판과 화분 공간: **구체 낙하 42개 + PhysX raycast 42개 PASS**.
- 위 PhysX 결과는 번호판 추가 전 검증이다. 번호판 추가 후 모든 충돌 형상·변환·물리 재질·중력 설정의 해시가 동일함을 확인하여 물리 실험을 반복하지 않았다.
- 위 검증은 월드 형상과 물리 지지면에 대한 확인이다.

근거: [정적 검사 JSON](outputs/validation/static_validation.json), [렌더·PhysX 검사 JSON](outputs/preview/capture_status.json), [소품 경계 검사 JSON](outputs/validation/containment_validation.json), [생성 manifest](worlds/cbnu_e10/build_manifest.json). 정적·PhysX 보고서에는 검사한 Stage의 SHA-256을 기록한다. 런타임 로그는 `outputs/runtime/isaac_capture.log`에 저장된다.

최신 번호판 변경 근거: [번호 확인](outputs/validation/floor_marker_validation.json), [7시점 렌더](outputs/preview/render_refresh.json), [물리 형상 불변 비교](outputs/validation/floor_marker_physics_comparison.json).

## 디렉토리 범위

이 저장소는 E10 디지털 트윈 월드 전용이다. USD·텍스처·배치 설정·참고 이미지·월드 생성/렌더/형상 검증 도구와 결과를 보관한다. `worlds/`와 `assets/`를 함께 유지하면 E9·강화학습 저장소 없이 사용할 수 있다.

강화학습 코드·모델·로봇 제어·평가 CSV·실행 로그는 [HimLoco 연구 프로젝트](/home/a/HimLoco-AMP-Lab_UROP_II/experiments/cbnu_locomotion/README.md)에서 관리한다. 사용자 후속 요청에 따라 **주행 영상·스크린샷·다운로드 ZIP은 이 월드의 `outputs/recordings/`에 보관**한다. 학습 코드·모델과 연결용 심볼릭 링크는 두지 않는다.

## 근거와 변경 기록

- [영상 검토 및 구현](docs/1_cbnu_e10_world.md)
- [저장 카메라 제거·소품 경계](docs/2_camera_removal_fixture_containment.md)
- [공식 사진 기반 외관](docs/3_official_photo_exterior.md)
- [문 창문 음각](docs/4_recessed_door_windows.md)
- [6층 조명·문·계단 연결](docs/5_six_floor_lighting_and_doors.md)
- [엘리베이터 옆 층 번호판](docs/6_elevator_floor_markers.md)
- [월드 전용 디렉토리 분리](docs/7_world_repository_scope.md)

## 주행 영상

| 모델·조건 | E9 | E10 |
| --- | --- | --- |
| 새 model_14601 · 복도 목표 3.0m/s | [영상](outputs/recordings/model14601_e10_e9_20261109/deliverables/E9_driving.mp4) · [사진 12장](outputs/recordings/model14601_e10_e9_20261109/deliverables/E9_screenshots) | [영상](outputs/recordings/model14601_e10_e9_20261109/deliverables/E10_driving.mp4) · [사진 12장](outputs/recordings/model14601_e10_e9_20261109/deliverables/E10_screenshots) |
| 기존 model_14001 · 복도 목표 3.0m/s | [영상](outputs/recordings/corridor3_e10_e9_20261109/deliverables/E9_driving.mp4) | [영상](outputs/recordings/corridor3_e10_e9_20261109/deliverables/E10_driving.mp4) |
| 기존 model_14001 · 복도 목표 1.2m/s | [영상](outputs/recordings/stable_e10_e9_20261109/deliverables/E9_driving.mp4) | [영상](outputs/recordings/stable_e10_e9_20261109/deliverables/E10_driving.mp4) |

새 모델 영상은 1080p·25fps이며 선택한 완주본이다. E9 상승은 첫 실패 후 seed 43 재시도 본이며 실패 원본도 보존한다. 기존 평가에서 촬영한 영상은 `outputs/recordings/evaluation/` 아래에 있다. 입력·CSV·검증 JSON은 HimLoco에 유지하고 [미디어 보관 변경 기록](docs/8_driving_media_storage.md)에 경로와 검증을 기록한다.
