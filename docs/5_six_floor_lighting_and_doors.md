# E10 모든 층 내부·조명·문 상부 수정

- 날짜: 2026-11-09 (Asia/Seoul)
- 상위: [README](../README.md)
- 이전: [문 창문 음각](4_recessed_door_windows.md)
- 요청: 모든 층과 문 뒤 공간에 조명 추가, 다른 층도 3층과 동일하게 제작, 문 위 남은 공간을 문으로 채움.

## 변경 결과

1–6층의 복도·문·빈 방 구획·소품·조명·계단을 3층 구조로 통일했다. 3층 경로는 유지하고 다른 층은 `/World/Levels/Level_N` 아래의 내부 USD 참조로 만든다. 층 안내판은 각 층 번호로 바꿨다. 3층 외 층은 개별 실측이 아니라 사용자 요청에 따른 반복 모델이다.

각 층 문 16조·문짝 32개·방 구획 17곳이며, 전체 문짝은 192개, 방 구획은 102곳이다. 방의 바닥·천장·구획벽과 조명을 함께 복제했다. 각 방 내부에 직접 조명이 있어 닫힌 문에 가려도 실내를 비춘다.

| 광원 | 개수 |
| --- | ---: |
| 방 천장 패널 | 180 |
| 복도·화분 공간·엘리베이터 앞 | 90 |
| 계단 입구·경사 구간·중간참 벽등 | 64 |
| 환경광·태양광 | 2 |
| 합계 | **336** |

문짝 높이를 2.10m에서 2.26m로 늘려 상부 프레임 하단과 맞추고 상부 유리 구간을 제거했다. 모든 문짝 위에 열린 틈이 없으며 기존 창의 음각 깊이(유리 35.5mm·창틀 9.5mm)는 유지했다.

두 계단실에서 각각 다섯 층간 연결을 만든다. 13단×0.16m의 두 경사 구간을 잇는 중간참의 중앙 18cm 틈을 채우고, 횡단을 막던 칸막이 끝과 난간을 정리했다. 모든 층의 계단과 연결 중간참 위 2m 공간을 검사했다. 1층 지하 방향은 바닥으로 막았으며 6층의 위쪽 진입은 난간으로 막았다. 6층의 빈 계단 공간은 아래층 도착 구간의 머리 위 여유를 위해 유지했다.

## 수정 파일과 함수

- [build_levels.py](../scripts/build_levels.py) `build_levels`: 층별 참조·높이, 1층/6층 끝 마감, 층간 연결 정보, 층별 안내판 재질.
- [build_lighting.py](../scripts/build_lighting.py) `build_lighting`, `panel`: 실제 바닥과 구획벽에서 방 범위를 구하고, 방별 천장등과 계단 벽등 배치.
- [build_world.py](../scripts/build_world.py) `Builder.door`, `stairs`, `build`, `review_views`: 문 상부 채움, 연결 가능한 계단, 전체 층 생성과 미리보기.
- [make_textures.py](../scripts/make_textures.py): 1–6층 안내판 생성.
- [lighting.json](../worlds/cbnu_e10/config/lighting.json): 공간별 조명 강도. 실제 조도 측정값이 아닌 USD 강도다.
- [validate_world.py](../scripts/validate_world.py), [inspect_containment.py](../scripts/inspect_containment.py): 모든 층의 문·조명·소품·계단 연결 검사.
- [capture_and_check.py](../scripts/capture_and_check.py): 층별 복도·방·하강 계단 렌더, 각 층 바닥과 층간 중간참의 물리 검사. `E10_CAPTURE_VIEWS`를 지정하면 해당 시점만 다시 촬영하며 별도 `render_refresh.json`에 기록한다.

## 검증 결과

- 최종 월드: 13,942 prim, 정적 collider 5,116개, 저장 카메라 0개.
- [정적 검사](../outputs/validation/static_validation.json): **95개 PASS**. 192개 문 창 음각·문 상부 틈 0개, 102개 방별 조명, 6층 치수, 연결 중간참 10곳 포함.
- [실내 소품 검사](../outputs/validation/containment_validation.json): 1,896개 형상, 벽 밖 돌출 0개.
- [PhysX 검사](../outputs/preview/capture_status.json): 42개 위치의 구체 낙하 + 같은 지지면 raycast, **84개 PASS**.
- 실제 렌더 26개 시점 저장. 노출값을 올리지 않고 USD 광원을 추가한 상태에서 방·복도·계단의 가시성을 확인했다.
- 최종 USD와 manifest·정적 검사·PhysX 보고서의 SHA-256이 일치한다.

대표 화면: [6개 층 구조](../outputs/preview/AllFloors.png), [방 안쪽](../outputs/preview/RoomFront.png), [6층 복도](../outputs/preview/CorridorLevel6.png), [문 상부](../outputs/preview/DoorRecess.png), [하강 계단](../outputs/preview/StairDownFar.png).

Go2 정책이나 실제 로봇 주행은 실행하지 않았다. 방은 빈 구획이며 문과 엘리베이터는 정적 형상이다. 이미 열어 둔 Stage는 기본 월드 파일을 다시 열어 반영한다.
