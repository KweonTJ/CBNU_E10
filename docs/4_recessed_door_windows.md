# E10 문 창문 음각 수정

- 날짜: 2026-11-09 (Asia/Seoul)
- 요청: 문 표면에서 양각으로 돌출된 모든 창을 음각으로 수정
- 상위: [README](../README.md)
- 이전: [외관 수정](3_official_photo_exterior.md)

## 형상 변경

연구실 문 16개, 문짝 32개의 창을 수정했다. 원래의 통짜 문짝 위에 유리판을 얹는 형상을 없애고, 각 문짝을 좌우 기둥·창 아래·창 위의 네 부분으로 나눠 실제 창 구멍을 만들었다.

문짝 로컬 좌표에서 문 표면은 y=0.0075m다. 창틀의 가장 앞면은 y=0.017m, 유리 앞면은 y=0.043m이므로 각각 **9.5mm·35.5mm 음각**이다. 문이 복도 양쪽에 회전 배치되어 있어도 문 자체의 좌표에서 이 관계를 유지한다. 문 두께 55mm 안에 유리의 뒷면까지 들어간다.

창 구멍 뒤를 기존 문짝 면이 막지 않는다. 큰 유리 분할문의 가로대도 같은 깊이로 넣었다. 유리에는 정적 충돌을 두어 닫힌 문이 물리적으로 관통되지 않게 했고, 손잡이의 돌출은 유지했다.

## 파일과 검증

- [build_world.py](../scripts/build_world.py)의 `Builder.door`: 문짝 분할, 안쪽 창틀, 안쪽 유리 및 분할대 생성.
- [validate_world.py](../scripts/validate_world.py): 32개 유리와 창틀의 문 표면 대비 깊이 및 문짝 배면이 창을 막지 않는지 확인.
- [capture_and_check.py](../scripts/capture_and_check.py): `DoorRecess` 근접 렌더 추가. 시점은 session layer에만 생성하며 배포 월드에는 저장하지 않는다.
- **32개 창 전부 음각 검사 PASS**, 창 개구부를 막는 문짝 면 **0개**. 전체 정적 검사 **74개 PASS**.

[근접 렌더](../outputs/preview/DoorRecess.png) · [정적 검증 JSON](../outputs/validation/static_validation.json) · [최종 렌더·PhysX 결과](../outputs/preview/capture_status.json).
