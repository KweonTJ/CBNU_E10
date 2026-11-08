# E10 엘리베이터 옆 층 번호판

- 날짜: 2026-11-09 (Asia/Seoul)
- 요청: 층을 구분할 수 있도록 엘리베이터 옆에 번호판 부착.
- 상위: [README](../README.md)
- 이전: [6층 내부·조명·문 상부](5_six_floor_lighting_and_doors.md)

각 층 엘리베이터 옆에 큰 `1F / 1층`부터 `6F / 6층` 번호판을 붙였다. 남색 바탕에 흰색 숫자를 사용하고, 상단에는 E10을 작게 표시했다. 판 크기는 50×70cm, 중심 높이는 각 층 바닥에서 1.62m다. 복도에서 다가오는 쪽에 배치하고 기존 벽등·호출 버튼·안내판과 겹치지 않게 했다.

## 수정 파일

- [make_textures.py](../scripts/make_textures.py): 여섯 층의 번호판 텍스처 생성.
- [build_world.py](../scripts/build_world.py) `make_materials`, `lobby`, `review_views`: 번호판 재질과 알루미늄 받침, 엘리베이터 옆 배치, 각 층 촬영 시점.
- [build_levels.py](../scripts/build_levels.py): 복제된 층마다 번호판 재질·텍스처·층 번호 속성을 해당 층 값으로 변경.
- [capture_and_check.py](../scripts/capture_and_check.py): 엘리베이터 시점의 가로 화면 설정.

3층의 번호판 경로는 `/World/Fixtures/Elevator/FloorMarker`이며, 다른 층은 `/World/Levels/Level_N/Fixtures/Elevator/FloorMarker`다. 재생성해도 층별 표기가 유지된다.

## 검증

- [층 번호 확인](../outputs/validation/floor_marker_validation.json): 6개 층의 번호·표시 문구·연결 텍스처·높이 일치.
- [정적 검사](../outputs/validation/static_validation.json): 95개 PASS. 저장 카메라 0개.
- [소품 경계](../outputs/validation/containment_validation.json): 번호판 포함 1,908개 형상, 벽 밖 돌출 0개.
- [실제 렌더](../outputs/preview/render_refresh.json): 층별 엘리베이터 6곳과 복도 접근 시점, 총 7개 촬영.
- [물리 비교](../outputs/validation/floor_marker_physics_comparison.json): 모든 collider 속성·월드 변환·물리 재질·PhysicsScene 설정의 SHA-256이 추가 전후 동일. 충돌 형상은 5,116개로 유지했다. 기존 PhysX 84개 PASS 보고서는 보존하고 물리 실험은 재실행하지 않았다.

[1층](../outputs/preview/ElevatorLevel1.png) · [2층](../outputs/preview/ElevatorLevel2.png) · [3층](../outputs/preview/ElevatorLevel3.png) · [4층](../outputs/preview/ElevatorLevel4.png) · [5층](../outputs/preview/ElevatorLevel5.png) · [6층](../outputs/preview/ElevatorLevel6.png) · [복도에서 접근](../outputs/preview/FarLobby.png)

이미 열어 둔 Stage는 [기본 월드](../worlds/cbnu_e10/cbnu_e10.usda)를 다시 열어 반영한다.
