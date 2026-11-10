# 7. E10 디지털 트윈 월드 전용 디렉토리 분리

- 날짜: 2026-11-09 (Asia/Seoul).
- 요청: 학습·모델·보행 실험을 HimLoco로 옮기고 E10은 월드 전용으로 유지.
- 연구 자료: [HimLoco CBNU 보행 프로젝트](/home/a/HimLoco-AMP-Lab_UROP_II/experiments/cbnu_locomotion/README.md).

현재 규칙: 후속 요청에 따라 **주행 영상·사진·ZIP은 E10에 보관**한다. [미디어 보관 변경](8_driving_media_storage.md) 참조. 아래는 최초 분리 당시 기록이다.

E10의 학습·평가·분석·주행 촬영 결과와 연구 스크립트·정책 설정·연구 문서 7–14를 연구 저장소로 이동했다. 파일 1,702개·8,755,556,605바이트의 이동 전후 해시가 일치했다. 월드 파일과 연구용 자료를 연결하는 심볼릭 링크는 남기지 않았다.

이 디렉토리에는 USD·텍스처·배치 설정·참고 이미지, 월드 생성/열기/렌더/형상 검증 스크립트 13개, 월드 미리보기·runtime·validation과 월드 문서만 둔다. README의 학습·보행 상세 내용은 연구 프로젝트로 분리했다.

기존 월드·assets·reference·월드 도구·미리보기·검증 파일의 해시는 그대로이며 정적 검사 95개를 통과했다. 이 작업에서 월드 형상이나 물리 설정을 변경하지 않았다. 전체 이관 검증과 실행 방법은 [연구 변경 기록 15](/home/a/HimLoco-AMP-Lab_UROP_II/experiments/cbnu_locomotion/docs/15_research_repository_migration.md)에 기록한다.
