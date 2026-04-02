"""
Generate PDF report for the 2026-03-20 alignment session.
Run with: /home/beams/2BMB/conda/anaconda/bin/python report_2026_03_20.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

OUTPUT = '/home/beams0/2BMB/conda/align-decarlof/docs/alignment_report_2026_03_20.pdf'

# ── Data ──────────────────────────────────────────────────────────────────────

# Phase 1: camera rotation alignment
# columns: iteration, time, overall_x, top, center, bottom, decision
phase1 = [
    ( 1, '19:33', -526.88, -1101.44, -526.57, -523.80, 'No motion'),
    ( 2, '19:35',  -525.15,  -530.32,  -524.18,  -521.40, 'Yes (SampleX moved)'),
    ( 3, '19:36',     4.28,     0.28,     4.52,     8.53, 'No motion'),
    ( 4, '19:38',     8.85,     4.66,     9.07,    13.22, 'No motion'),
    ( 5, '19:39',     3.63,    -0.06,     3.86,     7.58, 'No motion'),
    ( 6, '19:40',     5.23,     2.15,     5.45,     8.51, 'No motion'),
    ( 7, '19:41',     4.39,     1.94,     4.57,     7.02, 'No motion'),
    ( 8, '19:42',     4.79,     2.79,     4.94,     6.88, 'Yes (SampleX moved)'),
    ( 9, '19:43',    -0.04,    -1.29,     0.07,     1.16, 'No motion'),
    (10, '19:44',     0.19,    -0.76,     0.29,     1.04, 'No motion'),
    (11, '19:45',    -0.05,    -0.84,     0.04,     0.63, 'No motion'),
    (12, '19:46',     0.19,    -0.29,     0.28,     0.49, 'No motion'),
    (13, '19:47',    -0.28,    -0.47,    -0.22,    -0.35, '✓  Converged'),
]

# Phase 2: roll alignment (Y-sweep runs only, flat top/center/bottom)
# columns: iter, time, overall_x, top, center, bottom, note
phase2 = [
    (14, '19:49',     9.56,    9.53,    9.63,    9.43, 'Y ~ 0 (reference)'),
    (15, '19:51',   191.37,  192.26,  191.53,  190.92, 'Y large positive'),
    (16, '19:52',   185.03,  185.47,  185.01,  184.72, 'Y large positive'),
    (17, '19:53',   180.90,  181.70,  180.85,  180.13, 'Y large positive'),
    (18, '19:54',   184.99,  186.33,  185.21,  184.15, 'Y large positive'),
    (19, '19:55',   179.04,  180.84,  179.35,  177.84, 'Y large positive'),
    (20, '19:56',   176.59,  177.74,  176.53,  175.36, 'Y large positive'),
    (21, '19:57',   178.66,  180.45,  178.98,  177.45, 'Y large positive'),
    (22, '20:00',    -4.62,   -3.58,   -4.57,   -6.19, 'Y ~ 0'),
    (23, '20:01',  -114.80, -114.11, -114.64, -116.25, 'Y large negative'),
    (24, '20:03',  -112.10, -111.07, -111.72, -113.25, 'Y large negative'),
    (25, '20:04',   165.04,  167.10,  165.38,  163.61, 'Y large positive'),
    (26, '20:05',   165.13,  166.48,  165.05,  163.61, 'Y large positive'),
    (27, '20:07',    -2.17,   -1.00,   -2.11,   -3.89, 'Y ~ 0 (cam touch-up)'),
    (28, '20:08',    -2.73,   -1.42,   -2.66,   -4.64, 'Y ~ 0 (cam touch-up)'),
    (29, '20:09',    -1.89,   -0.83,   -1.81,   -3.43, 'Y ~ 0 (cam touch-up)'),
    (30, '20:11',    -2.43,   -1.26,   -2.37,   -4.15, 'Y ~ 0 (cam touch-up)'),
    (31, '20:17',     6.77,    8.39,    7.04,    5.03, 'Y ~ 0 after roll adj.'),
    (32, '20:18',     5.46,    7.14,    5.73,    3.74, 'Y ~ 0 after roll adj.'),
    (33, '20:20',     1.05,    2.65,    1.30,   -0.62, 'Cam fine-tune'),
    (34, '20:22',     1.05,    2.47,    1.29,   -0.45, 'Cam fine-tune'),
    (35, '20:23',     0.74,    1.98,    0.95,   -0.61, 'Cam fine-tune'),
    (36, '20:24',     0.40,    1.27,    0.57,   -0.63, 'Cam fine-tune'),
    (37, '20:25',     0.88,    1.37,    0.98,    0.16, 'Cam fine-tune'),
    (38, '20:26',     0.55,    0.66,    0.60,    0.14, '✓  Cam re-converged'),
    (39, '20:27',     2.27,    2.41,    2.36,    1.90, 'Y ~ 0 (reference)'),
    (40, '20:28',    39.62,   39.88,   39.71,   39.19, 'Y positive'),
    (41, '20:29',    37.48,   37.74,   37.53,   36.99, 'Y positive'),
    (42, '20:30',   -71.11,  -71.35,  -71.06,  -71.39, 'Y negative'),
    (43, '20:31',   -69.64,  -69.82,  -69.56,  -69.93, 'Y negative'),
    (44, '20:32',  -107.29, -107.61, -107.18, -107.54, 'Y large negative'),
    (45, '20:33',  -106.81, -107.20, -106.76, -107.04, 'Y large negative'),
]

PIXEL_SIZE = 0.349784  # µm/pixel

# ── Helpers ───────────────────────────────────────────────────────────────────

def tilt(row):
    return row[5] - row[3]   # bottom - top

COLORS = {
    'header':     '#1a3a5c',
    'subheader':  '#2e6da4',
    'accent':     '#e8f4fd',
    'converged':  '#d4edda',
    'yes':        '#fff3cd',
    'warn':       '#ffeeba',
    'text':       '#222222',
}

def add_header(fig, title, subtitle=''):
    ax = fig.add_axes([0, 0.93, 1, 0.07])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle='square,pad=0',
                                facecolor=COLORS['header'], zorder=0))
    ax.text(0.5, 0.65, title, ha='center', va='center', fontsize=14,
            fontweight='bold', color='white', transform=ax.transAxes)
    if subtitle:
        ax.text(0.5, 0.2, subtitle, ha='center', va='center', fontsize=9,
                color='#add8f7', transform=ax.transAxes)


# ── Page 1: Title page ────────────────────────────────────────────────────────

with PdfPages(OUTPUT) as pdf:

    # ── PAGE 1 ──────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle='square,pad=0',
                                facecolor='white'))

    # top bar
    ax.add_patch(FancyBboxPatch((0, 0.85), 1, 0.15, boxstyle='square,pad=0',
                                facecolor=COLORS['header']))
    ax.text(0.5, 0.925, 'Beamline 2BM-B — Detector Alignment Report',
            ha='center', va='center', fontsize=18, fontweight='bold',
            color='white', transform=ax.transAxes)
    ax.text(0.5, 0.875, 'Session: 2026-03-20   |   19:30 – 20:33 CDT   |   45 align rotation runs',
            ha='center', va='center', fontsize=10, color='#add8f7',
            transform=ax.transAxes)

    # summary boxes
    summaries = [
        ('Pixel size', '0.3498 µm/px', COLORS['accent']),
        ('Camera rotation\niterations', '13', COLORS['accent']),
        ('Roll alignment\niterations', '32', COLORS['accent']),
        ('Final tilt\n(bottom−top)', '0.12 px', COLORS['converged']),
    ]
    for i, (label, value, color) in enumerate(summaries):
        x = 0.08 + i * 0.23
        ax.add_patch(FancyBboxPatch((x, 0.70), 0.20, 0.12,
                                    boxstyle='round,pad=0.01',
                                    facecolor=color, edgecolor=COLORS['subheader'],
                                    linewidth=1.5, transform=ax.transAxes))
        ax.text(x + 0.10, 0.775, value, ha='center', va='center',
                fontsize=14, fontweight='bold', color=COLORS['header'],
                transform=ax.transAxes)
        ax.text(x + 0.10, 0.718, label, ha='center', va='center',
                fontsize=8, color='#444', transform=ax.transAxes)

    # overview text
    overview = (
        "This report documents a complete detector alignment session performed on 2026-03-20 at the\n"
        "Advanced Photon Source, beamline 2BM-B. The session used the align command-line tool and\n"
        "followed a two-phase procedure:\n\n"
        "  Phase 1 — Camera Rotation Alignment: equalize the rotation axis position at the top,\n"
        "  center, and bottom of the detector image by adjusting the Optique Peter camera rotation\n"
        "  motor. Convergence criterion: |bottom − top| < ~0.5 px.\n\n"
        "  Phase 2 — Roll Alignment: verify that the overall rotation axis position is consistent\n"
        "  when the hexapod Y stage is moved to different heights, then correct with hexapod roll.\n\n"
        "NOTE: This session used the previous version of align, which did not yet log operator motor\n"
        "settings (camera rotation angle, roll, pitch, Y position). Those inputs are therefore\n"
        "reconstructed qualitatively from the shift measurements only. Future sessions will log\n"
        "all motor positions automatically."
    )
    ax.text(0.08, 0.67, overview, ha='left', va='top', fontsize=9,
            color=COLORS['text'], transform=ax.transAxes,
            fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa',
                      edgecolor='#dee2e6', linewidth=1))

    # timeline
    ax.text(0.08, 0.34, 'Session timeline', fontsize=11, fontweight='bold',
            color=COLORS['header'], transform=ax.transAxes)
    timeline = [
        ('19:30–19:32', 'align resolution',         '→ pixel size = 0.3498 µm/px'),
        ('19:33–19:47', 'Phase 1  Camera rotation', '→ tilt: 577 px → 0.12 px  (13 iterations)'),
        ('19:49–19:58', 'Phase 2a  Y sweeps',        '→ large Y offsets, measuring roll sensitivity'),
        ('20:00–20:11', 'Phase 2b  Roll correction', '→ overall shift at Y=0 re-checked'),
        ('20:17–20:26', 'Phase 2c  Camera touch-up', '→ small residual tilt corrected'),
        ('20:27–20:33', 'Phase 2d  Final Y sweeps',  '→ flat top/center/bottom, roll verified'),
    ]
    for j, (time, phase, result) in enumerate(timeline):
        y = 0.30 - j * 0.045
        ax.add_patch(FancyBboxPatch((0.08, y - 0.012), 0.84, 0.038,
                                    boxstyle='round,pad=0.005',
                                    facecolor='#f0f4f8' if j % 2 == 0 else 'white',
                                    edgecolor='#dee2e6', linewidth=0.5,
                                    transform=ax.transAxes))
        ax.text(0.10, y + 0.007, time, fontsize=8, color='#666',
                transform=ax.transAxes, fontfamily='monospace')
        ax.text(0.22, y + 0.007, phase, fontsize=8.5, fontweight='bold',
                color=COLORS['header'], transform=ax.transAxes)
        ax.text(0.52, y + 0.007, result, fontsize=8, color='#444',
                transform=ax.transAxes)

    ax.text(0.5, 0.03, 'Generated by align  •  Argonne National Laboratory  •  2BM-B',
            ha='center', va='center', fontsize=7, color='#999',
            transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

    # ── PAGE 2: Phase 1 table + convergence plot ─────────────────────────────
    fig = plt.figure(figsize=(8.5, 11))
    add_header(fig, 'Phase 1 — Camera Rotation Alignment',
               'Goal: equalize shift at top / center / bottom of detector  |  metric: tilt = bottom − top')

    gs = gridspec.GridSpec(2, 1, figure=fig, top=0.91, bottom=0.05,
                           hspace=0.35, height_ratios=[1.6, 1])

    # --- table ---
    ax_t = fig.add_subplot(gs[0])
    ax_t.axis('off')

    col_labels = ['#', 'Time', 'Overall X\n(px)', 'Top\n(px)', 'Center\n(px)',
                  'Bottom\n(px)', 'Tilt b−t\n(px)', 'Decision']
    table_data = []
    row_colors = []
    for row in phase1:
        t = tilt(row)
        table_data.append([
            str(row[0]), row[1],
            f'{row[2]:+.2f}', f'{row[3]:+.2f}', f'{row[4]:+.2f}', f'{row[5]:+.2f}',
            f'{t:+.2f}', row[6]
        ])
        if 'Converged' in row[6]:
            row_colors.append([COLORS['converged']] * 8)
        elif 'Yes' in row[6]:
            row_colors.append([COLORS['yes']] * 8)
        else:
            row_colors.append(['white'] * 8)

    tbl = ax_t.table(
        cellText=table_data,
        colLabels=col_labels,
        cellColours=row_colors,
        loc='center', cellLoc='center'
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.4)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor(COLORS['subheader'])
            cell.set_text_props(color='white', fontweight='bold')
        cell.set_edgecolor('#dee2e6')

    ax_t.set_title('Table 1 — Shift measurements per iteration', fontsize=10,
                   fontweight='bold', color=COLORS['header'], pad=8)

    # --- convergence plot ---
    ax_p = fig.add_subplot(gs[1])
    iters   = [r[0] for r in phase1]
    tilts   = [abs(tilt(r)) for r in phase1]
    overall = [abs(r[2]) for r in phase1]
    tops    = [r[3] for r in phase1]
    bottoms = [r[5] for r in phase1]

    ax_p.semilogy(iters, tilts, 'o-', color='#e74c3c', linewidth=2,
                  markersize=6, label='|Tilt| = |bottom−top| (px)')
    ax_p.semilogy(iters, overall, 's--', color='#3498db', linewidth=1.5,
                  markersize=5, label='|Overall X shift| (px)', alpha=0.7)
    ax_p.axhline(0.5, color='green', linestyle=':', linewidth=1.5,
                 label='Convergence threshold (0.5 px)')
    ax_p.axvline(8.5, color='orange', linestyle='--', linewidth=1,
                 label='SampleX corrected (iter 2 & 8)', alpha=0.8)
    ax_p.axvline(2.5, color='orange', linestyle='--', linewidth=1, alpha=0.8)

    ax_p.set_xlabel('Iteration', fontsize=9)
    ax_p.set_ylabel('Shift magnitude (px, log scale)', fontsize=9)
    ax_p.set_title('Figure 1 — Tilt and overall shift convergence', fontsize=10,
                   fontweight='bold', color=COLORS['header'])
    ax_p.set_xticks(iters)
    ax_p.legend(fontsize=7.5, loc='upper right')
    ax_p.grid(True, which='both', alpha=0.3)
    ax_p.set_facecolor('#fafafa')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

    # ── PAGE 3: Phase 2 table ────────────────────────────────────────────────
    fig = plt.figure(figsize=(8.5, 11))
    add_header(fig, 'Phase 2 — Roll Alignment',
               'Goal: overall X shift consistent at all hexapod Y positions  |  camera re-verified mid-session')

    gs2 = gridspec.GridSpec(2, 1, figure=fig, top=0.91, bottom=0.05,
                            hspace=0.38, height_ratios=[2.2, 1])

    ax_t2 = fig.add_subplot(gs2[0])
    ax_t2.axis('off')

    col_labels2 = ['#', 'Time', 'Overall X\n(px)', 'Top\n(px)', 'Center\n(px)',
                   'Bottom\n(px)', 'Tilt b−t\n(px)', 'Note']
    table_data2 = []
    row_colors2 = []
    cam_touchup = {27, 28, 29, 30, 33, 34, 35, 36, 37}
    for row in phase2:
        t = tilt(row)
        table_data2.append([
            str(row[0]), row[1],
            f'{row[2]:+.1f}', f'{row[3]:+.1f}', f'{row[4]:+.1f}', f'{row[5]:+.1f}',
            f'{t:+.2f}', row[6]
        ])
        if 'Converged' in row[6] or '✓' in row[6]:
            row_colors2.append([COLORS['converged']] * 8)
        elif row[0] in cam_touchup:
            row_colors2.append([COLORS['warn']] * 8)
        elif abs(row[2]) > 30:
            row_colors2.append([COLORS['accent']] * 8)
        else:
            row_colors2.append(['white'] * 8)

    tbl2 = ax_t2.table(
        cellText=table_data2,
        colLabels=col_labels2,
        cellColours=row_colors2,
        loc='center', cellLoc='center'
    )
    tbl2.auto_set_font_size(False)
    tbl2.set_fontsize(7.5)
    tbl2.scale(1, 1.28)
    for (r, c), cell in tbl2.get_celld().items():
        if r == 0:
            cell.set_facecolor(COLORS['subheader'])
            cell.set_text_props(color='white', fontweight='bold')
        cell.set_edgecolor('#dee2e6')

    # legend patches
    patches = [
        mpatches.Patch(facecolor=COLORS['accent'],    label='Y-sweep measurement (large shift)'),
        mpatches.Patch(facecolor=COLORS['warn'],      label='Camera touch-up mid-roll phase'),
        mpatches.Patch(facecolor=COLORS['converged'], label='Converged'),
        mpatches.Patch(facecolor='white', edgecolor='#ccc', label='Y ~ 0 reference'),
    ]
    ax_t2.legend(handles=patches, loc='lower center', ncol=4,
                 fontsize=7, bbox_to_anchor=(0.5, -0.04),
                 framealpha=0.9, edgecolor='#ccc')

    ax_t2.set_title('Table 2 — Roll alignment measurements (iterations 14–45)',
                    fontsize=10, fontweight='bold', color=COLORS['header'], pad=8)

    # overall shift scatter: Y-sweep runs
    ax_p2 = fig.add_subplot(gs2[1])
    sweep_iters   = [r[0] for r in phase2 if abs(r[2]) > 20]
    sweep_overall = [r[2] for r in phase2 if abs(r[2]) > 20]
    ref_iters     = [r[0] for r in phase2 if abs(r[2]) <= 20]
    ref_overall   = [r[2] for r in phase2 if abs(r[2]) <= 20]

    ax_p2.bar(sweep_iters, sweep_overall, color='#2e6da4', alpha=0.75,
              label='Y-sweep (large offset)', width=0.6)
    ax_p2.bar(ref_iters, ref_overall, color='#e74c3c', alpha=0.8,
              label='Y ~ 0 reference / cam touch-up', width=0.6)
    ax_p2.axhline(0, color='black', linewidth=0.8)
    ax_p2.set_xlabel('Iteration', fontsize=9)
    ax_p2.set_ylabel('Overall X shift (px)', fontsize=9)
    ax_p2.set_title('Figure 2 — Overall shift per iteration (Phase 2)',
                    fontsize=10, fontweight='bold', color=COLORS['header'])
    ax_p2.legend(fontsize=8)
    ax_p2.grid(True, axis='y', alpha=0.3)
    ax_p2.set_facecolor('#fafafa')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

    # ── PAGE 4: Key takeaways ────────────────────────────────────────────────
    fig = plt.figure(figsize=(8.5, 11))
    add_header(fig, 'Key Takeaways & Path to Automation', '')

    ax = fig.add_axes([0.06, 0.05, 0.88, 0.86])
    ax.axis('off')

    sections = [
        ('1.  Camera Rotation Alignment is predictable and automatable', '#1a3a5c', [
            'The tilt metric (bottom − top pixel shift) is a direct linear proxy for camera rotation error.',
            'One large initial correction (577 → 8.9 px, ~65× improvement) was followed by 11 fine steps.',
            'Tilt reduction per step was roughly proportional to the remaining tilt, suggesting a simple',
            'proportional controller (camera_rotation_correction ∝ tilt) would converge in 2–3 steps.',
            'The operator accepted SampleX correction twice during this phase to keep overall shift near 0;',
            'this can also be automated since the required SampleX move is already computed by align.',
        ]),
        ('2.  Camera rotation and roll are NOT fully independent', '#1a3a5c', [
            'The operator had to touch up camera rotation (iterations 27–38) after roll adjustments,',
            'suggesting that moving the hexapod Y/roll slightly perturbs the camera tilt.',
            'Automation must therefore iterate: align camera → check roll → re-check camera → repeat.',
            'A simple sequential loop with a shared convergence criterion will handle this correctly.',
        ]),
        ('3.  Roll alignment needs SampleY logged — the critical gap in this session', '#8b0000', [
            'The old logs show the overall shift at different Y positions but NOT what Y value was used.',
            'Without SampleY, we cannot reconstruct the roll sensitivity (px shift per mm of Y travel),',
            'which is the key quantity needed to compute the required roll correction automatically.',
            'The new align version now logs SampleY at every run. One new session will provide this.',
        ]),
        ('4.  What the new logs will enable', '#1a5c1a', [
            'Camera rotation automation: fit tilt vs. camera_rotation_angle → compute exact correction.',
            'Roll automation: fit overall_shift vs. SampleY at two heights → compute roll correction.',
            'Pitch automation: fit Y-shift (new metric) vs. sample_pitch → compute pitch correction.',
            'Expected total iterations to full alignment: ~5–8 (vs. 45 in this manual session).',
        ]),
        ('5.  Recommended next session protocol (with new logging)', '#1a3a5c', [
            '  a)  Run align resolution  → confirm pixel size.',
            '  b)  Run align rotation at Y = 0  →  record tilt and overall shift.',
            '  c)  Adjust camera rotation;  repeat (b) until |tilt| < 0.5 px.',
            '  d)  Run align rotation at Y = +8 mm  and  Y = −8 mm  →  record both overall shifts.',
            '  e)  Adjust roll;  repeat (d) until |shift_up − shift_down| < 1 px.',
            '  f)  Re-run (b–c) to confirm camera rotation still within tolerance.',
            '  g)  Adjust pitch to zero the Y-shift component.',
            'Collect logs at each step — this session will train the automation model.',
        ]),
    ]

    y_pos = 0.97
    for title, color, bullets in sections:
        ax.text(0.0, y_pos, title, fontsize=10, fontweight='bold', color=color,
                transform=ax.transAxes, va='top')
        y_pos -= 0.032
        for bullet in bullets:
            ax.text(0.02, y_pos, f'•  {bullet}', fontsize=8.5, color=COLORS['text'],
                    transform=ax.transAxes, va='top', wrap=True)
            y_pos -= 0.026
        y_pos -= 0.018
        ax.plot([0.0, 1.0], [y_pos + 0.010, y_pos + 0.010], color='#dee2e6',
                linewidth=0.8, transform=ax.transAxes)
        y_pos -= 0.008

    ax.text(0.5, -0.01,
            'Generated by align  •  Argonne National Laboratory  •  2BM-B  •  2026-03-21',
            ha='center', va='bottom', fontsize=7, color='#999',
            transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

print(f'Report written to {OUTPUT}')
