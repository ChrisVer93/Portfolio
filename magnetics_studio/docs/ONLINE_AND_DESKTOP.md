# Online and Windows development previews — R002 / v0.9.32

The user explicitly authorised a development executable and GitHub publication on 22 November 2026. This supersedes the earlier prohibition on building any application executable before feature completion. It does not establish final feature completion, industrial parity, signed release status or clean-Windows qualification.

## Online tool

The stable entry is https://chrisver93.github.io/Portfolio/tools/magnetics-studio/ and the portfolio Tools page links to it. The original interface, builder, independent winding/container/layer semantics, B-H digitiser, visualisation and field exports are reused. A pinned Pyodide 0.27.7 WebAssembly worker runs the actual original standard-library reference Python. No saved result or substitute JavaScript approximation stands in for a new field solve.

Supported online computation follows the original reference paths: 2D/3D static fields, reversible nonlinear 2D where supported, ordinary meshes, reference current/convergence studies, original 2D adaptation, dedicated linear 2D AC and frequency studies. Existing physical limitations still apply. Original native compiled PyOpenMagnetics design, Netgen/NGSolve and CAD are unavailable in this browser build and reported as unavailable to existing controls. The desktop download link remains visible. Core screening and designer requests are not falsely converted into reference FEM.

The initial browser mesh is additionally limited to 24,000 estimated cells; a real operation is terminated after 240 seconds. A dedicated worker preserves UI responsiveness. Cancellation terminates the actual worker and reinitialises Python for later requests. The main-page adapter retains only complete accepted results, the prior solved field/export and explicit job identities. Unsupported native and invalid static/AC requests fail preflight without replacing the accepted job. Cancellation also handles the asynchronous preflight/initialisation interval. Original FEM fields are not rewritten.

The engine packet contains exact original Python, inputs and required report-view resources, with source SHA256 values in version.json. Assets use tool-relative URLs under /Portfolio/tools/magnetics-studio/. The digitiser sample image and original report template/scripts are included. Initial browser runtime/assets require network access; this online preview is not advertised as an offline installation. Project data remains in the browser execution path. Export project JSON to move between browser domains or desktop. Browser local storage is separate for each origin.

## Windows tool

Successful main-branch builds publish source-commit-specific development prereleases under https://github.com/ChrisVer93/Portfolio/releases. Download MagneticsStudio-Windows-x64.zip, extract the complete folder and run MagneticsStudio.exe. Keep the console open while using the browser UI. The full folder, including _internal, is required. Python and installed native dependencies are bundled; the application launches a loopback-only original server and default browser. No installer or one-file frozen package is introduced.

The private --backend-worker entry executes the original whitelisted native worker in another copy of the frozen executable. Source execution retains its original Python child invocation. Resource paths follow PyInstaller’s actual __file__ layout. Existing Host/token/origin protections, source validation, isolated cancellation and native budgets are preserved. Native availability retains exact original version guards.

Pinned build dependencies are listed in requirements-desktop.txt. The preview includes PyOpenMagnetics 1.7.35, NumPy/SciPy, CadQuery 2.7.0 with OCP 7.8.1.1.post1, Netgen/NGSolve 6.2.2608 and MVB 0.6.12. The historical core-only screening bridge still expects CadQuery 2.6.1, so that separate route remains unavailable in this shared 2.7.0 bundle. No qualification pin is silently relaxed. The newer geometry-CAD route retains its own 2.7.0 guard. Metadata availability alone does not prove every optional native feature on Windows.

The first real Windows branch build ran on GitHub’s Windows Server 2025 runner. The exact frozen package passed original HTML/resources, actual project JSON roundtrip, a nonzero reference solve, actual OpenMagnetics design through frozen-to-frozen worker dispatch, genuine native cancellation, retained previous FEM field and JSON/CSV/VTK/HTML exports. Child PATH contained only Windows system directories; Python was absent from that PATH. The build runner still has Python installed for building. Proxy variables in the application point to a closed loopback port, while loopback HTTP is allowed; this is not a physical offline-host/firewall qualification. Browser/OS picker and clean Windows 10/11 without Python installed remain final-release checks.

BUILD_PROVENANCE.json and desktop-smoke.json accompany each tested package. SHA256.txt describes the published archive. Existing exact upstream notices are retained; the build also copies actual transitive distribution metadata/licence files into THIRD_PARTY_NOTICES. This is notice collection, not a completed legal/dataset redistribution audit. No mandatory prominent MIT co-branding is inferred.

## Reproducible checks and publication

```text
python tools/build_browser.py ../static-preview
NODE_PATH=<QA node_modules> node tests/browser-runtime.test.cjs ../static-preview
# On a permitted Windows build host with exact dependencies installed:
python tools/build_desktop.py ../magnetics-build
node tests/desktop_smoke.cjs ../magnetics-build/MagneticsStudio/MagneticsStudio.exe
python -m unittest tests.test_release_surfaces tests.test_transformer_designer -v
```

QA-only Node dependencies are Pyodide0.27.7, jsdom26.1.0 and @napi-rs/canvas0.1.100. Browser CI additionally uses Playwright1.62.1 and its Chromium. They are not desktop application dependencies. Local DOM checks label synthetic viewport/file delivery; the Pages pipeline separately runs actual native Chromium controls, downloads/imports and screenshots before publishing.

The existing GitHub Pages workflow preserves Loss Lab regression checks, builds the preview from checked-in source, executes real Wasm/DOM and native Chromium checks, then deploys. A failed check skips upload/deployment and leaves the previous published site intact. The Windows workflow builds only on relevant source/recipe changes, tests the exact package, and publishes successful main builds as development prereleases. Report-only changes do not rebuild Windows. Branch build artifacts expire after 30 days; GitHub release assets are the durable user download.

An early native Chromium test checked designer availability before its asynchronous backend response. It correctly blocked publication. The final check waits for the actual capability state. An earlier local full profile became source_changed when final UI test/export resources were edited; its counts are not credited as final-source qualification. Legacy tests also regenerate evidence at historical paths; original bytes were restored, new outputs retained separately, and final discovery rerun in a detached checkout. Final source-bound receipts and actual CI evidence are recorded in the numbered report.

## Continuing development

For each accepted future source increment, preserve the canonical archive identity/version guard and original historical reports. Synchronise the corresponding runtime/build/test changes to ChrisVer93/Portfolio/magnetics_studio, retain the existing Pages/Windows checks and verify their outcomes. Keep this fixed online URL. Preserve unrelated portfolio/Loss Lab work with current GitHub SHA guards. Failed build/deployment is not a completed release. Do not claim continuous execution between scheduled runs.

Physical source/mesh/order/domain convergence, full joined winding/return/core coupling, broader adviser/safety/manufacturing constraints, native nonlinear/AC and full CLLC remain development work. Genuine Maxwell/hardware benchmarks and final clean-Windows release qualification are still pending.
