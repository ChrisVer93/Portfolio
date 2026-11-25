# S005 verification checkpoint — 25 November2026; runtime remains v0.9.35

Independent free-space Biot–Savart sheet-current local-field verification now records four actual reference3D solves (750/6000/4374/34992tetrahedra). Fine-mesh centre discrepancies11.16–11.23%, off-axis32.89–33.09%; maximum independent quadrature refinement change0.004758%, with a separately evaluated centre expression check passed. No design/accuracy qualification is inferred. Direct34992-cell QA exceeds GUI port-study24k ceiling; no production budget changed. No runtime/build/test/physics files changed; previous256passed20skipped profile remains historical, not rerun today. See verification/verify_sheet_field_s005.py, sample_results/local_field_s005/ and docs/reports/Task_S005_Local_Field_Verification_Report.html for every added executable line, exact models, actual vectors/logs, equations/units/boundaries and limitations.

NEXT: isolate persistent local-field discretization/source representation errors via further mesh/order and independently sampled field studies; retain prior working runtime and all existing physical/Windows qualification limits. Earlier entries follow.

# Current checkpoint — v0.9.35 / S004, 24 November2026

The separate S004 report explains all220added/replacement executable/declaration lines across17files. All3402protected prior files, including83prior report HTML/evidence files, remain byte-identical; original PDE/material/source/sparse kernels are unchanged.

Verified publication: Pages45465471831/job138699124831 and Windows45465471823/job138699125137 both SUCCESS on runtime commit93ba15717c15802bf80249b6aa948545d41d2ff3. Actual native Chromium interval-study/download and exact frozen interval-study/adviser/cancel/export checks passed. Windows DEVELOPMENT ZIP: https://github.com/ChrisVer93/Portfolio/releases/download/magnetics-93ba15717c15/MagneticsStudio-Windows-x64.zip (268049991bytes; SHA2561932a27d977e053b3db918717ebb164d92fa688882848e1c747908a273733a57). Final clean-Windows and physical/commercial qualification remain pending.

Actual final qualification:43independently audited modules,256Python passed,20optional native FEM/CAD checks skipped,zero failed/error/unverified. Three new focused methods also passed separately in pure Python (counts overlap discovery); all105existingJavaScript checks and genuine WebAssembly interval-study/field-retention checks passed. Source CLI independently reproduced all4spatial project/mesh hashes and full measurement records. Both tested ordinary2D/3D fixture result bytes match v0.9.34 exactly after excluding both elapsed timings. Runtime GitHub commit93ba15717c15802bf80249b6aa948545d41d2ff3:14exact matched blobs,13existing guards,zero unrelated changes.

The original Inductance port study now offers **Every fitted interval**: explicit dyadic1/2/4 subdivision of every fitted core, gap, winding and exterior interval. Fine simplices remain inside coarse simplices; every original plane, material-tag area/volume and physical source is preserved. The ordinary mesh path is preserved; both tested2D/3D fixture fields are exact against v0.9.34 after excluding only both elapsed timings. Shared mesh-mode/factor metadata and full mesh-hash checks reproduce the actual refined solve. Old API requests without mode retain target behavior; UI/CLI default to interval. UI, source CLI and genuine browser/frozen tests use the same reference physics. No new runtime dependency.

Actual planar air1:286→1144→4576triangles, Lshort119.418337→134.337963→138.564143µH (last3.050%change). Spatial air2:1350→10800tetrahedra,67.703977→127.613812µH (46.946%change). Fine spatial air1→2 changes128.143505→127.613812µH (0.413%). These remain coarse unqualified models; air sensitivity does not bound mesh error. Uniform refinement keeps aspect ratios and does not complete adaptive refinement/quality optimization or physical/Maxwell validation. Same ideal planar paired currents/spatial sheets, linear materials and closed exterior boundary. No finite transformer copper, loaded resonant network or native nonlinear/AC is added.

Exact algorithm, PDE/source/boundary/units/assumptions, reproducible real crossed cases and exhaustive source/per-line report: docs/INTERVAL_REFINEMENT.md, sample_results/interval_refinement/, docs/reports/Task_S004_Interval_Refinement_Report.html. All historical reports/evidence are preserved. The first focused command lacked source PYTHONPATH and failed import; the first whole-result equivalence comparison omitted nested solver timing and failed on timing only. Both failures remain explicit; only corrected complete/source-bound evidence is credited.

Latest22November override permits DEVELOPMENT executables and GitHub publication; final clean permitted Windows10/11 offline/noPythoninstalled and complete physical/commercial qualification remain pending. Fixed app https://chrisver93.github.io/Portfolio/tools/magnetics-studio/ ; preserve unrelated portfolio/LossLab work, current canonical identity/version and GitHub commit/blob guards. SourceZIP remains ZIP_LZMA with Python standard-library extraction; Explorer extraction remains unqualified.

NEXT: adequate source/p/order/domain/local-field accuracy, measured joined finite winding/return/core, matched adviser/FEM model conventions, native nonlinear/AC and full CLLC; genuine Maxwell/hardware references and complete redistribution/data-rights audit remain open. No claim of commercial parity or continuous execution. Earlier entries below are historical.

# Current checkpoint — v0.9.34 / S003, 23 November2026

Verified publication: Pages run45250963615/job137960156201 and Windows run45250963995/job137960156169 both passed on runtime commitb20c4a9c22b5ac45ad0548f6ae62182f29900f66. Actual native Chromium study/download and frozen study/adviser/cancel/export checks passed. Windows DEVELOPMENT ZIP: https://github.com/ChrisVer93/Portfolio/releases/download/magnetics-b20c4a9c22b5/MagneticsStudio-Windows-x64.zip (268049013bytes; sha256:fe30a44cc9b64116f1af57902eca7e37715a6c1862cf3645eeb84e1858a80773). Report explains all249added/replacement executable/declaration lines across16files;3194prior files remain byte-identical. Final clean-Windows and physical/commercial qualification remain pending.

Actual final regression:42independently audited modules,253Python passed,20optional native checks skipped,zero failed/error/unverified. Three new focused methods also passed separately in pure Python (overlap discovery). All105existingJavaScript checks and real WebAssembly study/field-retention tests passed. The actual source CLI reproduced all6spatial study project/mesh hashes and full measurement records exactly. Tested runtime commitb20c4a9c22b5ac45ad0548f6ae62182f29900f66 uses15exactly matched GitHub blobs with11existing-file guards and zero unrelated changes.

Inductance now offers a genuine reference linear2D/3D mesh/air study for the explicitly selected input/shorted electrical ports. Every point solves the complete original field/matrix. Rigid source translation expands only exterior air; material/turn/polarity/section order remain fixed and planar depth is unchanged. Integer factors retain nominal physical mesh spacing for air comparisons. Exact generated projects, project/mesh hashes, actual cell counts, matrices and separate sensitivity axes are exported. Identical adjacent fitted meshes are flagged and excluded from refinement evidence. Original project, accepted field and existing workflows are retained. CLI tools/study_ports.py and shared desktop/browser job action use actual fitted preflight budgets and original cancellation.

Actual six-point3D study at air2 changes short input99.587301to133.840929µH on5280to16224tetrahedra (25.593% normalized mesh change). At mesh3, air expansion changes131.482603to133.840929µH (1.762%). Planar h1/h2,a1 are identical286triangle meshes; h3 gives127.910504µH versus119.418337µH coarse (6.639%). These coarse models are NOT converged or design-qualified. Empirical changes are not error bounds; exterior mesh topology also changes during air expansion. No source/p/physical/external accuracy or new PDE/mesh kernel is claimed.

Final source-bound regression/actual CI evidence is in sample_results/port_study/ and docs/reports/Task_S003_Port_Convergence_Report.html; usage/model/units/resources/limits in docs/PORT_STUDY.md. The earlier local profile predates the identical-fitted-mesh guard and is retained as different-source/unqualified evidence. Only the fresh final profile is credited. Separate focused and pure-Python methods overlap discovery; original105JavaScript checks and real WebAssembly study/field retention checks pass. Native Chromium and exact frozen Windows study/adviser/cancel/export CI outcomes, guarded source commits and development-download digests are recorded in publication.json and the report.

Fixed online reference preview remains https://chrisver93.github.io/Portfolio/tools/magnetics-studio/ . Latest user permits development executables and per-increment GitHub sync+CI with current guards, preserving unrelated portfolio/Loss Lab work. Native adviser/CAD/NGSolve remain desktop-only; legacy core-only CadQuery2.6.1 guard is not relaxed. Clean permitted Windows10/11 offline/noPythoninstalled launch/open/save/solve/cancel/export, full feature/physical/commercial qualification and redistribution audit remain pending. SourceZIP remains ZIP_LZMA; use Python standard-library extraction; Explorer extraction remains unqualified.

NEXT: source/p/order/domain/local-field accuracy and larger crossed studies at adequate resolution, actual joined finite winding/return/core, matched adviser/FEM model conventions, native nonlinear/AC and full CLLC. No Maxwell/hardware parity or continuous execution is promised. Always resolve latest canonical/GitHub metadata and retain identity/version/commit/blob guards. Earlier entries are historical.

# Current checkpoint — v0.9.33 / S002, 22 November 2026

Verified publication: Pages run45058050128 on workflow-fix commit0c7a4f9e4692fd09f22849801b695a6a3c7cd9b4 passed actual Wasm/Chromium controls and deployment. Windows run45057624001 on runtime commit968699f880731bf98502efdc3de48defd7ece12c passed exact frozen API/adviser/cancel/export/new reduction checks and published https://github.com/ChrisVer93/Portfolio/releases/download/magnetics-968699f88073/MagneticsStudio-Windows-x64.zip (268037695bytes, SHA256b3e0169218464ad0c7807e11f8f13d091e894a392b1d181f50166671aafb76c2). Earlier Pages attempts passed all application tests but failed absent/duplicate artifact lookup. Unique run/attempt artifact naming, read-only Actions access and bounded metadata checks corrected publication. Full failure logs remain. The S002 report explains all265added/replacement executable/declaration lines across15files and verifies3073prior files unchanged.

Linear 2D/3D matrix results now offer explicit input and simultaneous-shorted-winding selection in Inductance. Canonical electrical IDs define independent ports; equal display names do not connect sources. The shared standard-library reduction retains all short-to-short mutual terms, computes cancellation currents, checks normalized reciprocity/positive energy/independence, and exports the exact supplied matrix/digest, source project and solver metadata. Field/job/source data are retained. Nonlinear/AC results without a real static matrix have no control; dependent ideal modes are rejected without invented pseudoinverses.

The 338-triangle planar test gives open1216.731151958µH / both-short119.418354605µH. The 2940-tetrahedron spatial ideal-sheet test gives open168.095713276µH / both-short131.482603490µH. Independent prescribed-current field re-solves cancel shorted linkage and agree with predicted energy within4.55e-11 relative. These are same-model linear consistency checks, not mesh/domain or physical accuracy, finite-copper qualification or Maxwell validation. Open-input self and cancelled coupling are explicitly not a unique magnetising/leakage T-network split. No PDE, material, source, mesh or sparse kernel changed.

Actual final source profile:41 independently audited modules,250Python passed,20optional native checks skipped,zero failed/error/unverified. Four new methods also pass separately in pure Python; counts overlap discovery. All105existingJSchecks and genuine WebAssembly/DOM integration pass. Real protected HTTP characterization leaves accepted job/field state intact. Complete results and per-line source report: docs/PORT_REDUCTION.md, sample_results/port_reduction/ and docs/reports/Task_S002_Multiwinding_Shorts_Report.html.

Tested runtime source is GitHub commit968699f880731bf98502efdc3de48defd7ece12c in ChrisVer93/Portfolio; fixed online URL remains https://chrisver93.github.io/Portfolio/tools/magnetics-studio/ . CI publication outcomes and exact Windows development-preview URL/hash are recorded in sample_results/port_reduction/publication.json and the separate report. No clean permitted Windows10/11 offline/no-Python-installed qualification is inferred from Server-runner smoke. The latest user authorised development-preview executables; the old final-only restriction is superseded for previews. Final physical/commercial/parity and clean-host release qualification remain pending.

NEXT PHYSICS: independent source/mesh/p/domain/observable accuracy, joined finite winding/return/core coupling, matched adviser-candidate FEM and model conventions, native nonlinear/AC and full CLLC. Genuine independent Maxwell/hardware evidence and complete redistribution/data-rights audit remain open. Preserve original workflow and historical reports/evidence. Resolve latest canonical metadata and GitHub commit/blob guards before every accepted update. Do not promise continuous execution between scheduled runs.

Earlier entries are historical.

# Current checkpoint — v0.9.32 / R002, 22 November 2026

User explicitly authorised building a development executable now and deploying Magnetics Studio in GitHub alongside Loss Lab. This supersedes the earlier no-executable-before-final timing restriction for development previews; final feature completion, physical/commercial parity and clean-Windows release qualification remain pending.

LIVE: https://chrisver93.github.io/Portfolio/tools/magnetics-studio/ . The original interface and exact standard-library reference Python now run in a Pyodide 0.27.7 worker. Genuine reference 2D/3D fields, dedicated linear 2D AC, original builder/B-H/MAS workflows and original field exports are retained. Native adviser/CAD/NGSolve do not run in this browser preview and are explicitly unavailable. Browser initial mesh budget is 24000 cells and actual worker time budget240s. True worker termination/cancellation retains accepted prior field/export data. Original kernels/electrical/material/layer semantics are unchanged.

WINDOWS: https://github.com/ChrisVer93/Portfolio/releases/tag/magnetics-a1a4b5ec3441 . Source commit a1a4b5ec34417b5d4bdebb6bb94a1e15152f5454. Actual Windows Server2025 runner built the one-folder frozen application and passed bundled originalHTML, projectJSON roundtrip, nonzero reference solve, genuine frozen-to-frozen OpenMagnetics adviser (2passing candidates), actual native cancellation, prior field retention and JSON/CSV/VTK/HTML exports. Python was absent from the child PATH; it remains installed on the build host. Proxy variables pointed at a closed loopback port, with loopback HTTP allowed; no OS-wide offline/clean-host claim. Package268026780bytes; SHA256425c85e1b0ea4f39e7058036885e6bbcaaafd0ed6682ffe0c6551a5cf02d448b. Exact upstream notices/metadata collected. New geometry-CAD/NGSolve metadata are enabled, not new Windows numerical qualification. Legacy core-only bridge remains disabled because its existing CadQuery2.6.1 guard is not relaxed for the shared2.7.0 bundle.

Actual final source profile:40independently audited modules,246Python passed,20optional nativeFEM/CAD skips,zero failures/errors/unverified. Four new real adapter tests and five retained actual native-adviser CLI/HTTP methods pass; these overlap discovery. All105existingJSchecks and five pure-PythonDCmethods pass. Actual WebAssembly/DOM checks run original nonzero2D/3D/AC fields, allfieldexports, unavailable-native preflight, worker cancellation and accepted-field retention. Native Chromium151 / Playwright1.62.1 passes original solve controls, real project download/input import, field download and capability state. Live deployed 2D UI separately displayed Bpeak0.29131T, energy0.0056343J,1860triangles/992nodes. These are actual rounded observations, not new physical convergence/Maxwell evidence.

An initial native Chromium fixture checked capability state before its asynchronous reply, blocked publication, and was corrected to await the genuine state. An earlier local profile became source_changed during final UI/report-resource test improvements and is retained as unqualified evidence. Final qualification uses only fresh complete source-bound receipts; no failed/incomplete counts are credited.

See docs/ONLINE_AND_DESKTOP.md, deployment/, sample_results/release_preview/ and docs/reports/Task_R002_Online_Windows_Preview_Report.html for exact source/per-line explanations, CI output, resource/model assumptions, real tests and limits. Existing reports/evidence are preserved. The full Windows ZIP is in the source-specific GitHub prerelease; it is not duplicated into this source archive. Source ZIP_LZMA extraction continues to require documented Python extraction; Explorer remains unqualified for that source ZIP. The Windows build uses a separate ordinary ZIP and complete folder.

FUTURE PUBLICATION: sync each accepted runtime/build/test increment to ChrisVer93/Portfolio/magnetics_studio with current GitHub commit/blob guards. Existing Pages workflow gates publication on real Wasm/DOM and Chromium checks; Windows workflow builds/tests relevant changes and publishes passing main builds as source-commit-specific development prereleases. Fixed online URL stays the same. Preserve unrelated Loss Lab/portfolio work and existing canonical Library identity/version guards. No promise of continuous execution between scheduled runs.

NEXT PHYSICS: independent source/p/order/domain and observable accuracy; actual joined winding/return/core coupling; broader adviser/insulation/manufacturing constraints and matched candidate FEM; native nonlinear/AC and full CLLC. Genuine Maxwell/hardware references, complete redistribution/data-rights audit and final clean permitted Windows10/11 offline checks without Python installed remain pending.

Earlier entries are historical.

# Current checkpoint — v0.9.31 / D001, 21 November 2026

The separate **Design transformer** button beside Builder and source CLI now generate actual two-winding catalogue transformer candidates from primary Lm/optional leakage/turns-ratio bands, both winding voltage/current waveforms at 1–4 operating corners, and explicit B/loss/temperature/core-envelope limits. The pinned full OpenMagnetics adviser uses its installed core/material/bobbin/wire catalogue; no duplicate database is introduced. Studio re-simulates every candidate and separately checks actual turns, nominal fit, both Lm evaluations, primary/secondary leakage referral, all declared per-corner limits and actual core dimensions. Rejected candidates and missing-model errors remain explicit.

The illustrative 50 W sinusoidal 100 kHz / 25 °C case produces two passing RM 6-R / material 97 28:14 component candidates. Lowest-loss direct Lm=193.426981853µH, primary leakage=0.639741510µH, estimated peak B=0.133092900T, estimated total loss=0.947996172W and model maximum temperature=93.653537°C. A third candidate fails leakage/temperature. Adding a hotter second corner rejects all three returned candidates. Changing targets to 400 µH / 3:1 generates different 60:20 / 65:22 windings but all fail the unchanged 100 °C gate. These are bounded searches, not global feasibility/optimality proofs or physical validation.

Actual final verification: 39 independently audited source modules; 245 Python cases passed, 17 optional native FEM/MVB/CAD cases skipped, zero failure/error/unverified. Five focused helper/nativeCLI/HTTP methods pass (overlap discovery), all 105 unchanged JS checks and five pure-Python DC methods pass. Real DOM+rastercanvas+protectedHTTP/native-worker integration passes form/SI mapping, exact requirements/result/MAS downloads, actual cancellation, no-match/rejected-input/stale labels, escaped names and original nonzero FEM field retention. DOM geometry/file delivery are synthetic; no fresh native-browser layout,OSchooser,Windows,commercial or hardware execution is claimed.

Complete models, exact source/per-line explanations, actual logs/receipts and qualification limits: docs/TRANSFORMER_DESIGNER.md, sample_results/transformer_designer/ and docs/reports/Task_D001_Transformer_Designer_Report.html. The core/material/bobbin/wire counts in this installed catalogue are 2107 / 1073 / 525 / 4340; searched subset is standard concentric ferrite, no stock check. Component estimates, functional/P2/OVC-II insulation screening, default thermal assumptions and nominal fit do not qualify safety, manufacturing, user-specific cooling or full-transformer envelope. Candidate MAS remains separate from original project/FEM; no automatic overwrite or matched conversion.

NEXT: broaden adviser/input/search constraints and qualify source-bound generated-candidate conversion, measured geometry/electrical equivalence and actual matched FEM. Continue independent source/p/domain/observable accuracy, joined finite winding/return/core, native nonlinear/AC and full CLLC. Full stationary commercial parity, genuine Maxwell/hardware references, redistribution audit and final clean-Windows qualification remain open. No application executable, installer, frozen bundle or packaging-test executable generated. ZIP_LZMA uses documented Python extraction; Explorer compatibility remains unqualified.

Canonical identity remains libfile_1985842cb14c8191837882ec40817011. Baseline resolved version 43, magnetics_studio_v0_9_30.zip, SHA256 a7d13bc9b3bb1fd807e4bfc2e5cf5fa56b9b14e44c6f1993c96ac2321a457720, 54,201,012 bytes, 2658 entries. Always resolve latest metadata and retain guarded writeback. Desktop plan/roadmap resolved at versions 3 / 5, still B001; no unnecessary duplicate or speculative overwrite.

Earlier entries are historical.

# Current checkpoint — v0.9.30 / P002E10, 21 November 2026

A separate source CLI now controls fixed-source native h refinement using every selected signed pickup flux, explicit relative/absolute tolerances and a consecutive accepted-interval streak. Original residual/energy refinement, all preceding numerical kernels and the original browser-builder workflow remain unchanged. Full accepted meshes, fields, source proofs, per-pickup decisions and resource stops are retained. Existing flux measurement accepts the new final-accepted-frame result format.

Actual strict, deliberately loose and DOF-budget runs passed. The 0.1% case reaches four accepted passes without meeting stability; its remote smooth/current-matched difference is -25.5222%. The deliberately loose 20% case meets two stable intervals after three solves, while its remote physical-reference difference remains -27.2594%. These are empirical stopping semantics, not certified accuracy or commercial parity. The actual 16-angle budget case retains its third matched mesh/field and never credits the rejected candidate as an interval.

Verification: 38 independently audited modules; 240 Python cases passed, 17 optional skipped, zero failed/error/unverified. The separate final native-focused profile passed eight methods (three new helpers, three new native methods and two prior native surface-flux regressions). Five pure-Python DC cases and all 105 existing JavaScript checks passed. Actual source CLI output matches the independently executed benchmark native fields, accepted mesh and complete pickup/stability history exactly.

See docs/FLUX_ADAPTIVE.md, sample_results/flux_adaptive/ and docs/reports/Task_P002E10_Flux_Control_Report.html for the complete physical model, actual measurements, code and per-line explanations.

NEXT: independent source/p/domain convergence and defensible accuracy estimates, then actual joined winding/return/core association and native nonlinear/AC. Requirements-driven adviser/design synthesis for Lm and leakage targets remains needed; current Studio is a forward investigation tool. Full CLLC, commercial/hardware validation and final clean-Windows qualification remain open. No application executable, installer or frozen bundle generated.

Earlier entries are historical.

# Current checkpoint — v0.9.29 / P002E9, 20 November 2026

Optional native finite-loop postprocessing and a separate source CLI now measure signed magnetic flux through oriented triangular pickup surfaces. Each surface is clipped against the actual tetrahedra, completely area-checked and integrated from genuine native polynomial fields. Interior mesh-face traces count one physical area. Pickup flux is not automatically winding linkage or transformer magnetising/leakage inductance. No solver/source/material equation or original browser-builder workflow changed.

Seven actual native h/p/source/domain cases demonstrate why quantity-of-interest checks are needed: the finer 16-angle-source / 260 mm-domain case has signed smooth/current-matched flux differences +1.5744% centrally and -7.3215% at a remote pickup. Coarse h/p comparisons remain nonmonotonic. No calibrated error bound or new observable-driven stopping controller is claimed.

Verification: 37 independently audited modules; 237 reference-profile Python cases passed, 14 optional skipped, zero failed/error/unverified. A separate pinned native run passed 8 focused methods (4 helpers, 2 new native methods and 2 prior native regressions). Five pure-Python DC methods and all 105 existing JavaScript checks passed. The actual order-2 CLI export matches independently computed benchmark fields, energy and flux exactly.

Verification results, all exact code/per-line explanations and actual logs are in docs/reports/Task_P002E9_Surface_Flux_Report.html. See docs/LOOP_SURFACE_FLUX.md and sample_results/surface_flux/ for physical assumptions, SI inputs, complete native fields, independent reference quadrature and reproducible commands.

NEXT: flux-based independent source/mesh/p/domain convergence and observable-driven stopping, then real joined winding/return/core association. Native nonlinear/AC, full CLLC, commercial/hardware validation and final clean-Windows qualification remain open. No application executable, installer or frozen bundle generated.

Earlier entries are historical.

# Current checkpoint — v0.9.28 / P002E8, 19 November 2026

The separate source CLI now performs native residual-driven h refinement on a fixed finite-current loop. Netgen handles local bisection and conformity. Every copper child is contained in its original source tetrahedron; parent-by-parent copper volume and the complete original affine RT0 current are preserved. Magnetic-domain volume is checked separately. Optional p enrichment solves the newest accepted mesh that fits the unchanged 45,000 native DOF ceiling, with explicit budget rejections and a correctly matched field/mesh.

The coarse 4-pass sequence grows from 1,848 to 23,516 tetrahedra while its uncalibrated residual ratio falls from 6.513 to 1.536. Energy grows, but point-field errors do not improve consistently. The indicator is not a certified error bound. The separate 16-angle source / 260 mm outer-domain case has 0.485%, 1.898% and 5.603% current-matched smooth-reference field differences, using 43,943 mixed DOFs. Its higher-order solve fits its initial mesh only. Do not attribute that accuracy improvement to h adaptation alone.

Verification: 36 audited modules, 233 Python cases passed and 12 optional skips in the reference profile. The separate native environment passed all 9 focused cases (3 helpers, 4 new native cases and 2 prior native regressions); actual budget-stop CLI, 5 pure-Python DC cases and 105 existing JavaScript checks also passed.

NEXT: quantity-of-interest and independent source/mesh/p/domain convergence, then a real joined winding with explicit return and core. Native nonlinear/AC, full CLLC, commercial/hardware validation and final clean-Windows qualification remain open. No application executable, installer or frozen bundle generated.

Earlier entries are historical.

# Current checkpoint — v0.9.27 / P002E7, 18 November 2026

A separate source CLI now transfers the closed finite annular copper current onto a conforming full magnetic air mesh. Every original copper tetrahedron and its full affine conservative current are retained exactly. The unchanged reference Nedelec kernel solves a boundary-collapsed tree gauge; optional pinned NGSolve solves the same source with a mixed gauge and higher approximation orders. No magnetic mass penalty is added. Actual volume fields, physical energy, source-mode linkage and energy inductance are exported.

Lowest-order native/reference full-volume B differs by less than 1e-10 relative on the saved fixture. Native order 3 has 27,519 mixed DOFs. Its same-source centre/off-axis/distant-probe differences are 0.958%, 0.751% and 7.208%; the matched-current smooth-annulus differences are 3.091%, 3.102% and 13.337%. This is a coarse faceted verification source, not a converged transformer model. Complete/reduced native gradient gauges agree in volume B within 6.41e-15. Inductance is a single fixed DC current-mode energy measure; it is not transformer magnetising/leakage separation.

Verification: 35 audited modules, 230 Python cases passed and 8 optional skips in the reference profile; 2 new native cases passed separately, along with 5 pure-Python DC cases and 105 existing JavaScript checks. Actual native CLI export matched the independently saved native volume fields and energy exactly.

NEXT: improve independent mesh/p/domain convergence on a finer source, then qualify a real joined winding with explicit return and core through a production native geometry/field adapter. Full CLLC, native nonlinear/AC, commercial/hardware validation and final clean-Windows qualification remain open. No application executable, installer or frozen bundle generated.

Earlier entries are historical.

# Current checkpoint — v0.9.26 / P002E6, 18 November 2026

The new source CLI solves a complete finite annular copper loop, closes its coincident excitation cut with shared conservative face currents, and computes free-space magnetic probes by volume Biot–Savart quadrature. The whole physical return half is included. The exact saved scalar fields, RT0 currents, seam topology, magnetic moment and numerical field are retained. This benchmark is separate from the original transformer builder and H(curl) FEM solver.

Four actual meshes from 96 to 24,576 tetrahedra reduce centre vector-field error from 4.93% to 0.08449%. Finest off-axis error is 0.09300%; resistance differs by -0.069765% from the smooth finite-annulus reference. The maximum cell current defect is 1.31e-15 A. Recovered-current centroid error remains 0.9659% and its centroid Joule estimate is 0.0967% above the original scalar value. Conservation, constitutive accuracy and field accuracy are recorded separately.

Verification: 34 audited modules, 222 Python cases passed, 6 optional native cases skipped, 8 new focused cases, 5 pure-Python DC cases and 105 existing JavaScript checks passed.

NEXT: qualify closed finite-current transfer into the H(curl) magnetic domain with independent source/gauge/field/energy and air-boundary checks, then an actual joined winding plus return and core. Round geometry, native nonlinear/AC, full CLLC, commercial/hardware validation and final clean-Windows qualification remain open. No application executable or installer generated.

Earlier entries are historical.

# Current checkpoint — v0.9.25 / P002E5, 17 November 2026

DC source tools now offer an opt-in conservative current reconstruction. One signed current per shared mesh face is projected to satisfy charge balance in every tetrahedron, zero current through insulated walls and the prescribed terminal reaction. A lowest-order Raviart–Thomas field recovers consistent cell values. Both DC solve CLIs accept `--conserve-current`. A separate CLI can add the reconstruction to a detached copy of an existing result.

The exact bar remains accurate, and projected sector centroid-vector error decreases from 11.24% to 0.872% over four meshes. On the saved foil and round meshes the largest reconstructed cell current defect is below 1.14e-14 A. Independently integrated face fluxes also pass normal-continuity, wall and terminal checks. The weighted correction changes the foil and round centroid fields by 8.37% and 10.76%; this is postprocessing with a declared metric. Its constitutive and energy accuracy require further qualification.

Verification: 33 audited modules, 214 Python cases passed, 6 optional cases skipped, and 105 JavaScript checks passed.

NEXT: construct an explicit physical return and qualify conservative current transfer into the magnetic domain with source, gauge, field and energy checks. Improve the round geometry approximation and validate reconstructed-current dissipation independently. Native nonlinear/AC, full CLLC, matched Maxwell benchmarks and final clean-Windows qualification remain pending.

Earlier entries are historical.

# Current checkpoint — v0.9.24 / P002E4, 17 November 2026

The original four-turn round STEP winding now solves within the existing 90,000-tetrahedron and 30,000-node DC budgets using explicit curvature sizing and an optional SciPy/SuperLU path. Both original terminal IDs remain bound. The regular PCG and Netgen curvature defaults remain available. No new browser or magnetic-source route is introduced.

At target h = 2 mm, curvature settings 1.25, 1.5 and 1.7 produced 42,564, 69,048 and 88,120 tetrahedra. Resistance decreased from 17.42868 to 16.82221 mΩ at 5 mV and 58 MS/m. The finest caps were about 5.4% smaller than the corresponding CAD surfaces and volume was 4.59% smaller. The workflow is demonstrated but exact curved-geometry resistance remains unqualified. On an identical coarse mesh, PCG and SuperLU resistance agreed within 1.75e-10 relative. Finer PCG runs reached the iteration cap.

Verification: 32 audited modules, 208 Python cases passed, 6 optional cases skipped, and 105 JavaScript checks passed.

NEXT: reconstruct a locally conservative normal current flux on the tetrahedral faces, preserve it through magnetic transfer, and model an explicit physical return. Improve round geometry approximation independently of algebraic tolerances. Full CLLC magnetic coupling, Maxwell comparison and Windows qualification remain pending.

Earlier entries are historical.

# Current checkpoint — v0.9.23 / P002E3, 16 November 2026

The standalone source CLI `tools/solve_cad_dc.py` checks the original project and joined STEP archive, passes both measured cap IDs through Netgen/OpenCascade to a first-order tetrahedral mesh, and drives a homogeneous DC conductor through the selected cap. It reports mesh, potentials, element current density, signed currents, Joule loss, resistance and CAD-to-mesh volume and cap area differences. The P002E2 bar and sector use the same scalar kernel.

The archived two-turn foil chain was solved on four actual meshes from 1,407 to 26,479 tetrahedra. At 58 MS/m and 5 mV the finest result was 3.70423 mΩ and 6.74904 mW. The resistance span over the four meshes was 0.1144% of the finest value, with nonmonotonic changes. The four-turn round chain exceeded the mesh budget. This development increment is a conductor-only CLI, without a new browser route or magnetic coupling.

Verification: 31 audited modules, 205 Python cases passed, 6 optional cases skipped, and 105 JavaScript checks passed.

NEXT: qualify the round winding with a practical native mesh and add face-conservative current reconstruction plus a physical external return before coupling into the magnetic solver. Independent Maxwell results and Windows qualification remain pending.

Earlier entries are historical.

# Current checkpoint — v0.9.22 / P002E2, 15 November 2026

The standalone source CLI `tools/solve_dc.py` solves one homogeneous finite 3D conductor driven by two equipotential caps. It exports a conforming, tagged tetrahedral mesh, nodal voltage, element current density, terminal current, Joule loss, resistance and mesh quality. Two supported parametric geometries are a rectangular bar and a faceted annular sector. It reuses Studio's tetrahedron geometry and sparse PCG. The main project and magnetic solver entry points are unchanged.

The analytical bar check gave 86.20689655 µΩ, ±58 A and 0.290 W at 5 mV. Across four sector meshes, resistance error fell from 4.017% to 0.0641% and volume-weighted centroid current-density error fell from 17.78% to 2.19%. See `docs/reports/Task_P002E2_DC_Conduction_Report.html` for the equations, exact code, verification and limitations.

Verification: 30 audited modules, 198 Python cases passed, 11 optional cases skipped, 5 focused standard-library cases passed, and 105 JavaScript checks passed.

NEXT: build a conforming native mesh on the actual P002E1 joined winding, match both STEP cap IDs and qualify geometric and DC convergence. Confirm that the current density transferred to the magnetic domain preserves charge balance and includes a physical return. Full finite-copper CLLC, AC, Maxwell benchmarks and clean Windows checks remain pending.

Earlier entries are historical.

# Current checkpoint — v0.9.21 / P002E1, 14 November 2026

The source CLI `tools/bind_cad_chain.py` takes a checked joined CAD ZIP, a separate original 3D project and a stable winding key. It independently reconstructs the region partition and chain/cut plans, checks the STEP digests, and reimports solids to verify expected box occupancy, joined conductor volume, domain bounds, material separation and both geometric caps.

The round fixture binds six core regions and one complete four-turn primary across two source sections. A separate two-turn foil primary also passed native reimport and cap checks. In each case the independent secondary is outside the selected conductor binding. The reference ideal-sheet model gave identical nonzero results before and after binding on 5,616 tetrahedra. The new report covers the verified scope and exact code.

Verification: 29 audited modules, 198 Python cases passed, 6 optional cases skipped, and 105 JavaScript checks passed.

NEXT: construct a conforming tagged mesh and qualify a DC conduction case with analytical resistance, current and power balance before magnetic coupling. Remaining conductors, physical insulation, external returns, independent Maxwell benchmarks and final Windows qualification remain pending.

Earlier entries are historical.

# Current checkpoint — v0.9.20 / P002D4, 13 November 2026

The additional `native_bobbin_assembly: true` option requires the single-turn option and all three limbs wound. It adds a detached full native coil to `coil_geometry.native_bobbin_assembly`. Global windows follow native centre/right/left column order. The complete saved CLLC assembly passed the pinned native section/layer fit API with this mapping. Setting all sections to window zero failed. These nominal geometry checks leave physical clearances, measured CAD and FEM copper and terminals to separate qualification.

Opt-in native_single_turn_orientation applies the overlapping orientation only to local bobbin layers with exactly one physical turn. The three saved CLLC views now pass the PyOpenMagnetics 1.7.35 fit call with this option. The baseline centre fit still returns false. Complete assembly data, six independent windings, fourteen sections, 36 packed rows and 51 turns retain their original geometry and order. The earlier exchange packet exports byte-identically.

Both builders restore the source exactly. A nonzero planar comparison returned identical field arrays and 4.5529154174823174e-5 J on 3330 triangles. The full native assembly passed the nominal fit check with the explicit global mapping. Physical clearance and terminal-field qualification remain open.

Verification: 28 audited modules, 196 Python cases passed, 6 optional cases skipped, and 105 JavaScript checks passed.

NEXT: match physical CAD and field regions for finite copper with returns and terminals. Maxwell comparison and final clean-Windows qualification remain pending.

Earlier entries are historical.

# Current checkpoint — v0.9.19 / P002D3, 12 November 2026

Optional MAS exchange now emits three separate scalar coil/bobbin fit views for the saved rectangular EE CLLC. The original six independent windings, fourteen sections, 36 packed rows, 51 turns and geometry-only assembly packet retain their order, coordinates and ownership. Each local view uses the original limb datum and conservative two-face bounds that reserve the adjacent sleeve. The new option requires explicit SI wall dimensions for all three limbs and rejects windings distributed across limbs.

Native PyOpenMagnetics 1.7.35 read all section IDs, local coordinates and explicit window indices. Native fit accepted the left and right views but returned false for the eight-section centre view. Studio nominal containment passed for that view. Diagnostic orientation changes and single-winding centre subsets also returned false. The centre discrepancy is still open. These are local coil fit checks, separate from native multi-bobbin assembly fit and physical three-dimensional clearances.

Both builders round-trip the saved CLLC recipe exactly. A fresh two-winding foil spatial run before and after exchange returned identical fields and energy on 5,940 tetrahedra. See docs/MAS_EXCHANGE.md and the separate Task P002D3 report for usage and logged evidence.

Verification: 27 audited Python modules, 191 passed and 6 optional native cases skipped. All five focused tests and 105 existing JavaScript checks passed. Real authenticated HTTP export and restore matched the direct project. An out-of-fit request returned HTTP 400 and preserved analysis state.

NEXT: resolve the centre-limb native fit discrepancy and qualify whole-assembly native bobbin mapping. Then associate matched CAD/core/insulation and finite copper/terminal geometry with actual field regions. Nonlinear and AC native qualification, Maxwell benchmarks and clean-Windows packaging remain pending. No application executable, installer or frozen bundle generated.

Earlier checkpoints below are historical.

# Current checkpoint — v0.9.18 / P002D2, 11 November 2026

Optional MAS exchange for a symmetric rectangular E-core now associates middle-limb sections with the processed bobbin's winding window zero. The caller declares axial and radial wall thicknesses in metres. The exporter derives the nominal clear window from the existing matched EE shape, validates each unchanged section envelope, and includes the core shape, distributed gap and material provenance. Both original builders round-trip exactly. Existing geometry-only packets remain compatible, including the six-winding, 51-turn multi-limb CLLC. The new option rejects outer-limb sections rather than assigning them to the middle window.

On the four-turn foil transformer, PyOpenMagnetics 1.7.35 generated the same 19.5 × 49 mm nominal window and accepted the native section and layer fit. A fresh 5,940-tetrahedron reference comparison returned identical vector fields and energy before and after exchange. CLI and authenticated HTTP accepted valid input, rejected invalid fit and preserved analysis state. See docs/MAS_EXCHANGE.md and the separate Task P002D2 report and logs.

Verification: 26 audited Python modules, 186 passed and 6 optional native cases skipped. All five focused tests and 105 JavaScript checks passed. The supplementary planar comparison used a 1.2 mm axial wall and 0.4 mm radial wall. Native fit passed for the 19.6 × 47.6 mm window. Actual field arrays and energy were identical before/after restore on 374 triangles.

NEXT: verify native multi-column or per-limb bobbin windows for the full CLLC assignment, then associate measured CAD and field regions, tagged finite copper and terminal/return geometry. Nonlinear and AC native qualification, external Maxwell benchmarks and clean-Windows packaging remain pending. No application executable, installer or frozen bundle generated.

Earlier checkpoints below are historical.

# Current checkpoint — v0.9.17 / P002D1, 11 November 2026

Opt-in MAS coil geometry now derives native sections, packed radial layers and turn coordinates/lengths from the existing rounded E-core CAD plan. The saved CLLC recipe retains six independent windings, fourteen Studio sections, 36 packed rows and 51 turns. The 2D and 3D builders project the same native geometry. Studio limb ownership and the SI origin transform travel in the exchange envelope. Existing CLI and authenticated HTTP endpoints accept the option. Default functional-only packets are retained.

PyOpenMagnetics 1.7.35 actually read all six winding layer lists and their exact coordinates. The native DC calculation used the projected lengths in a detached QA copy with explicitly declared copper. Changing one turn length changed only its winding's estimate. These checks exercise the reader and resistance model. Full native bobbin/window fit, curved CAD association, connected finite conductors and FEM terminals remain open. No PDE or source model changes.

Verification: 25 audited Python modules, 181 passed and 6 optional native cases skipped. The five focused tests and 105 existing JavaScript checks passed. All 51 reimported STEP turns matched the MAS projection in centre and volume-derived length. The actual 5,940-tetrahedron foil fixture gave identical vector field arrays and 1.605016075554145e-7 J before and after restore. The larger field trial was stopped for runtime and is excluded from verification.

See docs/MAS_EXCHANGE.md, docs/reports/Task_P002D1_MAS_Coil_Geometry_Report.html and sample_results/mas_coil_geometry/ for usage, actual test logs, data and line-level source provenance. Commercial/hardware comparisons and Windows release qualification remain pending. No application executable, installer or frozen bundle generated.

NEXT: associate the existing section limb identities with matched native core and bobbin winding windows, then qualify tagged curved CAD/field geometry and finite solved copper/returns/terminals. Native nonlinear/AC and independent benchmarks remain separate milestones. Resolve canonical metadata before guarded updates.

Earlier checkpoints below are historical.

# Current checkpoint — v0.9.16 / P002C2C2D, 10 November 2026

Source-bound connection inspection now reports complete declared chains,partial/disconnected components,unlinked turns,untouched independent windings,original ordered section transitions and planned free end IDs. Actual packet link order cannot reorder the source traversal. Inspect chain coverage/Save inspection in Analysis,the protected /api/turn-links-plan endpoint and tools/connection_plan.py share the same validator and preserve accepted job/field state. Editing cuts/routes/drafts or source invalidates displayed inspection. Planned metadata explicitly does not prove native topology or a solved network.

Native joined components now carry verified_chain only after the actual transferred solid passes every existing contact/isolation/volume/bounds/face gate and its measured free terminal IDs match the declared chain ends. Actual fixture:four0.8mm round primary turns across p_a/p_b sections around an interleaved independent two-turn secondary;three explicit external routes,six cap contacts,one valid STEP solid,two expected ends. The source interleaving/material/currents are unchanged. A partial subset and two disconnected components covering all turn nodes remain partial. Full saved-source inspection retains51turns/14layers/6windings;no full saved native joined export is claimed.

Final qualification: one intact24-module182-case profile (177passed5optional native FEM/MKF skipped),6focused methods plus the final UTF-8CLI repeat,105originalJSchecks,new chain and previous foil/round/ports/bobbin/turn/field CAD actual DOM/canvas/protectedHTTP/native checks,and independent read-only audit. Actual5616-tetrahedron ideal-sheet3Dfield has energy1.619895737152456e-6J with exact before/after field and winding arrays. This is same-model preservation,not finite current continuity,mesh/domain convergence or external correlation. All executable changes and actual evidence are in Task_P002C2C2D_Section_Chains_Report.html.

Only engine/turn_links.py changes among29preceding engine files;all23preceding Python test modules and every historical report/evidence file remain exact. Existing native process budgets,cuts,profile restrictions and explicit routes are unchanged;no autorouting,manufacturing bend/clearance approval,2Dconnected-copper solver,FEM current/voltage terminals,loadedCLLC,nonlinear3D/AC3D or commercial/hardware/native-browser/Windows qualification. No executable/installer/frozen/test bundle generated. Earlier failed/damaged evidence stays unchanged;its historical cause remains unestablished.

NEXT:native MAS geometric layer/turn consumption and broader matched component mapping;meaningful bend geometry/litz policy and complete bobbin/curved-core/CAD-to-field association;then finite solved copper/returns/FEM terminals and qualified native nonlinear/AC with physical source/mesh/domain/impedance/loss convergence. P002 and the stationary programme remain incomplete. Always resolve current canonical metadata and preserve version guards. No continuous-execution promise.

An initial intentionally paused12-module profile is retained under sample_results/connection_chains/earlier_before_wrap. Sidebar review then added explicit text wrapping to the new inspection output;final qualification requires a fresh full profile for that final source. No hashes repaired or composite result credited.

Earlier checkpoints below remain historical.

# Current checkpoint — v0.9.15 / P002C2C2C, 9 November 2026

Explicit source/cut-bound connection geometry now supports matching bare rectangular foil as well as the existing bare round profiles. Both original widths/heights/profiles/signed currents must match. Native sketch width begins along globalY and height alongZ at the actual X-normal slit cap. Explicit right-angle miter transport adds no destination twist. Both actual native cap contacts must cover the full original face with opposing normals;equal volume/areas alone do not establish orientation. A real seven-point path rotates its destination and rejects on partial contact. The valid three-segmentXZfixture joins two foil turns in one transferred valid solid with two exposed ends,independent area×length/summed volume and unchanged physical/reference split.

Qualified fixture:0.8×1.2mm bare foil,explicit0.3mm turn insulation,9.8mm lead,expected lead volume9.408e-9m³. Native cap areas and normal-dot/penetration are recorded. Rectangular provenance has width,height,area and circumcircle radius;no circular diameter. Conservative path/domain/separation guards use sqrt(w²+h²);round-only geometry remains field-cad/6,foil requests field-cad/7. Source/cut packet1,owners,interleaving and original current/material data are unchanged. Litz,bobbin/sleeve combinations and manufacturing bend/clearance qualification remain unsupported. No full51-turn joined saved design is claimed.

Final qualification: one complete source-bound23-module176-case profile (171passed5optional native FEM/MKF skipped),14focused foil/round methods,105originalJSchecks,new foil and previous round-connection/port/bobbin/turn/field CAD actual DOM/canvas/protectedHTTP/native checks,and a separate read-only audit. Actual nonzero3Dfield arrays/winding results remain exact around planning;HTTP and CLI retain prior accepted field/user output on the tested failures. No new PDE/mesh/finite-conductor solve,commercial/hardware/native-browser/Windows execution. Report Task_P002C2C2C_Foil_Connections_Report.html includes every new/replacement executable line,exact patches/hashes,actual raw logs and limits.

An early smoke used the wrong profile spelling foil instead of the existing canonical rectangular and rejected valid input. Corrected to canonical spelling before qualification;raw diagnostic retained. The native orientation prototype is retained separately as an intentionally rejected partial-contact example. Older rejected regression evidence remains byte-identical;its historical log-mutation cause stays unestablished. All magnetic kernels and earlier reports are preserved. No executable/installer/frozen/test bundle generated.

NEXT: broader explicit section connections,bend geometry,litz policy and native MAS layer/turn consumption;complete bobbin/curved-core/CAD-to-field association;then finite solved copper/returns/FEM terminals and qualified native nonlinear/AC with physical/source/mesh/domain/impedance/loss convergence. FullP002,independent commercial references and final permitted clean-Windows qualification remain pending. Always resolve canonical metadata and use version guards. No continuous-execution promise.

Earlier checkpoints below remain historical.

# Current checkpoint — v0.9.14 / Task P002C2C2B, 8 November 2026

Explicit source/cut-bound bare-round connection packets now join consecutive same-owner turn segments through deliberately supplied SI axis-aligned right-angle routes. Analysis draft/editor/save, protected API and source CLIs share validation. Actual transferred native leads require independent area×length volume, opposing full-cap contacts and isolation from unrelated physical geometry. Fusion must reimport as one valid solid with summed volume/union bounds, exactly two exposed original end faces and no surviving consumed caps. Physical bodies replace selected turn pieces; exact original input/lead STEP is retained separately as reference geometry.

Qualified example: two opened turns joined in an actual four-turn/two-independent-winding axial fixture. Core-intersecting explicit route rejects natively. The full saved source draft preserves51turns/14layers/6independent windings; it is not a full joined native saved winding. Only equal-diameter bare round consecutive same-owner sources with equal signed current are supported. Foil/litz,branches,loops,skipped turns and combined bobbin/sleeves reject. No autorouting,manufacturing bend/clearance approval or silent interleaving/material/source edits.

Final qualification: one intact22-module170-case profile (165passed5optional native FEM/MKF skipped),8focused methods,105original JavaScript checks,new connection and four prior CAD DOM/canvas + actual protected HTTP/native integrations,plus final/independent read-only audits. Complete actual logs,full code/patches/per-line explanations and hashes are in Task_P002C2C2B_Connection_Geometry_Report.html. An initial focused test expected ValueError instead of the isolated worker's documented RuntimeError for an actual rejected core collision; original failure/source retained,assertion corrected,full focused/profile rerun. No production guard was weakened. Native CQ2.7.0/OCP7.8.1.1.post1;no new native browser/OS dialog/Windows/commercial/hardware execution.

All28preceding engine files and21preceding Python test modules,historical reports/evidence and numerical kernels remain byte-identical. No FEM geometry/current path is changed: actual nonzero linear ideal-sheet3Dfields and winding results remain exact around CAD planning/export. Joined STEP does not establish finite solved copper,FEM terminals,voltage sources,impedance/losses,3DAC or loaded CLLC operation. See TURN_LINKS.md.

NEXT: broader explicit source-associated connections,foil/litz/bends and native MAS layer/turn consumption;complete bobbin/curved-core association;then finite solved copper/return/terminal sources and qualified native nonlinear/AC with mesh/domain/impedance/loss refinement. P002 and stationary parity remain incomplete. Final Windows packaging stays deferred;no executable/installer/frozen/test bundle before feature completion. Refresh current canonical metadata and preserve guarded replacement;no continuous execution promise.

A first regression profile failed its post-batch audit after test_source_integrity.py output changed from1681recorded bytes to149observed bytes. The exact original ledger,receipt,damaged log and available batch consoles remain in sample_results/turn_links/failed_attempts/full_first_evidence_changed. No matching open file descriptor was observed in a subsequent /proc scan;this does not establish cause. The rejected profile is excluded without repaired hashes;final qualification requires a fresh complete run.

Earlier checkpoints below remain historical.

# Current checkpoint — v0.9.13 / Task P002C2C2A, 7 November 2026

Delivered explicit slit-turn geometric terminal faces as the next connection prerequisite. engine/turn_ports.py creates empty source-bound drafts with ordered actual turn/source/layer/series/container/independent winding IDs,profile dimensions and signed source current. Only cuts may be edited:1–16 unique existing turn IDs plus finite SI gap_m. Cuts stay at the centre of the top straight side with one conductor-width margin to each rounded corner. Source/anchors are exact immutable snapshot data;2D,stale/raw-edited recipes,null/duplicate/unknown/unsupported fields and ignored cut modes reject before accepted-job replacement.

Actual native CAD subtracts the declared cross-section × gap,retains one valid solid and original outer bounds,and verifies the exact reimported STEP terminal areas,centres and opposite outward normals. Cut centres must become empty; adjacent surviving conductor must stay occupied. Small foil and round cases each open2turns. Saved51turn/14layer/6independent winding design opens actual litz turn_8 and retains73checked parts; its2terminal areas are1.720210473399621e-5m² and normals±X. It remains a litz envelope,not resolved/connected copper. All field/source/material/interleaving data remain original; no new FEM terminal,lead,connection or physical solve is claimed. Main field viewer unchanged; inspect downloaded STEP. Existing bobbin/ordinary/closed-turn routes retain prior contracts; optional combined bobbin+slit requests were not separately qualified this increment.

UI draft/edit/save/download and source tools/turn_ports.py / export_field_cad.py --turn-solids --ports share the protected /api/turn-ports-draft and actual isolated native job path. New field-cad/5 manifest records explicit cuts and measured terminal faces,not persistent BRep face indices. Real HTTP/DOM jobs retain an accepted nonzero field and previous CAD on preflight errors. Actual5940-tetrahedron linear ideal-sheet3Dfield has energy4.352162870716339e-7J and exact before/after field/winding arrays. This is model/state preservation,not finite-copper,mesh/domain,Maxwell or hardware validation.

Actual final qualification:21modules/162cases,157passed5optional native FEM/MKF skipped,21unique attempts in seven3-module invocations/six intentional audited pauses; final and independent read-only audits passed.7focused methods and105original JS checks plus new/prior field/turn/bobbin DOM/canvas + real HTTP/native checks pass. First focused attempt6pass1fail from incorrectly calling ordinary turn_1 litz; corrected to actual turn_8. First UI setup ran before its generated fixture existed. Those exact logs/pre-fix test remain labelled and excluded. All26other prior engine files,20prior Python tests and historical reports/evidence remain byte-identical; seven PDE/material/mesh/sparse kernels unchanged. No dependency or licence changes; CQ2.7/OCP7.8QA does not upgrade older P001 production pins. No browser/OS dialog/Windows/commercial/hardware qualification or executable generated.

NEXT P002C2C2B: explicit lead/inter-turn/section connection geometry and joined topology using the measured end faces. Then native MAS layer/turn geometric consumption,complete bobbin/curved-core and solved CAD/source association; finite copper/return/current terminals and native nonlinear/AC with source/mesh/domain/impedance/loss convergence remain pending. P002 and full stationary programme incomplete. Q002 mitigations delivered; historical truncation cause unestablished. Preserve original core/material/digitiser/gap/container/independent-winding/layer workflows. No executable/installer/frozen/test build before final feature completion; no continuous-execution promise. Refresh metadata and preserve guarded canonical writeback.

A first paused regression profile failed its resume audit after an inductance log changed from1100recorded bytes to999observed bytes. Cause unestablished;original ledger/receipts/damaged log retained and excluded. Final qualification uses a fresh profile,not repaired or composite evidence.

Earlier checkpoints below remain historical.

# Current checkpoint — v0.9.12 / Task P002C2C1, 6 November 2026

Delivered explicit source-bound bobbin ring segments/flanges for exact spatial builder snapshots. engine/bobbin_cad.py validates immutable source/anchor metadata,1–16 explicit typed SI parts, safe unique IDs, same-limb owner geometry within1pm round-off, positive extents and actual finite-domain bounds. tools/bobbin_parts.py and protected /api/bobbin-draft create empty drafts only. Analysis offers draft/edit/save and existing isolated checked-STEP export; CLI --turn-solids --bobbin packet.json shares the same native path. No automatic dimensions, repositioning, electrical connectivity or inferred clearance approval.

Actual native CQ2.7.0/OCP7.8.1.1.post1: four foil turns plus a local sleeve segment and shared flange produce14checked parts. Saved six independent windings/fourteen layers/51turns plus one explicit local c2__w1__layer_1 segment produce74checked parts. Positive-volume core and turn collisions actually reject; valid fixtures have zero Boolean candidates because guaranteed-empty broad-phase tests apply. All new parts have transferred STEP hashes, one valid solid, declared millimetres, measured SI bounds/volume and empty bore. This is limited export geometry, not a complete bobbin or solved dielectric/copper. Previous inferred full-height sleeves remain rejected where overlapping; no winding/material/interleaving is changed.

Actual final qualification: one intact20-module155-case profile,150passed5optional native FEM/MKF skipped;7focused methods;105original JavaScript console checks; new bobbin and prior field/turn CAD DOM/canvas + real protected HTTP/native checks. A real5940-tetrahedron linear ideal-sheet3Dfield has energy4.352162870716339e-7J and identical field/winding arrays before/after part planning; GUI/API preserve an accepted nonzero result during draft/export/preflight rejection. No new field equation, convergence, dielectric/loss, commercial/hardware/native-browser/Windows qualification. PDE kernels and all prior test modules/reports/evidence remain byte-identical. See BOBBIN_PARTS.md and Task_P002C2C1_Explicit_Bobbin_Report.html for exact hashes/code/line explanations and full logs. Failed worker-argument/owner-roundoff attempts and two stale-binding UI attempts stay labelled and excluded from final counts; the UI test now edits only parts in the actual browser-snapshot draft.

NEXT programme P002C2C2: explicit leads/inter-turn/section connections and geometric association, native MAS geometric layer/turn consumption, complete bobbin/curved-core mapping; then finite solved copper/terminals and qualified native nonlinear/AC with mesh/domain/impedance/loss refinement. Preserve six independent windings/fourteen layers and all original workflows. Q002 mitigations are delivered; historical truncation cause stays unestablished, not a replacement for programme development. Full commercial/hardware/Windows and final packaging remain pending. No executable/installer/frozen/test build before final feature completion; no continuous-execution promise. Refresh canonical metadata and retain version guards at every replacement.

The final intact profile uses five four-module invocations with four intentional pauses and unchanged-source audited resumes (20 unique attempts). An earlier supervisor stopped without a completion summary; its entire interrupted profile is retained and excluded, with cause unestablished.

Earlier checkpoints below remain historical.

# Current checkpoint — v0.9.11 / Task Q002, 5 November 2026

Verification uses a parent-owned bounded nonseekable pipe, continuous selector drainage and actual EOF/byte accounting. A retained writer beyond one second after observed direct exit is nonpassing and triggers tested POSIX group cleanup. Completed log/receipt/checkpoint files are flushed/fsynced before hashing or atomic replacement; directory/power-loss durability is not established. Protocol2 adds final whole-profile evidence audits and read-only --audit. No silent legacy resume/upgrade or repaired hashes.

Actual final qualification: one intact19-module/148-case profile,143passed/5optional native checks skipped,19attempts. Final plus independent read-only audits passed. All15focused verifier methods (7new+8existing) and105original JavaScript console checks passed. Actual existing2D/3D and2048-triangle10kHz finite-Dirichlet analytical AC fields ran under the new transport. No new FEA equation or accuracy/parity claim. All26engine files and18prior Python test modules remain unchanged. Of649prior entries,10deliberate executable/version/documentation files change;639remain exact, including all historical reports/results.

A real synthetic descendant truncates inherited seekable stdout under the exact old verifier while it still reports success. New pipe capture blocks this tested class; a separately injected late external mutation fails the final audit while preserving the recorded digest and damaged bytes. This does not establish the historical adaptive/server truncation cause. Old rejected ledgers and the P002C2B composite qualification remain unchanged. Q002 mitigations are delivered; historical cause investigation stays open. Arbitrary hostile/path writes, escaped descendants, external parent death, all native process trees, Windows and power loss remain unqualified. See VERIFICATION_RUNNER.md and Task_Q002_Evidence_Integrity_Report.html.

NEXT programme P002C2C: safe explicit bobbin segments/flanges, leads/inter-turn/section connections, native MAS geometric layer/turn consumption and CAD-to-field association; then finite solved copper/terminals and qualified native nonlinear/AC with mesh/domain/impedance/loss refinement. Preserve all six independent windings/fourteen layers and original core/material/digitiser/gap/container workflow. External commercial/hardware/Windows and final packaging qualification remain pending. No executable/installer/frozen build before feature completion and no continuous-execution promise.

Earlier checkpoints below remain historical.

# Current checkpoint — v0.9.10 / Task P002C2B

Optional Analysis/CLI native CAD now exports actual individual rounded-rectangle turn solids associated with original source windows, independent winding IDs and ordered physical layers. Round/foil profiles are bare geometry; litz is an explicitly labelled bundle envelope. Full-height sleeve inference is a separate explicit option, off by default. Rebuilt-source equality, actual individual packing fit, qualified native STEP reimport/bounds/volume/bore and positive-volume collision guards remain mandatory. No source/PDE/mesh/material solver changed and no finite-copper or connected-winding solve is claimed. The main viewer is unchanged; new solids are in downloaded STEP. Read CLOSED_TURN_CAD.md and Task_P002C2B_Closed_Turn_CAD_Report.html.

The saved six-winding/fourteen-layer design has51turns. Inferred full-height sleeves intersect another winding's bundle envelope and are rejected when requested; winding positions are not changed silently. Explicit bobbin geometry, leads, inter-turn/section transitions, terminals, pitch, native MAS geometry consumption and solved CAD association remain unfinished. Two early native attempts hit240s; a later cached full-height-sleeve attempt revealed actual overlap. Those failures remain in task evidence and are excluded from passing counts. New code caches native measures and skips only guaranteed-empty comparisons; original process budgets remain.

Verification integrity: two complete supervisor ledgers failed later raw-log audits (first adaptive, then server). Cause remains unestablished; preserve original profile/profiles/full_first and full_second plus rejected_profile_reason.json. No recorded hashes are rewritten. Final qualification is an explicit source-identical per-module composite:17valid second-run modules plus an actual independent6-case server rerun. Each selected module has matching source/log/receipt hashes, observed exit0 and an actual unittest completion summary.141unique top-level cases:136passed,5optional native checks skipped. This is not an intact18module full-profile artifact. Track Q002 investigation open.

Actual qualification:141unique top-level cases,136passed and5optional native physics checks skipped using17valid second-run modules plus the independent6-case server rerun, all source/log/receipt/summary checked. No intact full-profile artifact is claimed. Native51turn export has73checked parts; separate4foil-turn/sleeve HTTP/CLI and real3Dfield retention, positive-overlap rejection and final DOM/canvas/native checks pass.105original JS checks and prior CAD UI compatibility pass. Separate report explains350added/replacement executable/declaration/integration lines across10files. All534prior files checked;10planned originals change,524remain exact.

NEXT action: investigate Q002 log integrity before claiming reliable intact full-profile execution. Programme NEXT P002C2C: explicit safe bobbin segments/flanges and winding leads/connections, native MAS geometric layer/turn mapping and curved/solid source association; then finite solved copper/terminals and qualified native nonlinear/AC with mesh/domain/impedance/loss convergence. Preserve original core/material/digitiser/gaps/container/independent-winding/layer workflows and source identity. Full commercial/hardware/Windows validation and final executable remain pending. No executable before final feature completion and no continuous-execution promise.

Earlier checkpoints below remain historical.

# Current checkpoint — v0.9.9 / Task P002C2A

Editable native MAS permeability/B-H point subdocuments now map deliberately into real builder material assignments through Material-step preview, protected API and source CLI. Core-region binding, exact original source/point hashes and explicit edited-data provenance prevent silent loss of design/curve semantics. Both dimensional builders preserve six independent windings/fourteen layers; linear laws keep stored curves dormant, and nonlinear 3D remains rejected. No full MAS material/catalogue record, temperature interpolation, hysteresis/loss data, finite copper or new field kernel is claimed. Read MAS_MATERIAL_POINTS.md and the separate Task_P002C2A_Material_Points_Report.html for actual evidence and every changed executable line.

Actual final evidence:16isolated modules,135top-level cases,130passed and five optional native FEM/OpenMagnetics checks skipped. Seven new material tests passed in the frozen-code profile, including real2D/3D changed-mu fields and reversible nonlinear2D vs independent direct-input solves;105original JS checks and actual new/prior DOM/HTTP/native-CAD integration passed. No new browser/Windows/commercial/hardware, mesh/domain or native NGSolve/MKF qualification. All459prior files compared; only7deliberate prior files changed and452remain byte-identical. Report explains314added/replacement executable/declaration/integration lines in8files.

Next P002C2B: actual coil/layer/turn geometric association, complete bobbin/closed-turn/leads and supported curved core; then finite solved copper/terminals and native nonlinear/AC with mesh/domain/impedance/loss qualification. P002 remains incomplete. Preserve original core/material/digitiser/gap/container/independent-winding/layer workflow. Commercial/hardware/Windows validation and final executable remain pending; no executable before final feature completion. Q001 infrastructure is used for bounded isolated regression; earlier interruption root cause remains open.

Earlier checkpoints below are historical.

# Current checkpoint — v0.9.8 / Task Q001

Added supervised isolated verification profiles, atomic child completion receipts, exact source/environment/log hashes, explicit failure/timeout/cancellation outcomes, exclusive POSIX writer locking and bounded intentional pause/resume. Source: tools/verify_suite.py and verification/unittest_worker.py. See VERIFICATION_RUNNER.md and the separate Task_Q001_Verification_Report.html for equations, actual numerical/QA execution evidence and every new/changed executable line.

This mitigates the incomplete long profiles recorded in P002C1; it does not establish their root cause or qualify a monolithic native process. Failed/cancelled/unknown-interruption profiles cannot silently retry through resume; create a new output and preserve earlier evidence. POSIX writer/process control is qualified only in the recorded Linux scope; hard parent-death orphan cleanup, Windows and every native descendant-tree failure remain unqualified. No physical formulation, mesh, material, AC, winding/circuit or prior engine code changed; application edits are version labels only. All prior reports/results remain exact.

Actual final evidence: 15 isolated modules,128 top-level cases,123 passed and five optional native checks skipped; every module had observed exit0, valid completion receipt and unchanged source/dependency fingerprint. Eight new synthetic protocol methods and105 original JS checks passed; the existing core-builder DOM/HTTP check also reran. Fresh existing 2D/3D field/matrix and changed-gap outputs are preserved separately from unchanged historical artifacts. No new field-accuracy or commercial benchmark claim.

NEXT programme work remains P002C2: native material/coil section/layer/turn mapping and geometric association, full bobbin/closed-turn/leads and supported curved core, then finite solved copper/terminals and native nonlinear/AC with mesh/domain/impedance/loss convergence. Use isolated bounded verification for subsequent increments; keep root-cause investigation and platform/dependency qualification open. Preserve six independent electrical windings/fourteen layers and original builder/digitiser workflow. External Maxwell/hardware, full commercial parity and final Windows executable remain pending. No executable before final feature completion and no continuous execution promise.

Earlier checkpoints below remain historical.

# Current checkpoint — v0.9.7 / Task P002C1

Editable MAS E-shape/gap exchange is now in builder Dimensions/Air gaps, API and CLI. It reconstructs supported symmetric rectangular EE dimensions and distributed cuts from actual native subdocument edits, while retaining material binding, independent windings and layer order. The saved six-winding/fourteen-layer source round-trips its real core regions/sources in both dimensions. See MAS_CORE_GEOMETRY.md and Task_P002C1_Core_Geometry_Report.html for exact source, equations and actual evidence.

This is not a full MAS root/core assembly or native material catalogue resolution. No inferred manufacturing-piece count, saturation/loss data or arbitrary gap redistribution. No PDE/mesh/material/AC kernel or previous engine file changed. A selected separate MVB0.6.12/CadQuery2.7 nominal-shape QA comparison does not upgrade the older production MKF/MVB2.6.1 pins; that deployment conflict remains pending. Saved MVB mating offset and Studio cut lengths remain separate. External commercial/hardware/Windows qualification and final executable remain pending.

Actual completed reference profile: 120 discovered,114 passed,six optional checks skipped. The new native MVB case passed separately, as did final selected real 2D/3D field evidence; mixed longer profiles without completion summaries are retained and excluded. Investigate combined native-profile execution stability before promoting a unified environment. 105 original JS checks and actual new/prior DOM/HTTP tests passed.

NEXT P002C2: complete native coil section/layer/turn and material representation with actual geometric association, complete bobbin and closed-turn/lead solids, supported curved-core mapping; then finite solved copper/terminals, qualified native nonlinear/AC and impedance/loss refinement. Keep all six independent winding/fourteen-layer identities and original core/material/digitiser/gap workflow. No application executable before final feature completion. Resolve latest canonical metadata and retain version guards and prior reports.

Earlier checkpoints below remain historical.

# Current checkpoint — v0.9.6 / Task P002B2

Analysis/CLI checked STEP export now includes actual convex 2D polygon regions, individual-wire facets and the existing faceted annular core, extruded by the declared planar depth. Native rectangular 3D sheets/envelopes remain unchanged. Material priority and explicit air holes are preserved; exported signed current-density metadata distinguishes explicit section turns from implicit winding totals. Read PLANAR_CAD.md and the separate P002B2 report for actual numerical evidence, complete code and per-line explanations.

Actual evidence: final full regression 113 discovered, 108 passed and five optional older native FEM/OpenMagnetics checks skipped; all 13 CAD methods passed in a separate forced-reference profile. 105 original JavaScript checks, real DOM/canvas + HTTP/native exports and actual source CLI passed. Three neutral CAD fixtures and a real 11,100-triangle reference field are preserved under sample_results/planar_cad. No mesh/domain/external accuracy claim. Planar manifests explicitly use field-cad/2 with prisms_m; spatial /1 remains.

The tested extension remains geometric. Planar wire prisms are straight prescribed-current conductors, not closed spatial copper turns or finite-conductor/terminal/eddy-current physics. A faceted annular XY section extruded through depth is not a general 3D toroidal winding model. No PDE, field mesher, material/AC kernel or application executable changed. Keep all original reports/evidence unchanged. External references, full commercial coverage and Windows deployment remain unqualified.

NEXT: P002C supported matched MAS/OpenMagnetics core/material/gap and section/layer/turn geometry, genuine curved cores, complete bobbin/turn solids and CAD-to-field association. Resolve the separate CadQuery 2.7 field-CAD / 2.6.1 older MKF-MVB worker qualification before claiming combined deployment; current single-interpreter version gates do not establish one environment can run both. Then finite solved copper/return/terminals and native nonlinear/AC with mesh/domain/impedance/loss convergence. Preserve six electrical windings/fourteen layers, version guards, every task report and the no-executable-before-final requirement. No continuous execution promise.

Earlier checkpoints below retain their historical task scope and evidence.

# Current checkpoint — v0.9.5 / Task P002B1

Checked field-model STEP export is available in Analysis and tools/export_field_cad.py through a separate cancellable geometry_cad worker. Rectangular material priority, gaps, actual ideal source sheets and optional explicitly labelled decorative envelopes are preserved. The saved six-winding/fourteen-layer 3D fixture exports 36 checked STEP parts; all three distributed gaps measure 0.86 mm. No MVB mating offset is added to this source-model export. Separate CadQuery 2.7.0/OCP 7.8.1.1.post1 qualification does not change older OpenMagnetics 2.6.1 pins. Read FIELD_CAD.md and the P002B1 report.

Actual evidence: 107 tests discovered, 102 passed and five optional older FEM/OpenMagnetics tests skipped. All seven new focused methods passed with MAGNETICS_PURE_PYTHON=1; actual native STEP reimports/cancellation and HTTP field retention did run. 105 original JavaScript checks plus new actual DOM/canvas + HTTP/native UI/export/blob/stale/error integration passed. No native browser/OS save-dialog, Windows or commercial/hardware qualification. Exact code/report covers 459 added/replacement executable/declaration/integration lines across 10 files; 73 prior engine/history files remain byte-identical. Only backend orchestration changed among existing engine files; no PDE/mesh/material/AC kernels changed.

NEXT: P002B2 supported OpenMagnetics/MAS core/material/gap and actual layer/turn geometry mapping, curved geometry, complete bobbin/turn solids and CAD-to-mesh/source equivalence. Then finite solved copper/terminals and native nonlinear/AC. Do not relabel zero-thickness sheets or decorative envelopes as finite solved copper, general curved CAD or manufacturing clearance. All parity/commercial/hardware/Windows/final packaging gates remain pending; no executable before final feature completion. Preserve latest canonical metadata/version guards and all task reports.

# Current checkpoint — v0.9.4 / Task P002A

P002A implements checked native MAS coil/wire and optional operating-point subdocuments plus source-preserving Studio restore through both builders, exposed by source CLI and authenticated HTTP API. Read MAS_EXCHANGE.md and the P002A report. Core/material/gaps/insulation and layer order remain exact Studio recipe data; native MAS geometric core/layers/turns and CAD equivalence remain unfinished. No GUI exchange controls or arbitrary MAS importer. Current-only periodic data is not labelled a complete native operating point: explicit voltage waveforms are required for all windings. Existing runtime kernels and historical reports remain unchanged; no solver parity or new executable.

Actual evidence: 100 tests discovered, 95 passed and five optional native FEM/CAD skipped; all nine focused methods passed with MAGNETICS_PURE_PYTHON=1, plus two targeted wire/default/schema rechecks. 105 existing JavaScript console checks passed; no fresh browser/native/Windows/commercial run. Actual reference two-winding before/after mesh, vector B, energy and full L matrix were identical within each dimension (374 triangles / 4752 tetrahedra); this is source consistency, not accuracy or a loaded CLLC benchmark. Six-winding/fourteen-layer saved workflows rebuilt identically. CLI export/restore and authenticated HTTP passed. Report covers 366 added/replacement executable/declaration lines, including tests, server and QA-only authoring. 72 existing engine/history files are byte-identical. Schema snapshots are QA-only with exact MAS Apache-2.0 / PEAS MIT notices; no catalogue data or binaries bundled.

NEXT: P002B measured core/material/gap coordinate mapping and actual MAS section/layer/turn geometry, bobbin/winding solids, CAD/field dimensional/volume/gap equivalence; preserve six independent windings/fourteen layers. Then finite solved copper/terminals and native nonlinear/AC qualification. Use latest canonical metadata/version guard; preserve all old reports and no-executable-before-final rule. Do not repeat F001 as unfinished or claim continuous execution.

# Current checkpoint — v0.9.3 / Task F001 — source and electrical-port integrity

F001 corrects the two reproduced v0.9.2 audit gaps before P002 integration. Public project validation migrates top-level series_groups into per-winding series_group on a detached copy, preserves source order/geometry/turns/currents and removes only the consumed duplicate representation. Reference/static/native grouping and sweeps use stable electrical keys; equal display names do not connect independent sources. Ambiguous membership, identity collisions and conflicting same-series static/RMS currents are rejected rather than averaged. Named containers stay independent. Existing current-editing UI receives canonical legacy examples through the same HTTP endpoint; component-screening request examples retain their separate schema.

Ordinary/static convergence/current/adaptive/native actions reject declared or assigned AC solids. Server preflight returns an actionable error before replacing a prior completed job/result; dedicated AC remains usable. Actual F001 tests include both reference dimensions, unchanged six-winding/fourteen-layer builder sidecars and HTTP state preservation. Native changes are source-inspected only when pinned packages are absent. Historical saved result JSON is not rewritten: re-solve to get the corrected grouped measurements.

Actual F001 validation: final discovery 91 tests (86 passed, five optional native FEM/CAD skipped), 11 focused forced-standard-library tests passed, 105 original JavaScript console checks passed. The 7020-tetrahedron reference CLLC case now exports two electrical ports; grouped primary L=386.500197778352 microhenry and the separate grouped-current sweep gives 386.500197769643 microhenry (relative difference 2.2534e-11). This is same-model consistency only, with no new mesh/domain/commercial qualification. Real HTTP rejection preserves the prior accepted AC field/job. No new actual browser/Windows or optional native run.

Read docs/reports/Task_F001_Source_Integrity_Report.html for complete changed/new code and every executable-line explanation, source hashes, actual logs and numerical evidence. Full Maxwell/FEMM correlation, native nonlinear/AC, 3D AC, transient circuits, losses/capacitance/thermal and Windows qualification remain pending. No application executable/installer/frozen bundle was generated. P002 matched OpenMagnetics core/material/gap/winding/layer/MAS mapping remains the next programme increment. F001 is a correctness prerequisite, not completion of P002 or solver parity. Preserve the original core/material/digitiser/gaps/circuit/winding/layer workflow and source archive identity. Use current metadata and guarded writeback.

Distribution: ZIP_LZMA complete source archive; extract with python -m zipfile -e magnetics_studio_v0_9_3.zip extracted. All earlier reports/evidence are preserved. Explorer extraction remains unqualified.

Earlier checkpoints below are historical where superseded.

# Current checkpoint — v0.9.2 / Task U001

The material image digitiser has a bounded responsive workspace with a left graph/point table, independent settings/validation sidebar and separate footer. Shared web/digitiser.css and web/digitiser.js also generate Image_BH_Digitiser.html via tools/build_digitiser.py. Empty/loading/calibration/trace/error/validated states, row selection and viewport drop routing were corrected without changing numerical calibration, SI conversions, B-H checks, sessions or solver physics. Actual headless Chromium153/Playwright1.62.1 verified181assertions,20layoutstates/eight sizes, real file pickers/downloads/pointers, material apply and standalone offline behaviour; synthetic drop/101-point layout fixtures are explicitly labelled in the report. 105 prior JS checks and5server checks passed. Internal QA screenshots and browser/development dependencies are not deliverables or runtime dependencies. See the separate U001 full-code/per-line report.

Distribution: the complete v0.9.2 archive uses ZIP_LZMA compression, preserving all source, historical reports and solved examples. Use Python standard-library extraction: python -m zipfile -e magnetics_studio_v0_9_2.zip extracted. Windows Explorer ZIP_LZMA support has not been qualified. The standalone digitiser remains a directly opened offline HTML file. A first transfer was rejected by the final integrity check and the prior working archive restored before retrying this smaller complete package; do not reuse that invalid package/hash.

Next programme task remains P002 matched OpenMagnetics geometry/material/gap/winding/layer/MAS mapping, followed by curved solved copper/terminals and native nonlinear/AC with qualified refinement/impedance/loss convergence. No application executable/installer/frozen build before final feature completion. Resolve latest canonical metadata and preserve guarded writeback and historical reports. Earlier checkpoints below are historical where superseded.

# Current checkpoint — v0.9.1 / Task S001

Inductance sweep display was missing: current sweeps stored flux linkage but only plotted energy; AC studies lacked Ls/Rop postprocessing and a prior native history could hide later study results. S001 adds linkage-based chord curves, labelled finite-interval slopes, actual AC per-port Ls=Im(V/I)/(2pi f), signed/missing-data-aware SVG plots, source/series-group/bias semantics and latest-study precedence. Reference 2D/3D and AC jobs were actually exercised. The current sweep remains the reference backend and says so; this increment does not introduce a native sweep, tangent/nonlinear inductance matrix, general circuit solve or magnetising/leakage separation. Read INDUCTANCE_SWEEPS.md and the S001 report. Historical reports remain unchanged.

Next programme task remains P002 matched OpenMagnetics geometry/material/gap/winding/layer/MAS mapping, then curved solved geometry/finite copper terminals, native nonlinear/AC and verified mesh/impedance/loss convergence. Mesh budgets and uncalibrated native refinement remain as in B001. Source executable/installer/frozen builds stay deferred until the final feature-complete version. Resolve latest canonical metadata and guard writeback; do not assume a version number.

Earlier checkpoints below are historical where superseded.

# Current checkpoint — v0.9 / Task B001

The user requests a testable new source tool for tomorrow with FEMM-level 2D and commercial stationary 3D capabilities as the eventual goal. Full parity has not been achieved. Netgen/NGSolve 6.2.2608 is now integrated for bounded linear 2D/3D magnetostatics, conforming unstructured meshes, recovery-based native local refinement, energy/reciprocity checks and real 3D field exports. Native workers are isolated/cancellable and exposed in Analysis; OpenMagnetics core calculation/CAD is now in the same interface as an explicitly separate screening model. Do not confuse that with completed winding CAD or matched solved geometry. See NATIVE_BACKEND_SETUP.md, CAPABILITY_TARGETS.md and the Task B001 report.

NEXT: complete matched OpenMagnetics core/material/winding/layer/MAS geometry integration; qualify curved solved geometry and finite copper/source terminals; then native 2D nonlinear/AC and adaptive impedance/loss control, axisymmetric/magnet/boundary features and nonlinear/AC 3D. Preserve and extend current tests; retain original reference/nonlinear 2D/AC paths. The new native backend has explicit pilot budgets and a small documented 3D gauge regularisation; do not expand its claims without physical sensitivity/refinement tests. Mesh indicators are uncalibrated; pass/budget limits are not convergence. Full Windows/native browser and commercial-solver evidence remain pending.

No application executable, installer or frozen/test package may be generated until the final feature-complete version, per user instruction. Continue source-form development and numbered full-code/per-line technical reports. Canonical archive identity remains libfile_1985842cb14c8191837882ec40817011; refresh current metadata and preserve version guards before writeback. Historical reports below remain part of the record, but earlier next-task instructions are superseded by this current checkpoint.

# Stationary magnetics continuation checkpoint

Release v0.8: Task 001 (limited linear 2D magnetostatic adaptation) and Task 002 (limited linear 2D AC/eddy-current solver) are implemented and internally verified. External Maxwell and hardware correlation remain pending. Motion, rotation and moving interfaces stay deferred. Static forces, thermal coupling and electrical transients remain in the longer-term scope.

Task 002 model: RMS exp(+jωt), real linear isotropic μ, planar Az, no displacement current, finite Az=0 outer boundary. Each explicit ac_conductor group supplies SI conductivity, signed RMS total current and electrical phase, with one axial E0 gradient. A group can have zero net current and nonzero circulating eddy current. Stranded winding regions remain impressed uniform J and have no solved copper/litz loss. Do not silently enable conductivity from catalogue metadata. A region cannot be both a resolved solid and a stranded source.

The eliminated operator is K+jω(M−Σccᵀ/s); source is f_stranded+ΣcI/s. This is not a Hermitian outer product. Complex GMRES uses Hermitian inner products for Arnoldi, a separate mathematical role. Resolve phasors, independently integrate J and quadratic Joule loss, and check input complex power against P_loss+j2ωW_mean. Physical checks do not establish mesh/geometry accuracy.

Evidence: docs/reports/Task_002_AC_Eddy_Current_Report.html; sample_results/ac/benchmark.json. At 10 kHz the finite square-conductor reference has about 0.16% complex-impedance disagreement at 4608 triangles. This is a deliberately specified finite-Dirichlet analytical model, not the unbounded-wire impedance. High-frequency foil demonstration meshes are under-resolved by skin-depth diagnostics and are not qualified loss predictions. All new RMS/phase/export conventions and prior functionality have regression coverage. Native Windows/browser/file-picker testing and external solver correlation remain pending.

Next Task 003: AC-specific skin-depth/local size refinement using the conforming 2D splitter, followed by a verified AC residual/loss/impedance convergence workflow. Avoid relying on a tiny algebraic residual or power-balance identity as an AC mesh-accuracy bound. Validate mesh quality, net-current constraints and field-port/loss convergence at each frequency. The current AC budget is 8000 nodes/16000 triangles; expose controlled budget stops and do not silently grow it. Current adaptive_solve remains linear magnetostatic-only and must not be applied unchanged to the complex AC operator.

Subsequent tasks: full multiport impedance extraction with defined excitations, return/circuit semantics and source polarity; nonlinear 3D; 3D AC; field/circuit transients; material/core/litz losses; capacitance and thermal interfaces. Preserve the common core/material/digitiser/gaps/circuit-container/independent-electrical-winding/physical-layer workflow. Builder regeneration may replace raw AC region assignments; flag/review them rather than silently retaining invalid references.

Every completed task must add a numbered offline technical report with physical assumptions, equations/units/boundaries, discretisation, complete new/changed runtime/test/benchmark code explained line by line, exact source hashes, reproducible evidence, limitations and next action. Preserve earlier reports and their historical source snapshots. Update docs/reports/INDEX.md and CAPABILITY_REGISTER.json. Do not claim exact Maxwell parity from implemented checkboxes.

Canonical archive identity: libfile_1985842cb14c8191837882ec40817011. Resolve current metadata and use an optimistic version guard before replacing it. Persist tested source/reports/backlog in the archive; do not depend on scratch survival. On 26 October 2026 the user removed the IT-installation constraint and requested a double-click Windows executable with bundled runtime/dependencies. See docs/DESKTOP_OPENMAGNETICS_PLAN.md for the OpenMagnetics reuse decision, separate packaging backlog and Windows qualification gates. No executable or integration has been built yet. Retain the pure-Python reference path; compiled backends may now be evaluated and bundled with correct licences. If new work fails verification, preserve the previous tested release and record the actual blocker.

## Latest steering and Task P001 checkpoint

The user requests reuse of OpenMagnetics and challenges retaining our mesh/refinement code as the production choice. Do not assume it must remain: evaluate mature mesher/FEM packages; current solver is a working reference. See ARCHITECTURE_OWNERSHIP.md. Task P001 provides a real optional CLI core bridge to PyOpenMagnetics 1.7.35 / MVB 0.6.12 / CadQuery 2.6.1: Lm/DC wire calculation and reimported checked E42 core STEP/STL. It translates halfSet to half set and records/measures the additional 5 micrometre mating gap. The bridge is not full transformer design, winding CAD, MAS conversion or external FEM. Five package-free guard/contract tests plus a real native geometry/DC/scaling benchmark are recorded in its report. Preserve six independent windings/fourteen layers in both dimensional sidecars.

Next B001: qualify an external mesh/FEM backend before further committing to custom AC refinement. Next P002: complete matched core/material/winding/layer/operating-point mapping. Original numerical Task 003 remains pending and is subject to backend selection. Synchronised desktop plan and roadmap are embedded in this archive. DO NOT generate any application executable, installer or frozen/test bundle until the final feature-complete version; development/source validation continues. Full Windows/dependency/data-licence audit and Maxwell comparison are pending.
