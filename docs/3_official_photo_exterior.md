# E10 공식 외관 사진 기반 건물 외피

- 날짜: 2026-11-09 (Asia/Seoul)
- 요청: 긴 통로에 계단실 상자를 붙인 모습에서 E9처럼 정돈된 건물 외관으로 수정; 인터넷 자료 확인
- 상위: [README](../README.md)
- 이전: [카메라 제거·소품 정렬](2_camera_removal_fixture_containment.md)
- 다음: [문 창문 음각](4_recessed_door_windows.md)

## 근거

1. [충북대 공식 캠퍼스 지도](https://chungbuk.ac.kr/english/selectWebCampusList.do?key=736)의 공개 `loadData`에서 `buldNo=E10`, `campusNo=188`, `Electrical & Computer Engineering the 2nd Hall`을 확인했다.
2. 이 항목이 지정한 [공식 E10 사진](https://chungbuk.ac.kr/DATA/campus/20240405022354947_F3Rt.jpg)을 내려받아 직접 확인했다. 사진에 E10 표기, 붉은 벽돌 6층 외형, 층별 창호, 흰색 띠장과 수직 유리창이 보인다.
3. [충북대 로보틱스연구실](https://robotics.cbnu.ac.kr/index.php)의 E10 전자정보2관 표기로 건물 명칭을 교차 확인했다.

참고 사진: [원본 JPEG](../reference/exterior/cbnu_official_e10.jpg). 조사 출처와 확인 범위: [sources.json](../reference/exterior/sources.json). 사진 촬영일은 확인하지 않았으며 조회일은 2026-11-09다. 검색 중 함께 나온 다른 대학의 E10 사진은 사용하지 않았다.

## 구현 범위

복도 양옆에 방 측 바닥·천장·구획벽을 연결하고 그 바깥에 하나의 닫힌 건물 외피를 둘렀다. 원래 측면으로 나왔던 계단실과 화분 공간은 건물 폭 안에 포함된다. 외부에는 벽돌 외벽, 반복 창호, 층별 밝은 띠장, 양 끝 수직 유리창, 평지붕과 파라펫, E10 표지, 캐노피와 포장면을 배치했다.

3층 복도 바닥 z=0과 기존 실내 치수는 유지했다. 외관은 6층, 본체 폭·깊이 약 38.8×15.5m다. 층간 높이 4.16m는 13단×16cm×2와 일관되게 만든 **모델 가정**이다. 1층 바닥은 −8.32m, 본체 지붕 기준은 +16.64m이며 끝부분 지붕·파라펫은 더 높다.

사진으로 건물의 정확한 길이·깊이·층고나 촬영 복도의 실제 방위를 복원한 것은 아니다. 후면 창 배열도 추정이다. 다른 층은 외피만 만들었고, 실제 층간 이동·방 내부·엘리베이터 작동은 구현하지 않았다. 인접 E9 건물과 차량·정류장 등은 추가하지 않았다.

## 변경 파일과 검증

- [exterior.json](../worlds/cbnu_e10/config/exterior.json): 출처·관찰 사실·추정 치수·제한 사항.
- [build_exterior.py](../scripts/build_exterior.py): `Envelope.panel`, `window`, `elevation`, `tower`, `wings`, `roofs`, `build`로 외피 생성. `wings`는 계단 구간을 비워 하강 공간에 슬래브가 생기지 않게 한다.
- [build_world.py](../scripts/build_world.py): 외관 재질·생성기 연결, 별도 외관 검토 시점 데이터. Camera prim은 저장하지 않는다.
- [make_textures.py](../scripts/make_textures.py): 절차적 벽돌 재질과 E10 표지. 공식 사진을 텍스처로 붙이지 않았다.
- [capture_and_check.py](../scripts/capture_and_check.py): 외관 정면·후면 렌더 추가, 임시 카메라는 숨김 session layer에서만 사용.
- [validate_world.py](../scripts/validate_world.py): 6층 외피와 통합 기초 외곽 검사 추가.

최종 정적 검사 74개 PASS, 실내 소품 형상 316개 모두 벽 안쪽, 저장 카메라 0개다. 실제 Isaac Sim 렌더와 PhysX 낙하·raycast 28개 결과는 [검증 JSON](../outputs/preview/capture_status.json)에 최종 Stage 해시와 함께 저장한다. [정적 결과](../outputs/validation/static_validation.json) · [정면 렌더](../outputs/preview/ExteriorFront.png) · [후면 렌더](../outputs/preview/ExteriorRear.png).

구조 확인용 `cbnu_e10_overview.usda`는 실내 검토를 위해 외피와 천장의 표시를 숨긴다. 외관을 확인할 때는 기본 `cbnu_e10.usda`를 연다.
