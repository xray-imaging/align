# Alignment Automation Model — 2BM-B

*Last updated: 2026-04-02*

---

## Overview

The `align auto` command implements a fully automated 4-step alignment sequence that replaces
the manual iteration loop previously required after each `align rotation` run (45 iterations
in the 2026-03-20 session). The automation is based on geometry and experimental observations
from the 2026-03-20 and 2026-04-01 sessions.

**Implementation status:** complete — see `src/align/auto.py`.

---

## Prerequisite chain

Before running any rotation alignment, two prerequisite steps must be completed in order:

```
1. DMagic step
   Sets the correct sample IN and OUT positions for the current sample/lens geometry.
   ↓
2. align resolution
   Acquires flat field with sample fully OUT of beam → clean normalization → valid pixel size.
   Automation must verify pixel_size is finite before proceeding.
   If pixel_size == inf: abort and alert operator (sample did not clear beam for flat field).
   ↓
3. align rotation  (repeated per step below)
```

**Why this matters:** If the sample does not fully clear the beam during flat-field acquisition,
the normalized image is corrupted.  Phase cross-correlation returns shift = (0, 0), giving
pixel_size = ∞.  The same corrupted normalization would propagate to `align rotation`.
This was observed twice during the 2026-04-01 session (runs at 15:40 and 15:45).

---

## The three-axis alignment procedure

### Physical description of each axis

| Motor | PV | What it corrects |
|---|---|---|
| Camera rotation | `2bmb:m7` (cam 1) or `2bmb:m8` (cam 2) | Tilt of the rotation axis image in the detector plane.  Visible as `shift_top ≠ shift_bottom`. |
| Hexapod roll | `2bmHXP:m4` | Tilt of the rotation axis out of the detector plane, in the horizontal direction.  Only measurable when sample Y ≠ 0 (roll is under the rotary stage). |
| Hexapod pitch | `2bmHXP:m5` | Tilt of the rotation axis along the beam (Z direction).  Visible as non-zero Y-shift component of the cross-correlation.  Most sensitive axis. |

### Correct order of operations

```
Step 1 — Camera rotation  (at Y = 0)
Step 2 — Roll             (at Y_ref, operator-confirmed)
Step 3 — Pitch            (at Y_ref, done last — most sensitive)
Step 4 — Sample X center  (final centering)
```

---

## Step-by-step automation model

### Step 1 — Camera rotation alignment

**Goal:** `|shift_top − shift_bottom| < threshold` (suggested: 0.5 px)

**Where:** Sample Y = 0 (hexapod home).

**How:**
```
measure: tilt = shift_bottom − shift_top  [px]
correction: Δ_cam = −tilt / K_cam
apply: move camera_rotation_motor by Δ_cam
repeat until |tilt| < 0.5 px
```

**Sensitivity K_cam:** To be determined from a calibration run (apply known camera rotation
delta, measure resulting tilt change).  From the 2026-03-20 session, ~13 manual iterations
were needed to reduce tilt from 577 px to 0.12 px — a proportional controller would converge
in ~3 steps once K_cam is known.

**Note:** Camera rotation must be re-verified after roll adjustment (the 2026-03-20 session
showed that roll changes slightly perturb camera tilt).

---

### Step 2 — Roll alignment

**Goal:** Shift X at +Y_ref ≈ Shift X at −Y_ref (rotation axis does not walk with Y).

**Where:** Sample Y = +Y_ref and −Y_ref (symmetric sweep).

**Y_ref selection:**
- Suggested starting value: **±5 mm**
- Actual usable range: limited by hexapod kinematics (depends on current X, pitch, roll, theta)
  — nominal ±10 mm but practically smaller
- Larger |Y_ref| → higher sensitivity → more precise correction
- **Operator must confirm Y_ref before each sweep** (safety gate for the hexapod excursion)
- Y_ref should span the sample's imaging range (match the science requirement)
- Also depends on sample size and lens (a large sample at 10x may need a smaller sweep than a small sample at 4x)

**How:**
```
move sample Y to +Y_ref
measure: shift_plus = shift_x  [px]

move sample Y to −Y_ref
measure: shift_minus = shift_x  [px]

roll_error = (shift_plus − shift_minus) / 2
correction: Δ_roll = −roll_error / K_roll(Y_ref)
apply: move hexapod roll by Δ_roll
return sample Y to 0

repeat until |shift_plus − shift_minus| < threshold (suggested: 2 px)
```

**Sensitivity K_roll(Y_ref):** From the 2026-04-01 session at Y = −4 mm:
- Roll change of 0.040° → X-shift change of ~3.94 px → K_roll ≈ 99 px/deg at Y = −4 mm
- At Y = 0: K_roll ≈ 0 (roll has no leverage at Y = 0 — do not try to correct roll at Y = 0)
- K_roll scales approximately linearly with |Y_ref|

**After roll adjustment:** Re-run Step 1 (camera rotation) to verify tilt has not drifted.

---

### Step 3 — Pitch alignment

**Goal:** Y-component of the cross-correlation shift ≈ 0 at Y_ref.

**Where:** Sample Y = Y_ref (same position used for roll, or operator-specified).

**How:**
```
move sample Y to Y_ref
measure: shift_y = Y-component of cross-correlation shift  [px]

correction: Δ_pitch = −shift_y / K_pitch(Y_ref)
apply: move hexapod pitch (2bmHXP:m5) by Δ_pitch
return sample Y to 0

repeat until |shift_y| < threshold (suggested: 1 px)
```

**Sensitivity K_pitch(Y_ref):** From the 2026-04-01 session at Y = −4 mm:
- Pitch change of +0.100° → X-shift change of ~714 px → K_pitch ≈ 7,140 px/deg at Y = −4 mm
- **Pitch is the most sensitive axis by far** — even 0.01° error = ~71 px at Y = −4 mm
- This is why pitch is corrected last: camera rotation and roll must be converged first to
  avoid compounding errors

**Note:** The pitch correction uses the Y-component of the cross-correlation (logged as
"shift_y" / "(pitch)" in the new log format).  This was added to the logger in March 2026.

---

### Step 4 — Sample X centering

**Goal:** Rotation axis centered on the detector.

**Where:** Sample Y = 0.

**How:**
```
measure: shift_center  [px]  (from the most recent align rotation at Y = 0)
correction: Δ_x = −shift_center × pixel_size  [mm]
apply: move 2bmHXP:m1 (sample X) by Δ_x
```

This step is a direct single-shot correction — no iteration needed.

---

## Full automation loop (implemented in `src/align/auto.py`)

```python
# Prerequisites
assert dmagic_step_completed()
pixel_size = run_align_resolution()
assert pixel_size != inf, "Sample did not clear beam for flat field — abort"

# Step 1: Camera rotation
while True:
    top, center, bottom = run_align_rotation(sample_y=0)
    tilt = bottom - top
    if abs(tilt) < 0.5:  # px
        break
    delta_cam = -tilt / K_cam
    move(camera_rotation_motor, delta_cam)

# Step 2: Roll
Y_ref = operator_confirm(suggest=5.0)  # mm — operator gates this motion
while True:
    _, _, _ = run_align_rotation(sample_y=+Y_ref)
    shift_plus = shift_x
    _, _, _ = run_align_rotation(sample_y=-Y_ref)
    shift_minus = shift_x
    roll_error = (shift_plus - shift_minus) / 2
    if abs(roll_error) < 2:  # px
        break
    delta_roll = -roll_error / K_roll(Y_ref)
    move(hexapod_roll, delta_roll)

move(sample_y, 0)

# Re-check camera rotation after roll
# (repeat Step 1 if tilt has drifted)

# Step 3: Pitch
while True:
    _, _, _ = run_align_rotation(sample_y=Y_ref)
    if abs(shift_y) < 1:  # px
        break
    delta_pitch = -shift_y / K_pitch(Y_ref)
    move(hexapod_pitch, delta_pitch)

move(sample_y, 0)

# Step 4: Sample X center
_, center, _ = run_align_rotation(sample_y=0)
move(sample_x, -center * pixel_size)
```

---

## Sensitivity summary (from 2026-04-01 session, Y_ref = 4 mm)

| Axis | Motor | Sensitivity at Y = 0 | Sensitivity at Y = −4 mm |
|---|---|---|---|
| Camera rotation | `2bmb:m8` | ~? px/deg (calibration needed) | — |
| Roll | `2bmHXP:m4` | ~0 px/deg (no leverage) | ~99 px/deg |
| Pitch | `2bmHXP:m5` | smaller (geometry-dep.) | ~7,140 px/deg |

Sensitivities scale approximately linearly with |Y_ref|.  A dedicated calibration run
(apply known Δ_motor, measure resulting shift change) will sharpen these estimates.

---

## What is still needed

1. **First live run:** Run `align auto` on a real sample to validate convergence and tune
   thresholds (`--tilt-threshold`, `--shift-threshold`, `--pitch-threshold`).
2. **K_roll and K_pitch at multiple Y_ref values:** Confirm linear scaling assumption from
   the 2026-04-01 sensitivity data (currently two data points each).
3. **Hexapod range check:** Before moving to Y_ref, ideally query the hexapod's current
   position limits (depend on X, roll, pitch, theta) and warn if Y_ref exceeds safe range.
   Currently handled by operator confirmation at the `_confirm_y_ref()` prompt.

---

## Sessions log

| Date | Type | Runs | Notes |
|---|---|---|---|
| 2026-03-20 | Full alignment (manual) | 13 cam + 32 roll = 45 total | Old logger (no motor positions recorded) |
| 2026-04-01 | Sensitivity mapping (no corrections) | 9 runs | New logger; system already aligned from 3/20; sensitivity data used to set default K values |
| — | First `align auto` run (planned) | ~5–10 expected | Will validate K values and convergence thresholds |

## CLI reference

```
align auto [options]

Key options:
  --y-ref FLOAT                 Hexapod Y excursion for roll/pitch (mm) [default: 5.0]
  --tilt-threshold FLOAT        Camera rotation convergence (px)         [default: 0.5]
  --shift-threshold FLOAT       Roll convergence (px)                    [default: 2.0]
  --pitch-threshold FLOAT       Pitch convergence (px)                   [default: 1.0]
  --max-iterations INT          Max iterations per step                  [default: 10]
  --calibration-delta-cam FLOAT Camera rotation test delta (deg)         [default: 0.05]
  --calibration-delta-roll FLOAT Roll test delta (deg)                   [default: 0.02]
  --calibration-delta-pitch FLOAT Pitch test delta (deg)                 [default: 0.01]
```
