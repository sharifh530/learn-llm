"""Cross-field checks for authored visual traces, without executing lesson code."""
import math

def validate_visual(lesson):
    visual = lesson.get('visual')
    if not visual:
        return
    line_count = len(lesson['python_example']['code'].splitlines())
    for frame in visual['frames']:
        if len(frame['lines']) != len(set(frame['lines'])) or any(line > line_count for line in frame['lines']):
            raise ValueError(f"{lesson['id']}: visual focus must refer to unique existing Python lines.")
        if frame['layout'] == 'bars' and any('amount' not in item for item in frame['items']):
            raise ValueError(f"{lesson['id']}: every visual bar needs a bounded amount.")
        if any('amount' in item and not math.isfinite(item['amount']) for item in frame['items']):
            raise ValueError(f"{lesson['id']}: visual bar amounts must be finite.")
    if visual['frames'][-1]['console'] != lesson['python_example']['expected_output']:
        raise ValueError(f"{lesson['id']}: the final visual console must match the Python example output.")
    choices = visual['challenge']['choices']
    if sum(choice['correct'] for choice in choices) != 1 or len({choice['text'] for choice in choices}) != len(choices):
        raise ValueError(f"{lesson['id']}: the visual challenge needs one correct, distinct choice.")
