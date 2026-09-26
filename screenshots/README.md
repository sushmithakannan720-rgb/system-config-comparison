# Screenshots

Real screenshots captured from the running application:

| File | Page |
|------|------|
| `01_dashboard.png` | Dashboard after a live system scan |
| `02_details.png` | System Details page (cards + usage bars) |
| `03_comparison.png` | Compare page with a full comparison result |

To regenerate them (Linux, needs Xvfb + ImageMagick):

```bash
xvfb-run -a -s "-screen 0 1280x800x24" python tests/make_screenshots.py
```

On Windows simply run `python tests/make_screenshots.py` (ImageMagick's
`import` command is required) or take screenshots manually.
