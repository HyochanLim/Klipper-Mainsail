# CMYKW 5채널 출력 MVP

이 저장소는 다섯 개의 필라멘트 채널을 혼합하는 프린터를 위한
OrcaSlicer 기반 커스텀 프레임워크 사용법을 설명합니다.

```text
C = Cyan (시안)
M = Magenta (마젠타)
Y = Yellow (노랑)
K = Black (검정)
W = White (흰색)
```

OrcaSlicer에서 슬라이스한 G-code는 일반 G-code와 달리, 압출 명령 뒤에
`A/B/C/D/H` 값을 붙여 각 색상 필라멘트를 얼마나 압출할지(mm 단위) 모터
이동량으로 출력합니다. Klipper는 G-code를 한 줄씩 파싱해 해당 모터를
지정된 거리만큼 움직입니다.

목표는 메시 색상을 하나의 일반 익스트루더에 매핑하는 것이 아닙니다. 슬라이서는
모델의 색상 정보를 유지하고, 각 필라멘트 색상을 CMYKW 혼합 비율로 변환한 뒤
생성된 G-code에 채널별 압출량을 기록합니다.

소프트웨어 스택은 세 부분으로 구성됩니다.

- `OrcaSlicer/`: CMYKW 압출 비율과 이동 거리를 반영한 G-code를 생성합니다.
- `C:\Users\user\Desktop\klipper\klipper`: 추가 채널 축을 받아들이는
  커스텀 Klipper 펌웨어를 실행합니다.
- `C:\Users\user\Desktop\klipper\mainsail`: 웹 UI에서 CMYKW 채널 상태를
  표시합니다.

## 현재 MVP 상태

이 프로젝트는 소프트웨어 MVP입니다. 슬라이서, 펌웨어, UI 상태 패널은
갖춰져 있지만, 실제 프린터에서는 하드웨어 셋업과 `printer.cfg` 설정이
추가로 필요합니다.

아래 검증이 실제 기기에서 모두 통과해야 합니다.

1. 커스텀 Klipper 포크가 프린터 호스트에서 실행 중이다.
2. `printer.cfg`에 다섯 개의 물리 필라멘트 모터가 올바르게 매핑되어 있고,
   나머지 핀 매핑도 올바르게 설정되어 있다.
3. `REGISTER_CMYKW_AXES`가 Klipper 오류 없이 성공한다.
4. 수동 테스트 명령으로 예상한 모터가 움직인다.

   ```gcode
   G1 A1 B1 C1 D1 H1 F300
   ```

5. OrcaSlicer가 생성한 G-code가 정상적으로 시작되고, 아래와 같은 채널 이동을
   포함한다.

   ```gcode
   G1 X100 Y100 E10 A2 B3 C4 D1 H0
   ```

## OrcaSlicer 변경 사항

OrcaSlicer 포크는 색상 기반 G-code 출력 주변에 CMYKW 혼합 지원을 추가했습니다.

주요 동작:

- 슬라이서가 필라멘트 색상에 대한 CMYKW 혼합 비율을 계산합니다.
- 생성된 G-code는 논리적 총 압출량으로 일반 `E` 압출을 유지합니다.
- 실제 채널 모터 이동은 같은 이동(move)에 추가 축으로 출력됩니다.
- 생성된 G-code는 아래 축 매핑을 사용합니다.

  ```text
  A = Cyan (시안)
  B = Magenta (마젠타)
  C = Yellow (노랑)
  D = Black (검정)
  H = White (흰색)
  ```

- 미리보기에는 색상 비율과 출력 시간, 필라멘트 사용량, 낭비, 비용 등 기존
  출력 통계를 보여 주는 `CMYKW` 요약 팝업이 포함됩니다.

슬라이서 내부의 비율 순서는 `C, M, Y, W, K`이지만, UI와 G-code 표시는
`C, M, Y, K, W`로 읽어야 합니다. 혼합 배열 관련 코드를 수정할 때는 이 점에
주의하세요.

## Klipper 요구 사항

프린터는 커스텀 Klipper 포크를 실행해야 합니다. 이 프로젝트에서 사용하는
채널 축 변경이 포함되지 않은 일반 upstream Klipper 설치본으로는 부족합니다.

실제 `printer.cfg`는 이 저장소에 포함되어 있지 않습니다. 보통 프린터 호스트에
있으며, 예를 들면 다음과 같습니다.

```text
~/printer_data/config/printer.cfg
```

또는 구형 설정에서는:

```text
~/klipper_config/printer.cfg
```

아래 샘플 파일을 시작점으로 사용하세요.

```text
C:\Users\user\Desktop\klipper\klipper\config\sample-cmykw-channel-axis.cfg
```

샘플을 그대로 복사하지 마세요. 샘플의 핀 이름은 placeholder입니다. 실제
컨트롤러 보드와 배선에 맞게 최소한 아래 값들을 수정해야 합니다.

- `step_pin`
- `dir_pin`
- `enable_pin`
- `rotation_distance`
- 히터 핀
- 서미스터 핀
- 센서 타입
- 베드 크기, 엔드스톱, 홈잉, 그리고 일반 프린터 설정의 나머지 항목

CMYKW 모터는 `manual_stepper`로 설정합니다.

```ini
[manual_stepper c_motor]
[manual_stepper m_motor]
[manual_stepper y_motor]
[manual_stepper k_motor]
[manual_stepper w_motor]
```

일반 `[extruder]` 섹션도 유지해야 하지만, 이 MVP에서는 노즐 히터, 서미스터,
Klipper 논리 압출 검사용으로 사용합니다. 다섯 개의 물리 필라멘트 모터는
위의 manual stepper입니다.

## 필수 Klipper 매크로

출력 전에 `printer.cfg`에서 CMYKW 축을 등록해야 합니다.

```ini
[gcode_macro REGISTER_CMYKW_AXES]
gcode:
  MANUAL_STEPPER STEPPER=c_motor SET_POSITION=0
  MANUAL_STEPPER STEPPER=m_motor SET_POSITION=0
  MANUAL_STEPPER STEPPER=y_motor SET_POSITION=0
  MANUAL_STEPPER STEPPER=k_motor SET_POSITION=0
  MANUAL_STEPPER STEPPER=w_motor SET_POSITION=0
  MANUAL_STEPPER STEPPER=c_motor GCODE_AXIS=A
  MANUAL_STEPPER STEPPER=m_motor GCODE_AXIS=B
  MANUAL_STEPPER STEPPER=y_motor GCODE_AXIS=C
  MANUAL_STEPPER STEPPER=k_motor GCODE_AXIS=D
  MANUAL_STEPPER STEPPER=w_motor GCODE_AXIS=H
```

출력 시작 매크로에서 이를 호출해야 합니다.

```ini
[gcode_macro START_PRINT]
gcode:
  REGISTER_CMYKW_AXES
  # 여기에 일반 홈잉, 가열, 베드 메시, 퍼지, 기타 시작 단계를 추가하세요.
```

OrcaSlicer 머신 시작 G-code에서 아래를 호출하도록 설정하세요.

```gcode
START_PRINT
```

OrcaSlicer가 `T0`, `T1` 등을 출력한다면, 생성된 G-code에 등장할 수 있는
툴 번호에 대해 no-op 매크로를 유지하세요.

```ini
[gcode_macro T0]
gcode:
  G4 P0
```

OrcaSlicer 프로필에서 출력될 수 있는 모든 툴 번호에 대해 반복하세요.

## Mainsail 변경 사항

Mainsail은 여전히 UI 계층입니다. 혼합 비율을 계산하지 않으며 CMYKW 압출을
직접 제어하지도 않습니다.

Mainsail에는 `CMYKW Channels` 대시보드 패널만 추가했습니다. Klipper의
추가 축을 사람이 읽을 수 있는 채널 상태로 표시합니다.

```text
A -> Cyan (시안)
B -> Magenta (마젠타)
C -> Yellow (노랑)
D -> Black (검정)
H -> White (흰색)
```

패널은 아래 Klipper 상태를 읽습니다.

- `printer.gcode_move.axis_map`
- `printer.gcode_move.gcode_position`
- `printer.toolhead.extra_axes`
- `printer.toolhead.position`

또한 설정용 `REGISTER_CMYKW_AXES` 버튼을 제공합니다. 이 버튼은 혼합 제어가
아니라 등록/설정 동작으로 취급해야 합니다. 출력 중에는 패널이 읽기 전용입니다.

웹캠, 콘솔, 온도, 진행률, G-code 파일, 로그, 툴헤드 제어 등 기존 Mainsail
패널은 변경하지 않습니다.

## 중요 사용 규칙

MVP에서는 아래를 지켜 주시길 바랍니다다.

- 물리 필라멘트 튜브 순서를 축 매핑과 일치시킵니다.
- CMYKW 채널 이동 전에 `REGISTER_CMYKW_AXES`를 실행합니다.
- OrcaSlicer 아크 피팅(arc fitting)을 비활성화합니다.
- 이 MVP에서는 슬라이서 pressure advance 출력을 비활성화합니다.
- 필라멘트 없이, 또는 모터가 기계적으로 안전한 상태에서 테스트를 시작합니다.
- 실제 출력 전에 각 채널 모터 방향을 하나씩 확인합니다.
- 생성된 G-code의 압출 이동에 `A/B/C/D/H`가 포함되는지 확인합니다.

펌웨어 경로를 먼저 확장하지 않는 한 아래는 하지 마세요.

- 이 G-code 형식은 CMYKW 프린터 전용입니다. 다른 프린터에 사용하면
  호환되지 않습니다.
- `A/B/C/D/H`를 다른 Klipper manual stepper에 재사용하지 마세요.
- Klipper 아크 확장이 CMYKW 축을 보존한다고 가정하지 마세요.
- 일반 pressure advance가 다섯 채널 축에도 적용된다고 가정하지 마세요.
- stock Mainsail 패널로 런타임 혼합 비율을 편집하지 마세요.
- `T0`, `T1` 등은 실제 모터 명령이 아닙니다. 디버깅과 가독성을 위한 매크로이므로 임의로 삭제하지 마세요.

## Initial 셋업 체크리스트

1. 프린터 호스트에 커스텀 Klipper 포크를 설치하거나 전환합니다.
2. 프린터 호스트에서 실제 `printer.cfg`를 작성하거나 수정합니다.
3. 실제 핀으로 다섯 개의 `[manual_stepper ...]` 섹션을 추가합니다.
4. `REGISTER_CMYKW_AXES`를 추가합니다.
5. `START_PRINT`가 `REGISTER_CMYKW_AXES`를 호출하도록 설정합니다.
6. Klipper를 재시작합니다.

   ```gcode
   FIRMWARE_RESTART
   ```

7. 아래를 실행합니다.

   ```gcode
   REGISTER_CMYKW_AXES
   ```

8. 채널을 작게 움직여 테스트합니다.

   ```gcode
   G1 A1 F300
   G1 B1 F300
   G1 C1 F300
   G1 D1 F300
   G1 H1 F300
   ```

9. Mainsail에서 CMYKW 축이 등록된 것으로 표시되는지 확인합니다.
10. 작은 단색 객체를 슬라이스하고 생성된 G-code를 검사합니다.
11. 축 매핑, 모터 방향, 가열, 홈잉을 확인한 뒤에만 출력합니다.

## Before bug report

Klipper가 `A`, `B`, `C`, `D`, `H`에 대해 unknown command를 보고하면 축이
등록되지 않은 것입니다. `REGISTER_CMYKW_AXES`를 실행하고 매크로를 확인하세요.

특정 채널이 움직이지 않으면 아래를 확인하세요.

- 해당 `[manual_stepper ...]` 섹션
- 핀 이름
- enable 극성
- 모터 배선
- `rotation_distance`
- 올바른 `GCODE_AXIS`로 축이 등록되었는지 여부

잘못된 필라멘트 채널이 움직이면 모터 배선이나 축 매핑이 잘못된 것입니다.
OrcaSlicer를 먼저 수정하지 말고 Klipper의 모터-채널 매핑을 고치세요.

Mainsail에 CMYKW 패널이 보이지 않으면 Klipper가 `REGISTER_CMYKW_AXES`
매크로 또는 `gcode_move.axis_map`의 추가 축을 노출하는지 확인하세요.

G-code에 `G2` 또는 `G3` 아크 이동이 포함되어 있으면 이 MVP에서는 슬라이서
아크 피팅을 비활성화하세요.

G-code에 pressure advance 설정이 포함되어 있으면 이 MVP에서는 슬라이서
pressure advance 출력을 비활성화하세요.

## Patch notes

변경 범위는 작게 유지하세요. 이 프로젝트는 아직 MVP이므로, 새로운 추상화보다
설정 기반 동작과 단순한 상태 UI를 우선하세요.

현재 역할 분담은 다음과 같습니다.

- OrcaSlicer: CMYKW 비율 계산 및 채널 축 G-code 출력
- Klipper: `A/B/C/D/H`를 물리 필라멘트 모터에 매핑하고 이동 실행
- Mainsail: CMYKW 채널 등록 상태와 위치 표시

혼합 계산을 Mainsail로 옮기지 마세요. Klipper가 색상을 추론하게 만들지
마세요. OrcaSlicer가 프린터별 핀이나 배선에 의존하게 만들지 마세요.
