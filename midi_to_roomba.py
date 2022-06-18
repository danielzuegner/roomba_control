import argparse
from mido import MidiFile
import json

def parse_midi(file, track, meta_track=None):
    mid = MidiFile(file, clip=True)
    tempo = 500000 # 120 BPM
    ticks_per_beat = mid.ticks_per_beat

    tempos_at_ticks = {}
    if meta_track is not None:
        ticks = 0
        for msg in mid.tracks[meta_track]:
            if msg.type == 'set_tempo':
                print(msg)
                tempos_at_ticks[ticks] = msg.tempo
                ticks += msg.time

    notes, durations = [], []
    all_notes = []
    all_intervals = []
    active_notes = []
    last_was_note_on = False
    tick_count = 0
    total_64th_seconds = 0
    for msg in mid.tracks[track]:
        tick_count += msg.time
        if len(tempos_at_ticks) > 0:
            tempo_ix = max([k for k in tempos_at_ticks.keys() if k <= tick_count])
            tempo = tempos_at_ticks[tempo_ix]
            print(tick_count, tempo)

        if msg.type == 'set_tempo':
            print(msg)
            tempo = msg.tempo
        delta_ticks = msg.time
        delta_microseconds = tempo * delta_ticks / ticks_per_beat
        delta_seconds = delta_microseconds / (1000 ** 2)
        delta_64th_second = round(delta_seconds * 64)
        total_64th_seconds += delta_64th_second

        if msg.type == 'note_on' and not msg.velocity == 0:
            active_notes.append((msg.note, total_64th_seconds))

        elif msg.type == "note_off" or (msg.type == 'note_on' and msg.velocity == 0):
            ixs = [ix for ix, x in enumerate(active_notes) if x[0] == msg.note]
            ix = ixs[0]
            tpl = active_notes.pop(ix)
            all_notes.append(tpl[0])
            all_intervals.append(set(range(tpl[1], total_64th_seconds + 1)))

    buffer_size = 10
    filtered_notes = []
    iou_threshold = 0.5
    for ix in range(len(all_intervals)):
        interval = all_intervals[ix]
        note = all_notes[ix]
        from_ix = max(0, ix - buffer_size)
        to_ix = ix + buffer_size + 1
        buffer_intervals = all_intervals[from_ix: ix] + all_intervals[ix + 1: to_ix]
        buffer_intervals_after = all_intervals[ix + 1: to_ix]
        overlaps = [len(interval.intersection(other)) for other in buffer_intervals]
        buffer_notes = all_notes[from_ix: ix] + all_notes[ix + 1: to_ix]
        buffer_notes_after = all_notes[ix + 1: to_ix]
        ious = [len(interval.intersection(other)) / len(interval) for other in buffer_intervals]
        ious_after = [len(interval.intersection(other)) / len(interval) for other in buffer_intervals_after]
        
        large_iou_ixs = [ix for ix, x in enumerate(ious) if x > iou_threshold]
        cont = False
        for iou_ix in large_iou_ixs:
            if note < buffer_notes[iou_ix]:
                cont = True
                break
        if cont:
            continue
        nonzero_iou_ixs_after = [ix for ix, x in enumerate(ious_after) if x > 0]
        earliest_start = max(interval)
        for iou_ix in nonzero_iou_ixs_after:
            if note < buffer_notes_after[iou_ix]:
                other_interval = buffer_intervals_after[iou_ix]
                earliest_start = min(min(other_interval), earliest_start)
        interval = set(range(min(interval), earliest_start + 1))
        assert len(interval) > 0
        filtered_notes.append((note, interval))

    notes, durations = [], []
    previous_max = None
    for note, interval in filtered_notes:
        if previous_max is not None:
            if min(interval) - previous_max > 0:
                notes.append(0)
                durations.append(min(interval) - previous_max - 1)
        notes.append(note)
        durations.append(max(interval) - min(interval))
        previous_max = max(interval)
    return notes, durations
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--track-id', '-t', type=int, default=0)
    parser.add_argument('--meta-track', '-m', type=int, default=None)
    parser.add_argument('--out-file', '-o', type=str, default='out.json')

    args = parser.parse_args()
    notes, durations = parse_midi(args.file, args.track_id, args.meta_track)

    with open(args.out_file, 'w') as f:
        json.dump({
            'notes': notes,
            'durations': durations
        }, f)
    print(f'Successfully wrote output to {args.out_file}')