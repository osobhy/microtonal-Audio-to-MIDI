import librosa
import numpy as np
import pretty_midi

# =========================
# SETTINGS (tweak here)
# =========================
AUDIO_PATH = "30.wav"
MIDI_OUTPUT = AUDIO_PATH + "_quantized.mid"

# Pitch bend range on your synth (in semitones). Must match your synth!
PITCH_BEND_RANGE = 2.0

# Quantization for "pitch class" intention (e.g., quarter-tones)
QUANTIZATION_STEP = 0.5  # semitones

# Split when a pitch slide exceeds this and persists (not vibrato)
SLIDE_SPLIT_SEMITONES = 0.5
SLIDE_HOLD_FRAMES = 3  # frames it must persist before splitting

# Tremolo: treat onset peaks as new notes if pitch stays near the base
TREM_PITCH_TOL = 0.2  # semitones allowable deviation for “same note” tremolo
TREM_MIN_GAP_S = 0.035  # minimum time between tremolo notes

# Amplitude gating & durations
GATE_ON = 0.08   # normalized RMS to start a note
GATE_OFF = 0.05  # normalized RMS to end a note (hysteresis)
RELEASE_FRAMES = 5
MIN_NOTE_DUR_S = 0.05
MIN_GAP_S = 0.02
COOLDOWN_FRAMES = 2  # ignore new onsets for a couple frames after starting

# Pitch smoothing & bend thinning
PITCH_MEDIAN_WIN = 5             # frames for median smooth on MIDI float pitch
BEND_SEMITONE_STEP = 0.03        # only emit bend if change >= this (≈3 cents)
BEND_MAX_FRAME_SKIP = 3          # also emit at least every N frames

# pYIN / STFT
FRAME_LENGTH = 2048
HOP_LENGTH = 256
FMIN = librosa.note_to_hz("C2")
FMAX = librosa.note_to_hz("C7")

# MIDI instrument (GM acoustic nylon guitar ≈ plucked). 0-based program numbers.
MIDI_PROGRAM = 24

# =========================
# HELPERS
# =========================
def hz_to_midi_float(hz):
    """Like pretty_midi.hz_to_note_number but safe for arrays."""
    return 69.0 + 12.0 * np.log2(hz / 440.0)

def nanmedian_smooth(x, win):
    """Simple NaN-aware median filter."""
    if win <= 1:
        return x.copy()
    n = len(x)
    half = win // 2
    y = np.copy(x)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        seg = x[lo:hi]
        seg = seg[~np.isnan(seg)]
        if seg.size > 0:
            y[i] = np.median(seg)
        # else leave NaN
    return y

def normalize_rms(rms):
    # Normalize by 95th percentile to reduce outlier effects
    ref = np.percentile(rms, 95)
    if ref <= 1e-12:
        ref = np.max(rms) + 1e-12
    out = np.clip(rms / ref, 0.0, 1.0)
    return out

def velocity_from_rms(rms_val):
    # Map [0..1] -> [28..112], curved a bit
    v = int(28 + (rms_val ** 0.6) * (112 - 28))
    return int(np.clip(v, 1, 127))

def emit_pitch_bend_events(instrument, times, midi_pitch_float, base_semitone_int,
                           idx_start, idx_end):
    """
    Emit pitch bend events between [idx_start, idx_end) relative to base_semitone_int.
    Thin events by BEND_SEMITONE_STEP and BEND_MAX_FRAME_SKIP.
    """
    last_pb = None
    last_idx = None

    # Initial bend at start (so microtonal offset is in place immediately)
    dev0 = midi_pitch_float[idx_start] - base_semitone_int
    pb0 = int(np.clip((dev0 / PITCH_BEND_RANGE) * 8192, -8192, 8191))
    instrument.pitch_bends.append(pretty_midi.PitchBend(pitch=pb0, time=float(times[idx_start])))
    last_pb = pb0
    last_idx = idx_start

    for j in range(idx_start + 1, idx_end):
        mp = midi_pitch_float[j]
        if np.isnan(mp):
            continue
        dev = mp - base_semitone_int
        pb = int(np.clip((dev / PITCH_BEND_RANGE) * 8192, -8192, 8191))
        # Thin events
        if (abs(pb - last_pb) >= int(BEND_SEMITONE_STEP / PITCH_BEND_RANGE * 8192)) or (j - last_idx >= BEND_MAX_FRAME_SKIP):
            instrument.pitch_bends.append(pretty_midi.PitchBend(pitch=pb, time=float(times[j])))
            last_pb = pb
            last_idx = j

def add_note(instrument, times, rms, midi_pitch_float, idx_start, idx_end):
    """Create a MIDI note + pitch bends for frames [idx_start, idx_end)."""
    if idx_end <= idx_start:
        return False

    start_t = float(times[idx_start])
    end_t = float(times[idx_end - 1]) if idx_end - 1 < len(times) else float(times[-1])
    # Ensure non-zero duration
    end_t = max(end_t, start_t + 1e-3)

    # Choose semitone base; keep microtonal offset via pitch bend
    base_pitch_ref = midi_pitch_float[idx_start]
    if np.isnan(base_pitch_ref):
        return False

    # Quantize the *reference* to your desired grid, then round to semitone for base MIDI note
    q_ref = round(base_pitch_ref / QUANTIZATION_STEP) * QUANTIZATION_STEP
    base_semitone_int = int(np.clip(np.round(q_ref), 0, 127))

    # Velocity from RMS at onset frame
    vel = velocity_from_rms(rms[idx_start])

    note = pretty_midi.Note(
        velocity=vel,
        pitch=base_semitone_int,
        start=start_t,
        end=end_t
    )
    instrument.notes.append(note)

    # Pitch bends relative to base semitone
    emit_pitch_bend_events(instrument, times, midi_pitch_float, base_semitone_int, idx_start, idx_end)
    return True

# =========================
# LOAD + FEATURES
# =========================
y, sr = librosa.load(AUDIO_PATH, sr=None, mono=True)

# pYIN pitch (float MIDI numbers)
f0_hz, voiced_flag, _ = librosa.pyin(
    y, fmin=FMIN, fmax=FMAX, sr=sr, frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH
)
times = librosa.times_like(f0_hz, sr=sr, hop_length=HOP_LENGTH)

# Convert to MIDI float, smooth, and handle NaNs
midi_pitch = np.full_like(f0_hz, np.nan, dtype=float)
valid = (~np.isnan(f0_hz)) & (voiced_flag.astype(bool))
midi_pitch[valid] = hz_to_midi_float(f0_hz[valid])

# Median smoothing on MIDI float to tame jitter (preserve slides)
midi_pitch_smooth = nanmedian_smooth(midi_pitch, PITCH_MEDIAN_WIN)

# RMS envelope & onset strength
rms = librosa.feature.rms(y=y, frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH).flatten()
rms_n = normalize_rms(rms)

onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP_LENGTH)
onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr,
                                          hop_length=HOP_LENGTH, backtrack=False,
                                          pre_max=3, post_max=3, pre_avg=3, post_avg=3,
                                          delta=0.1, wait=0)
onset_set = set(int(f) for f in onset_frames)

# =========================
# NOTE SEGMENTATION (state machine)
# =========================
midi = pretty_midi.PrettyMIDI()
instrument = pretty_midi.Instrument(program=MIDI_PROGRAM)

in_note = False
idx_start = None
base_ref_pitch = None
release_count = 0
slide_count = 0
cooldown = 0
last_note_end_time = -1e9

n_frames = len(midi_pitch_smooth)

def is_voiced(i):
    return valid[i] and not np.isnan(midi_pitch_smooth[i])

def time_at(i):
    return float(times[i])

for i in range(n_frames):
    # Cooling period after starting a note to avoid immediate duplicates
    if cooldown > 0:
        cooldown -= 1

    # Gate logic
    gate_on = (rms_n[i] >= GATE_ON)
    gate_off = (rms_n[i] < GATE_OFF)

    if not in_note:
        # Start condition: voiced, above gate, and respect min gap from last note
        if is_voiced(i) and gate_on and (time_at(i) - last_note_end_time >= MIN_GAP_S):
            in_note = True
            idx_start = i
            base_ref_pitch = midi_pitch_smooth[i]
            release_count = 0
            slide_count = 0
            cooldown = COOLDOWN_FRAMES
        else:
            continue
    else:
        # If unvoiced or below gate, count towards release
        if (not is_voiced(i)) or gate_off:
            release_count += 1
        else:
            release_count = 0

        # Tremolo handling: onset peak with pitch near base -> split
        is_onset = (i in onset_set) and (cooldown == 0)
        pitch_dev = np.nan if base_ref_pitch is None or np.isnan(midi_pitch_smooth[i]) else (midi_pitch_smooth[i] - base_ref_pitch)

        tremolo_split = False
        if is_onset and (pitch_dev is not np.nan):
            if abs(pitch_dev) <= TREM_PITCH_TOL and (time_at(i) - time_at(idx_start)) >= MIN_NOTE_DUR_S:
                tremolo_split = True

        # Slide split: sustained deviation >= threshold
        slide_split = False
        if (pitch_dev is not np.nan) and (abs(pitch_dev) >= SLIDE_SPLIT_SEMITONES) and is_voiced(i):
            slide_count += 1
            if slide_count >= SLIDE_HOLD_FRAMES:
                slide_split = True
        else:
            slide_count = 0

        # End conditions
        should_end_for_release = (release_count >= RELEASE_FRAMES)
        should_end_for_trem = tremolo_split
        should_end_for_slide = slide_split

        if should_end_for_release or should_end_for_trem or should_end_for_slide:
            idx_end = max(i - (RELEASE_FRAMES if should_end_for_release else 0), idx_start + 1)

            # Enforce minimum duration; if too short, either extend or drop
            if time_at(idx_end - 1) - time_at(idx_start) < MIN_NOTE_DUR_S:
                # If we're releasing, try to extend until i (don’t drop)
                idx_end = i
                if time_at(idx_end - 1) - time_at(idx_start) < MIN_NOTE_DUR_S:
                    # Still too short — drop it
                    in_note = False
                    last_note_end_time = time_at(idx_end - 1)
                    idx_start = None
                    base_ref_pitch = None
                    release_count = 0
                    cooldown = COOLDOWN_FRAMES
                    continue

            # Add the finished note
            added = add_note(instrument, times, rms_n, midi_pitch_smooth, idx_start, idx_end)
            if added:
                last_note_end_time = time_at(idx_end - 1)

            # Start new note immediately for tremolo/slide if conditions allow
            if (should_end_for_trem or should_end_for_slide) and is_voiced(i):
                in_note = True
                idx_start = i
                base_ref_pitch = midi_pitch_smooth[i]
                release_count = 0
                slide_count = 0
                cooldown = COOLDOWN_FRAMES
            else:
                in_note = False
                idx_start = None
                base_ref_pitch = None
                release_count = 0
                cooldown = COOLDOWN_FRAMES

# Flush last note if open
if in_note and idx_start is not None:
    add_note(instrument, times, rms_n, midi_pitch_smooth, idx_start, n_frames)

# =========================
# WRITE MIDI
# =========================
midi.instruments.append(instrument)
midi.write(MIDI_OUTPUT)
print(f"✅ Saved microtonal MIDI to {MIDI_OUTPUT}  |  notes={len(instrument.notes)}  bends={len(instrument.pitch_bends)}")
