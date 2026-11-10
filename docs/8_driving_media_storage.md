# 8. 주행 영상의 월드 디렉토리 보관

- 날짜: 2026-11-09 (Asia/Seoul).
- 요청: 주행 영상은 Isaac 월드 디렉토리에 유지.
- 위치: [outputs/recordings](../outputs/recordings).

주행 영상 40개를 포함한 미디어 193개·7,475,707,586바이트를 E10에 돌려두었다. 영상·스크린샷·ZIP을 보관하며 기존 상대 구조를 유지한다. 보행 평가 영상은 outputs/recordings/evaluation에 둔다. 이동 전후 SHA-256이 일치하고 재인코딩이나 모델 변경은 없다.

학습 코드·모델·입력·평가 CSV·실행 로그·검증 JSON은 HimLoco에 유지한다. 향후 촬영 프로세스 종료 후 영상만 E10으로 옮기고, 사진·모음 영상·ZIP도 E10에 생성하도록 연구 도구를 수정했다. 단위 검사 25개와 준비 실행 4개를 통과했다.

[최신 새 모델 E9 영상](../outputs/recordings/model14601_e10_e9_20261109/deliverables/E9_driving.mp4) · [E10 영상](../outputs/recordings/model14601_e10_e9_20261109/deliverables/E10_driving.mp4) · [전체 ZIP](../outputs/recordings/model14601_e10_e9_20261109/E10_E9_model14601_driving.zip).

파일·함수 변경과 원본 해시·검증은 [연구 변경 기록 16](/home/a/HimLoco-AMP-Lab_UROP_II/experiments/cbnu_locomotion/docs/16_driving_media_storage.md)에 기록한다.
