# Christian Verrecchia — Engineering Portfolio

Power electronics, magnetics, embedded electronics and validation, with a self-contained browser-based Converter Loss Lab.

- **Portfolio:** https://chrisver93.github.io/Portfolio/
- **Loss Lab:** https://chrisver93.github.io/Portfolio/tools/loss-lab/

## One repository, one deployment

The portfolio and loss tool deploy together to GitHub Pages. The tool requires no ChatGPT service, server, account or database. Calculations run locally in a browser worker; imported data stays in the browser. Browser storage is local: export project JSON to move between computers or domains.

## Structure

- `dist/` — portfolio HTML, CSS and JavaScript
- `dist/tools/loss-lab/` — complete runnable loss tool, MATLAB exporter and downloadable documentation
- `tests/loss-lab/` — numerical, import and workflow regression tests with synthetic MAT fixtures
- `.github/workflows/pages.yml` — verifies the engine, then deploys `dist/`

## Development

Run `npm test` with Node 22 or later. No dependency installation or build is needed. Serve `dist/` with a static HTTP server to work locally; opening HTML directly as `file://` may block module workers.

## Deploy

GitHub Pages uses **Settings → Pages → Source: GitHub Actions**. Push to `main` to verify and publish both portfolio and tool. All asset links are relative, so the site can move to a custom domain without rewriting the tool.

## Model coverage

See `dist/tools/loss-lab/FEATURES.md` and `verification.json`. Numerical estimates depend on waveform mappings, curve coverage and model assumptions. Extrapolation warnings remain visible. Full MATLAB runtime parity and physical accuracy are not established.

## Portfolio content

Project graphics are illustrative and labelled. Public contact information can be added when supplied. Browser interaction and print-layout QA were unavailable in the creation environment.
