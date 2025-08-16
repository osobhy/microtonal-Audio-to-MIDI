import librosa
import numpy as np
import pretty_midi
import sys

# settings

PITCH_BEND_RANGE = 2.0
QUANTIZATION_STEP = 0.5  
SLIDE_SPLIT_SEMITONES = 0.3
SLIDE_HOLD_FRAMES = 3 
TREM_PITCH_TOL = 0.3 
TREM_MIN_GAP_S = 0.035  # minimum time between tremolo notes
GATE_ON = 0.05  
GATE_OFF = 0.035 
RELEASE_FRAMES = 5
MIN_NOTE_DUR_S = 0.03
MIN_GAP_S = 0.01
COOLDOWN_FRAMES = 1
PITCH_MEDIAN_WIN = 3            
BEND_SEMITONE_STEP = 0.03       
BEND_MAX_FRAME_SKIP = 3       
FRAME_LENGTH = 1024
PYIN_CENTER = False
LOAD_DTYPE = np.float32
HOP_LENGTH = 256
FMIN = librosa.note_to_hz("C2")
FMAX = librosa.note_to_hz("C7")
MIDI_PROGRAM = 24

# helpers
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
    return y

def normalize_rms(rms):
    ref = np.percentile(rms, 95)
    if ref <= 1e-12:
        ref = np.max(rms) + 1e-12
    out = np.clip(rms / ref, 0.0, 1.0)
    return out

def velocity_from_rms(rms_val):
    v = int(28 + (rms_val ** 0.6) * (112 - 28))
    return int(np.clip(v, 1, 127))

def energy_onsets_from_rms(rms_n, min_prominence=0.02, min_distance_frames=2):
    try:
        from scipy.signal import find_peaks
        d = np.maximum(0.0, np.diff(rms_n, prepend=rms_n[0]))
        peaks, _ = find_peaks(d, prominence=min_prominence, distance=min_distance_frames)
        return peaks.astype(int)
    except Exception:
        thr = np.percentile(rms_n, 75) 
        rising = (rms_n[1:] >= thr) & (rms_n[:-1] < thr)
        return np.nonzero(np.concatenate([[False], rising]))[0]

def emit_pitch_bend_events(instrument, times, midi_pitch_float, base_semitone_int,
                           idx_start, idx_end):
    """
    Emit pitch bend events between [idx_start, idx_end) relative to base_semitone_int.
    Thin events by BEND_SEMITONE_STEP and BEND_MAX_FRAME_SKIP.
    """
    last_pb = None
    last_idx = None

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
    end_t = max(end_t, start_t + 1e-3)

    base_pitch_ref = midi_pitch_float[idx_start]
    if np.isnan(base_pitch_ref):
        return False

    q_ref = round(base_pitch_ref / QUANTIZATION_STEP) * QUANTIZATION_STEP
    base_semitone_int = int(np.clip(np.round(q_ref), 0, 127))

    vel = velocity_from_rms(rms[idx_start])

    note = pretty_midi.Note(
        velocity=vel,
        pitch=base_semitone_int,
        start=start_t,
        end=end_t
    )
    instrument.notes.append(note)

    emit_pitch_bend_events(instrument, times, midi_pitch_float, base_semitone_int, idx_start, idx_end)
    return True

def convert_audio_file(audio_path, midi_output, settings=None):
    """Convert an audio file to MIDI using the microtonal engine."""
    global PITCH_BEND_RANGE, QUANTIZATION_STEP, SLIDE_SPLIT_SEMITONES
    if settings:
        if 'pitchBendRange' in settings:
            PITCH_BEND_RANGE = float(settings['pitchBendRange'])
        if 'driftThreshold' in settings:
            SLIDE_SPLIT_SEMITONES = float(settings['driftThreshold'])
        if 'quantizationStep' in settings:
            QUANTIZATION_STEP = float(settings['quantizationStep'])

    TARGET_SR = 16000
    y, sr = librosa.load(audio_path, sr=TARGET_SR, mono=True, dtype=LOAD_DTYPE)

    f0_hz, voiced_flag, _ = librosa.pyin(
        y, fmin=FMIN, fmax=FMAX, sr=sr,
        frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH, center=PYIN_CENTER
    )

    frame_dt = HOP_LENGTH / sr
    times = np.arange(len(f0_hz), dtype=np.float32) * frame_dt

    midi_pitch = np.full(f0_hz.shape, np.nan, dtype=np.float32)
    voiced_flag = voiced_flag.astype(bool, copy=False)
    valid = (~np.isnan(f0_hz)) & voiced_flag
    midi_pitch[valid] = hz_to_midi_float(f0_hz[valid])

    try:
        from scipy.signal import medfilt
        midi_interp = midi_pitch.copy()
        valid_idx = np.where(~np.isnan(midi_pitch))[0]
        if valid_idx.size > 1:
            nan_idx = np.where(np.isnan(midi_pitch))[0]
            midi_interp[nan_idx] = np.interp(nan_idx, valid_idx, midi_pitch[valid_idx])
        win = PITCH_MEDIAN_WIN if (PITCH_MEDIAN_WIN % 2 == 1) else (PITCH_MEDIAN_WIN + 1)
        if win < 1:
            win = 1
        midi_smoothed = medfilt(midi_interp, kernel_size=win).astype(np.float32, copy=False)
        midi_pitch_smooth = midi_smoothed
        midi_pitch_smooth[~valid] = np.nan
    except Exception:
        midi_pitch_smooth = nanmedian_smooth(midi_pitch, PITCH_MEDIAN_WIN)

    rms = librosa.feature.rms(y=y, frame_length=FRAME_LENGTH, hop_length=HOP_LENGTH).flatten()
    rms_n = normalize_rms(rms)

    min_dist = max(1, int(round(0.02 / (HOP_LENGTH / sr)))) 
    onset_frames = energy_onsets_from_rms(rms_n, min_prominence=0.02, min_distance_frames=min_dist)
    onset_set = set(int(f) for f in onset_frames)

    # NOTE SEGMENTATION 
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
        if cooldown > 0:
            cooldown -= 1

        gate_on = (rms_n[i] >= GATE_ON)
        gate_off = (rms_n[i] < GATE_OFF)

        if not in_note:
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
            if (not is_voiced(i)) or gate_off:
                release_count += 1
            else:
                release_count = 0

            is_onset = (i in onset_set) and (cooldown == 0)
            pitch_dev = np.nan if base_ref_pitch is None or np.isnan(midi_pitch_smooth[i]) else (midi_pitch_smooth[i] - base_ref_pitch)

            tremolo_split = False
            if is_onset and (not np.isnan(pitch_dev)):
                if abs(pitch_dev) <= TREM_PITCH_TOL and (time_at(i) - time_at(idx_start)) >= MIN_NOTE_DUR_S:
                    tremolo_split = True

            slide_split = False
            if (not np.isnan(pitch_dev)) and (abs(pitch_dev) >= SLIDE_SPLIT_SEMITONES) and is_voiced(i):
                slide_count += 1
                if slide_count >= SLIDE_HOLD_FRAMES:
                    slide_split = True
            else:
                slide_count = 0

            should_end_for_release = (release_count >= RELEASE_FRAMES)
            should_end_for_trem = tremolo_split
            should_end_for_slide = slide_split

            if should_end_for_release or should_end_for_trem or should_end_for_slide:
                idx_end = max(i - (RELEASE_FRAMES if should_end_for_release else 0), idx_start + 1)

                if time_at(idx_end - 1) - time_at(idx_start) < MIN_NOTE_DUR_S:
                    idx_end = i
                    if time_at(idx_end - 1) - time_at(idx_start) < MIN_NOTE_DUR_S:
                        in_note = False
                        last_note_end_time = time_at(idx_end - 1)
                        idx_start = None
                        base_ref_pitch = None
                        release_count = 0
                        cooldown = COOLDOWN_FRAMES
                        continue

                added = add_note(instrument, times, rms_n, midi_pitch_smooth, idx_start, idx_end)
                if added:
                    last_note_end_time = time_at(idx_end - 1)

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

    if in_note and idx_start is not None:
        add_note(instrument, times, rms_n, midi_pitch_smooth, idx_start, n_frames)

    # WRITE MIDI
    midi.instruments.append(instrument)
    midi.write(midi_output)
    print(f"✅ Saved microtonal MIDI to {midi_output}  |  notes={len(instrument.notes)}  bends={len(instrument.pitch_bends)}")
    return midi


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: script.py <input_audio> <output_midi>")
        sys.exit(1)
    convert_audio_file(sys.argv[1], sys.argv[2])
