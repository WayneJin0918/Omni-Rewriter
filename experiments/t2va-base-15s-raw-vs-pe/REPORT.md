# MiniMax-H3 Base 15s: Raw vs Omni-Writer PE

## Experiment

- 10 T2VA scenarios, 2 arms per scenario, 20 videos total.
- Raw and PE arms use the same seed, 768 short edge, 16:9 aspect ratio, and
  15-second target.
- PE backend: Qwen3.5-122B-A10B on 8 GPUs.
- Video backend: MiniMax-H3 FL2VA partition through SGLang, Ulysses degree 8
  on 8 H200 GPUs.
- Omni-Writer revision: recorded in `experiment.json`.
- SGLang source revision: `03f44c978acb00ae1ca45deb94e71d000c31b183`.

## Media validation

- 20/20 files contain both video and audio streams.
- Every output is 15.083 seconds.
- Video: H.264, 1344x768.
- Audio: AAC, 32 kHz, stereo.
- Total output size: 58,298,559 bytes.

Machine-readable probe results are in `eval/media_probe.json`.

## Prompt validation

- 10/10 PE prompts passed deterministic Omni-Writer validation.
- Five prompts passed on the first draft.
- Five prompts required one deterministic repair cycle.
- PE prompt text and complete envelopes are preserved under `pe/`.

## Comparison

Open `comparison.html` for ten side-by-side pairs. Each player keeps its own
audio track so Raw and PE audio are never mixed.

For a blind perceptual decision, hide the captions and score each pair on:

1. prompt adherence;
2. dialogue intelligibility, language correctness, and lip sync;
3. ambient and music fidelity;
4. action/audio synchronization;
5. shot timing and continuity;
6. physical plausibility;
7. visual and audio artifacts.

The experiment verifies structure and media integrity automatically. It does
not label PE as the winner without a perceptual review of the generated media.
