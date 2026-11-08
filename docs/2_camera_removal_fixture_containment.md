# E10 카메라 제거와 소품 실내 정렬

- 날짜: 2026-11-09 (Asia/Seoul)
- 요청: 월드의 카메라 삭제, 벽 바깥으로 돌출된 장애물을 안쪽으로 정리
- 이전: [1. E10 월드 제작](1_cbnu_e10_world.md)
- 결과: [기본 USD](../worlds/cbnu_e10/cbnu_e10.usda), [README](../README.md)
- 후속: [외관 추가](3_official_photo_exterior.md), [문 창문 음각](4_recessed_door_windows.md). 아래 collider 406개는 외관 추가 이전의 실내 기준이며 현재 전체 개수는 생성 manifest를 따른다.

## 변경

저장된 카메라 6개와 `/World/Cameras` 그룹, 기본 및 구조 확인 레이어의 카메라 설정 metadata를 제거했다. 촬영 시점은 `build_manifest.json`의 숫자 데이터로 유지하고, 미리보기 카메라는 session layer에만 생성한다. 재생성해도 Camera prim이 저장되지 않는다.

소품의 원점이 아니라 실제 메시와 기본 도형의 world bounding box를 검사했다. 벽을 침범하거나 벽면 여유가 부족한 화분 3개는 잎·화분·줄기를 함께 이동했다.

| 소품 | 이동량 (x, y), m | 최종 조건 |
| --- | --- | --- |
| Plant_00 | (+0.0833, +0.0513) | 잎 포함 벽면 여유 최소 0.08m |
| Plant_03 | (−0.1071, 0) | 잎 포함 벽면 여유 최소 0.08m |
| Plant_05 | (+0.2342, 0) | 잎 포함 벽면 여유 최소 0.08m |

양 끝 창의 유리·창틀·가드를 실내측에 배치하고, 화분 공간 창틀과 엘리베이터 목재 마감·문·표시부·벽등을 안쪽으로 맞췄다. 소화전함과 경보 장치도 벽면 안쪽으로 정렬했다. 경보 장치는 벽 방향에 맞는 축으로 고쳤다. 벽과 복도 폭·높이, 계단 치수는 유지한다.

## 파일과 함수

- [build_world.py](../scripts/build_world.py): `Builder.__init__`, `review_views`, `contain_group`, `plant`, `end_window`, `lobby`, `build`, `main`.
- [capture_and_check.py](../scripts/capture_and_check.py): `main`에서 `/ReviewCameras`를 session layer에만 생성.
- [open_world.py](../scripts/open_world.py): 저장된 카메라를 찾는 대신 기본 viewport를 session layer에서 설정.
- [inspect_containment.py](../scripts/inspect_containment.py): `allowed_rectangles`, `inspect_fixtures`, `main`으로 소품의 실제 형상 경계 검사.
- [validate_world.py](../scripts/validate_world.py): 기본·구조 확인 Stage의 카메라 0개와 소품 실내 포함 여부 검사 추가.

## 검증

- 기본 월드·구조 확인 Stage 모두 **Camera prim 0개**.
- `/World/Fixtures` 아래 Gprim **316개**의 수평 경계가 복도 또는 화분 공간 내부에 포함. 허용 오차 1mm, 돌출 형상 **0개**.
- 기존 치수·통행·계단 여유·충돌·의존성 검사와 새 검사 합계 **70개 PASS**, 정적 collider **406개** 유지.
- 최종 USD의 실제 Isaac Sim 렌더와 PhysX 낙하·raycast 결과는 [capture_status.json](../outputs/preview/capture_status.json)에 기록한다. 로봇 보행 시험을 뜻하지 않는다.
- 근거: [정적 검사](../outputs/validation/static_validation.json), [소품 경계 검사](../outputs/validation/containment_validation.json), [생성 manifest와 실제 이동량](../worlds/cbnu_e10/build_manifest.json).

문은 벽 개구부에 들어가는 건축 형상이며, 소품 경계 검사는 `Fixtures` 아래 전체 형상에 적용했다. 창과 엘리베이터 마감도 소품 경계 검사에 포함했다. 구조 벽·지붕·계단실 외곽을 잘라내어 통과시키지 않았다.
