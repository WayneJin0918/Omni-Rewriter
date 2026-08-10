# Example RewriteRequest payloads

Copy-paste inputs for `omni-rewriter expand`. Gallery viewing needs no GPU; expand needs any
OpenAI-compatible Writer that returns structured JSON.

| File | Task |
| --- | --- |
| `t2va_kite.json` | MiniMax-H3 style video PE |
| `seedance_t2va_kitchen.json` | Seedance video PE (`natural` / public 2.5 template) |
| `seedance_ref2va_interview.json` | Seedance ref2va PE (`json` render; placeholder refs) |
| `seedance_ref2va_pottery.json` | Seedance ref2va with typed `@Image` / `@Video` roles |
| `t2i_neon.json` | Seedream T2I PE |
| `image_edit_dress.json` | Qwen-Image PE (synthetic reference URL) |

```bash
export OMNI_WRITER_BACKEND_BASE_URL=https://api.openai.com/v1
export OMNI_WRITER_BACKEND_MODEL=gpt-5.6
export OMNI_WRITER_BACKEND_API_KEY=sk-...
omni-rewriter expand examples/requests/t2va_kite.json --output h3
omni-rewriter expand examples/requests/seedance_t2va_kitchen.json --output seedance
```
