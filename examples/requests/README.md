# Example RewriteRequest payloads

Copy-paste inputs for `omni-rewriter expand`. Gallery viewing needs no GPU; expand needs any
OpenAI-compatible Writer that returns structured JSON.

| File | Task |
| --- | --- |
| `t2va_kite.json` | MiniMax-H3 style video PE |
| `t2i_neon.json` | Seedream T2I PE |
| `image_edit_dress.json` | Qwen-Image-Edit PE (synthetic reference URL) |

```bash
export OMNI_WRITER_BACKEND_BASE_URL=https://api.openai.com/v1
export OMNI_WRITER_BACKEND_MODEL=gpt-5.6
export OMNI_WRITER_BACKEND_API_KEY=sk-...
omni-rewriter expand examples/requests/t2va_kite.json --output h3
```
