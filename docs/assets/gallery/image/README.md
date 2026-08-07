# Real image RAW vs PE samples

These low-resolution WebP files are derived from reproducible local runs. Labels
and prompts live in HTML/Markdown, not inside image pixels.

| Prefix | Model | Comparison |
|---|---|---|
| `qwen_t2i_*` | Qwen-Image-2512 | identical seed/size/steps, RAW vs PE prompt |
| `qwen_edit_*` | Qwen-Image-Edit-2511 | identical reference/seed/steps, RAW vs PE instruction |
| `hunyuan_t2i_*` | HunyuanImage-3.0 | identical seed/ratio, RAW vs PE prompt |

Full-resolution outputs and provenance manifests are generated under
`experiments/image-pe-raw-vs-pe/outputs/` and remain gitignored. Reproduce with:

Committed hardware, model, seed, size, step, and runtime details are recorded in
[`experiments/image-pe-raw-vs-pe/GENERATION_RUNS.md`](../../../../experiments/image-pe-raw-vs-pe/GENERATION_RUNS.md).

```bash
# Qwen environments
CUDA_VISIBLE_DEVICES=0 /pfs/weiyang/Miniconda3/envs/qwenimage/bin/python \
  experiments/image-pe-raw-vs-pe/run_experiment.py generate --backend qwen-t2i
CUDA_VISIBLE_DEVICES=0 /pfs/weiyang/Miniconda3/envs/qwenimage/bin/python \
  experiments/image-pe-raw-vs-pe/run_experiment.py generate --backend qwen-edit

# Hunyuan environment
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
  /pfs/weiyang/Miniconda3/envs/hyimage/bin/python \
  experiments/image-pe-raw-vs-pe/run_experiment.py generate --backend hunyuan
```
