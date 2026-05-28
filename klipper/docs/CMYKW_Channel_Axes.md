# CMYKW channel axes

This fork uses Klipper's existing `manual_stepper GCODE_AXIS` support for a
single nozzle with five filament channel motors.

Reserved axis mapping:

```text
A=Cyan
B=Magenta
C=Yellow
D=Black
H=White
```

The filament tubes must match that order. Do not assign `A/B/C/D/H` to any
other `MANUAL_STEPPER ... GCODE_AXIS=` use in the same config.

OrcaSlicer keeps `E` as the logical total extrusion value and writes the actual
channel motor positions on the same move. The channel axes are absolute
positions and are initialized to zero at print start:

```text
G1 X100 Y100 E10 A2 B3 C4 D1 H0
```

Put the hardware registration in Klipper, not in OrcaSlicer. OrcaSlicer's
machine start G-code only needs to call the Klipper start macro:

```text
START_PRINT
```

Register the motors from Klipper's print-start macro:

```text
[gcode_macro START_PRINT]
gcode:
  REGISTER_CMYKW_AXES
  # Add the rest of your normal print-start sequence here.
```

`REGISTER_CMYKW_AXES` resets the channel positions and maps the steppers:

```text
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

OrcaSlicer may still emit `T0` through `T19` as filament slot markers. Keep
them as no-op macros in Klipper, for example:

```text
[gcode_macro T0]
gcode:
  G4 P0
```

Do this for every slot number OrcaSlicer can output. The `Tn` line is not the
motor command in this fork; `A/B/C/D/H` are the motor commands.

Keep `[extruder]` for the heater, sensor, and logical E checks. The physical
filament motors are configured as `[manual_stepper ...]` sections; see
`config/sample-cmykw-channel-axis.cfg`.

Disable slicer pressure advance output for this MVP. With no physical
`[extruder]` stepper, Klipper's normal `SET_PRESSURE_ADVANCE` command has no
extruder stepper to tune, and the channel axes do not implement pressure
advance compensation.

Disable arc fitting for this MVP. Klipper's `gcode_arcs.py` expands `G2/G3`
using only `X/Y/Z/E/F`, so it does not preserve the extra channel axes.
