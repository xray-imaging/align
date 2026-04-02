# #########################################################################
# Copyright (c) 2020, UChicago Argonne, LLC. All rights reserved.         #
# #########################################################################

"""
Automated 4-step alignment sequence for 2BM-B.

Step 0: Prerequisite check — pixel size must be finite (run align resolution first).
Step 1: Camera rotation convergence at Y = 0.
Step 2: Roll correction at ±Y_ref (operator confirms range and FOV).
Step 3: Pitch correction at Y_ref (done last — most sensitive axis).
Step 4: Sample X centering.
"""

import time
import numpy as np

from align import log
from align import detector
from align import pv
from align import sample
from align import config
from align import util


def align_auto(params):

    global_PVs = pv.init_general_PVs(params)
    try:
        detector_sn = global_PVs['Cam1SerialNumber'].get()
        if detector_sn is None or detector_sn == 'Unknown':
            log.error('*** The detector with EPICS IOC prefix %s is down' % params.detector_prefix)
            return
        log.info('*** Detector %s on' % detector_sn)
        detector.init(global_PVs, params)
        detector.set(global_PVs, params)
        dark_field, white_field = detector.take_dark_and_white(global_PVs, params)
    except KeyError:
        log.error('  *** Some PV assignment failed!')
        return

    # ── Step 0: Prerequisite check ───────────────────────────────────────────
    if params.image_pixel_size is None or not np.isfinite(params.image_pixel_size):
        log.error('  [auto] Pixel size not set or infinite. Run "align resolution" first.')
        return
    pixel_size = params.image_pixel_size
    log.warning('  [auto] pixel size: %.4f um/px' % pixel_size)

    # ── Calibration: camera rotation sensitivity (at Y = 0) ─────────────────
    log.warning('  [auto] calibrating camera rotation sensitivity ...')
    r0 = sample._measure_rotation(params, global_PVs, dark_field, white_field)
    tilt0 = r0.shift_bottom - r0.shift_top

    pv.move_camera_rotation(global_PVs, params, params.calibration_delta_cam)
    r1 = sample._measure_rotation(params, global_PVs, dark_field, white_field)
    tilt1 = r1.shift_bottom - r1.shift_top
    pv.move_camera_rotation(global_PVs, params, -params.calibration_delta_cam)  # restore

    if abs(params.calibration_delta_cam) < 1e-6 or abs(tilt1 - tilt0) < 0.1:
        log.error('  [auto] camera rotation calibration failed (delta tilt too small). Check delta-cam setting.')
        return
    K_cam = (tilt1 - tilt0) / params.calibration_delta_cam
    log.warning('  [auto] K_cam = %.1f px/deg' % K_cam)

    # ── Operator confirms Y_ref ───────────────────────────────────────────────
    y_ref = _confirm_y_ref(params)

    # ── Calibration: roll and pitch sensitivity (at Y_ref) ───────────────────
    log.warning('  [auto] calibrating roll and pitch sensitivity at Y = %.1f mm ...' % y_ref)
    pv.move_sample_y(global_PVs, y_ref)

    r_base = sample._measure_rotation(params, global_PVs, dark_field, white_field)

    pv.move_sample_roll(global_PVs, params.calibration_delta_roll)
    r_roll = sample._measure_rotation(params, global_PVs, dark_field, white_field)
    pv.move_sample_roll(global_PVs, -params.calibration_delta_roll)  # restore

    pv.move_sample_pitch(global_PVs, params.calibration_delta_pitch)
    r_pitch = sample._measure_rotation(params, global_PVs, dark_field, white_field)
    pv.move_sample_pitch(global_PVs, -params.calibration_delta_pitch)  # restore

    pv.move_sample_y(global_PVs, 0)

    if abs(params.calibration_delta_roll) < 1e-6 or abs(r_roll.shift_x - r_base.shift_x) < 0.1:
        log.error('  [auto] roll calibration failed (delta shift_x too small). Check delta-roll setting or increase Y_ref.')
        return
    K_roll = (r_roll.shift_x - r_base.shift_x) / params.calibration_delta_roll

    if abs(params.calibration_delta_pitch) < 1e-6 or abs(r_pitch.shift_y - r_base.shift_y) < 0.1:
        log.error('  [auto] pitch calibration failed (delta shift_y too small). Check delta-pitch setting.')
        return
    K_pitch = (r_pitch.shift_y - r_base.shift_y) / params.calibration_delta_pitch

    log.warning('  [auto] K_roll  = %.1f px/deg at Y = %.1f mm' % (K_roll, y_ref))
    log.warning('  [auto] K_pitch = %.1f px/deg at Y = %.1f mm' % (K_pitch, y_ref))

    # ── Step 1: Camera rotation (at Y = 0) ───────────────────────────────────
    log.warning('  [auto] === Step 1: Camera rotation convergence ===')
    converged = False
    for i in range(params.max_iterations):
        r = sample._measure_rotation(params, global_PVs, dark_field, white_field)
        tilt = r.shift_bottom - r.shift_top
        log.warning('  [auto] step 1 iter %d: tilt = %+.2f px' % (i + 1, tilt))
        if abs(tilt) < params.tilt_threshold:
            log.warning('  [auto] step 1 converged (tilt = %+.2f px < %.1f px)' % (tilt, params.tilt_threshold))
            converged = True
            break
        pv.move_camera_rotation(global_PVs, params, -tilt / K_cam)
    if not converged:
        log.error('  [auto] step 1 did not converge in %d iterations — aborting' % params.max_iterations)
        return

    # ── Step 2: Roll (at ±Y_ref) ─────────────────────────────────────────────
    log.warning('  [auto] === Step 2: Roll convergence at Y = ±%.1f mm ===' % y_ref)
    converged = False
    for i in range(params.max_iterations):
        pv.move_sample_y(global_PVs, +y_ref)
        r_plus = sample._measure_rotation(params, global_PVs, dark_field, white_field)

        pv.move_sample_y(global_PVs, -y_ref)
        r_minus = sample._measure_rotation(params, global_PVs, dark_field, white_field)

        pv.move_sample_y(global_PVs, 0)

        roll_error = (r_plus.shift_x - r_minus.shift_x) / 2
        log.warning('  [auto] step 2 iter %d: roll_error = %+.2f px' % (i + 1, roll_error))
        if abs(roll_error) < params.shift_threshold:
            log.warning('  [auto] step 2 converged (roll_error = %+.2f px < %.1f px)' % (roll_error, params.shift_threshold))
            converged = True
            break
        pv.move_sample_roll(global_PVs, -roll_error / K_roll)
    if not converged:
        log.error('  [auto] step 2 did not converge in %d iterations — aborting' % params.max_iterations)
        return

    # Re-check camera rotation: roll adjustments can perturb tilt
    log.warning('  [auto] re-checking camera rotation after roll adjustment ...')
    r = sample._measure_rotation(params, global_PVs, dark_field, white_field)
    tilt = r.shift_bottom - r.shift_top
    if abs(tilt) > params.tilt_threshold:
        log.warning('  [auto] camera rotation drifted (tilt = %+.2f px) — re-running step 1' % tilt)
        for i in range(params.max_iterations):
            r = sample._measure_rotation(params, global_PVs, dark_field, white_field)
            tilt = r.shift_bottom - r.shift_top
            log.warning('  [auto] step 1 re-run iter %d: tilt = %+.2f px' % (i + 1, tilt))
            if abs(tilt) < params.tilt_threshold:
                log.warning('  [auto] camera rotation re-converged')
                break
            pv.move_camera_rotation(global_PVs, params, -tilt / K_cam)
        else:
            log.error('  [auto] camera rotation re-run did not converge — aborting')
            return

    # ── Step 3: Pitch (at Y_ref) ─────────────────────────────────────────────
    log.warning('  [auto] === Step 3: Pitch convergence at Y = %.1f mm ===' % y_ref)
    converged = False
    for i in range(params.max_iterations):
        pv.move_sample_y(global_PVs, y_ref)
        r = sample._measure_rotation(params, global_PVs, dark_field, white_field)
        pv.move_sample_y(global_PVs, 0)

        shift_y = r.shift_y
        log.warning('  [auto] step 3 iter %d: shift_y = %+.2f px' % (i + 1, shift_y))
        if abs(shift_y) < params.pitch_threshold:
            log.warning('  [auto] step 3 converged (shift_y = %+.2f px < %.1f px)' % (shift_y, params.pitch_threshold))
            converged = True
            break
        pv.move_sample_pitch(global_PVs, -shift_y / K_pitch)
    if not converged:
        log.error('  [auto] step 3 did not converge in %d iterations — aborting' % params.max_iterations)
        return

    # ── Step 4: Sample X centering ───────────────────────────────────────────
    log.warning('  [auto] === Step 4: Sample X centering ===')
    r = sample._measure_rotation(params, global_PVs, dark_field, white_field)
    delta_x_mm = -r.shift_center * pixel_size / 1000.0
    log.warning('  [auto] step 4: centering sample X by %+.4f mm (%+.1f px)' % (delta_x_mm, -r.shift_center))
    global_PVs['SampleX'].put(global_PVs['SampleX'].get() + delta_x_mm, wait=True, timeout=600.0)
    global_PVs['SampleXSet'].put(1, wait=True)
    time.sleep(.2)
    global_PVs['SampleX'].put(0, wait=True)
    time.sleep(.2)
    global_PVs['SampleXSet'].put(0, wait=True)

    config.save_sample_params(params)
    log.warning('  [auto] === Alignment complete ===')


def _confirm_y_ref(params):
    """Prompt operator to confirm Y_ref and that sample is in FOV at both positions."""
    log.warning('  [auto] Roll/pitch steps require moving sample Y to +/-Y_ref.')
    log.warning('  [auto] Default Y_ref = %.1f mm. Hexapod nominal range: +/-10 mm (may be less).' % params.y_ref)
    log.warning('  [auto] Larger Y_ref = higher sensitivity. Must stay within sample FOV.')
    answer = input('  Enter Y_ref in mm [Enter = %.1f]: ' % params.y_ref).strip()
    y_ref = float(answer) if answer else params.y_ref
    log.info('  [auto] Y_ref set to %.1f mm' % y_ref)
    if not util.yes_or_no('  Confirm: sample is in FOV at both Y = +%.1f mm and Y = -%.1f mm?' % (y_ref, y_ref)):
        log.error('  [auto] Operator did not confirm FOV. Aborting.')
        raise RuntimeError('Operator aborted auto alignment at Y_ref confirmation.')
    return y_ref
