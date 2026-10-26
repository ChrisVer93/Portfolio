# Feature parity and corrected behaviour
Version 1.0.0 — 9 October 2026

| Legacy workflow | Web workflow | Status |
|---|---|---|
| Project setup and snapshots | Named study, browser autosave, downloadable/openable versioned project JSON | Implemented; old Legacy results discarded |
| Device instances and alternatives | MOSFET/diode/capacitor/inductor instance editor and candidate models | Implemented with immutable IDs |
| Extract/import characteristic curves | MAT/JSON import, manual SI editor, image digitiser | Implemented |
| Image calibration, zoom, log axes | Three validated reference points, zoom/scroll, undo, linear/log axes | Implemented; Legacy zero-start interpolation / extrapolation and forced energy origins |
| Curve iterations and dependencies | Multiple iterations, per-iteration canonical units, optional scaling policy | Implemented |
| Simulation files | CSV/TXT, numeric MAT level-5, JSON columns | Implemented |
| Saved Legacy tables/snapshots | Legacy JSON export helper and snapshot migration | Implemented conversion route; helper not executed in Legacy here |
| Signal mapping and candidate bank counts | Current/voltage/gate selectors and series/parallel/replication counts | Implemented |
| Operating conditions and phases | All selected real-power pairs summed; optional balanced single-phase ×3 | Implemented |
| MOSFET conduction | Gate-on positive and reverse magnitude channel model | Corrected reverse-current categorisation; asymmetry not separately modelled |
| Body diode conduction | Off-state negative current with Vsd characteristic | Implemented |
| Eon/Eoff switching | Per-event energy with trace and explicit voltage scaling | Implemented; sample/commutation resolution still matters |
| Reverse recovery | Current-to-blocking event with Err or Qrr × V and no zero-plateau duplicates | Implemented approximation; assumptions must be confirmed |
| Capacitor ESR | Constant time I²R or harmonic resistance sum | Implemented |
| Winding copper | Constant time I²R or harmonic AC sum plus DC resistance | Implemented |
| Core loss | Balanced-voltage integration, ΔB/2 and Pv model with full dependency values | Implemented sinusoidal-equivalent approximation |
| Thermal iteration | Damped fixed-point solver; per-device or bank Rth, convergence and temperature checks | Implemented; shared coupled sink not included |
| Candidate precomputation | Unique alternative/point cache and bounded combination assembly | Implemented; max 2,000 combinations / 20,000 combined operating points |
| Best combination | Consistent average-efficiency ranking; no incomplete candidates eligible | Corrected |
| Loss-point debug views | Actual engine queries and per-device event traces | Implemented, sampled query preview |
| Efficiency graphs and maps | Separate voltage traces and exact available map cells | Implemented; unknown cells not filled |
| Reports and data exports | Self-contained HTML/print PDF, CSV, full result JSON | Implemented; no external image-path dependency |

## Important compatibility and modelling limits
- A browser does not execute desktop Legacy .m GUI code directly. This is a web
  implementation of its workflow and models, with intentional numerical fixes.
- Browser MAT import supports real primitive level-5 data, including cells,
  structs, characters, numeric types and zlib compression. Legacy table/MCOS,
  complex, sparse and v7.3 HDF5 require conversion or explicit unsupported handling.
- JSON exporter is included for Legacy tables and snapshots. Its source was
  inspected, but it could not be tested in Legacy in this environment.
- Legacy normalised ESR is interpreted according to the supplied digitiser,
  which already multiplies samples by raw Rbase. Samples are then converted
  exactly once to ohms. Other exporters should supply canonical SI curve JSON.
- Curve families use linear 1D, multilinear full grids, and normalised simplex
  interpolation for sparse 2D/3D data. Sparse geometry can differ from Legacy.
  The first enclosing supported simplex may differ from a Delaunay interpolant;
  this is disclosed in each result's notes. Strict domain rejection is default.
- Single-reference dependencies produce explicit warnings when requested
  conditions differ. They are not silently promoted to validated extrapolation.
- Analytic accuracy is tested; physical accuracy is not demonstrated without
  measured/validated source data. No real commercial devices are invented.
- MOSFET reverse channel model uses forward-curve magnitude symmetry, not a full
  third-quadrant current-sharing model. Hard/soft commutation and waveform
  sampling still require engineering interpretation.
- Core model is sinusoidal equivalent, not iGSE/minor-loop/DC-bias validation.
- FFT estimates depend on recorded bandwidth, resolution and periodic windows.
- Independent scalar thermal models do not solve a shared thermal network.
- Transformer, IGBT, GaN-specific and auxiliary/control/interconnect models are
  not separate supported classes in the supplied Legacy workflow or this port.
- Limits: one million samples per file, 2,000 combinations, 20,000 combined
  operating-point results; browser-memory limits may be reached earlier for
  many long files. No 36 GB dataset capability is claimed.
- All alternatives in an instance must use the same enabled loss categories,
  so intentionally omitted categories cannot create an unfair ranking.

## Verification
109 numerical/import/regression tests passed. Fixtures include real MAT level-5
struct/cell arrays and compressed numeric matrices generated with SciPy. The
synthetic demo runs two combinations across three loads; category/device sums
match the total losses and reported efficiency definition.

Static JS syntax and HTML/asset-reference checks are performed. Browser visual
and interactive QA was unavailable in this managed environment. Exact agreement
with the user's Legacy datasets, execution of the exporter in Legacy, hardware
validation and measured accuracy remain unverified.

Legacy interpolation policy: linear per-iteration interpolation/extrapolation, first-occurrence duplicate-axis handling, sorted inverse axes, then linear interpolation across Vgs and temperature on rectangular families. Negative extrapolated channel Vds contributions clamp to zero as in the Legacy source. Strict policy retains monotonic-branch and domain rejection. Legacy runtime parity has not been executed. The supplied CLLC project produces 44/44 valid rows in this mode; extrapolation warnings remain.

## Workflow and reporting update — 2026-10-13
- Component-specific characteristic choices and quantity-specific axis-unit menus. Empty numeric inputs for new alternatives and digitiser sessions; no candidate cloning. Fresh digitiser on entry, image replacement, target/characteristic change and successful save.
- Origin synthesis remains part of saved analysis data; synthesized points are hidden from digitiser, device and reference-curve plots, with explanatory notes.
- Body-diode digitiser matches Legacy characteristic axes, Tj/Vgs dependencies, negative-sample acceptance and magnitude storage. The engine retains its documented symmetric reverse gate-on channel approximation; full Legacy event-mask parity is not claimed.
- Eon/Eoff voltage scaling defaults enabled for newly created/imported curves, preserves explicit import opt-out, and can be changed in the editor or digitiser.
- Eon/Eoff temperature-independent checkbox suppresses Tj mismatch only, retains the reference temperature and records the assumption. Multiple reference temperatures must first be resolved; unrelated dependency warnings remain.
- Waveform batches are parsed and consistency-checked before import; all files must share variables, independent of column order. One shared rename/time/unit confirmation applies to the complete batch. Conversion and validation finish before any file is added.
- Print/PDF renders a dedicated full report. Legacy report categories are represented by combination efficiency plots, ranking charts, per-operating-point category stacks, per-component stacks, component alternative comparisons and Vin/Pout plus Vout/Pout efficiency maps. Exact points retained; missing map cells not fabricated. Tables repeat headings and maps split into printable column groups. SVGs and data are embedded in the HTML report. Browser visual QA unavailable.

Results presentation: operating points use calculated Vin, Vout and Pout, sorted numerically in that order. Tables, chart labels, debug selectors and CSVs share the same label. Combination comparisons display ascending IDs while the best candidate remains selected by mean efficiency. Original waveform names and IDs remain in full JSON for provenance.

Efficiency maps use a purple-to-yellow, perceptually ordered colour scale over the observed efficiency range, percentage labels and an explicit legend. Dashboard Vout slices share one scale per combination. Missing cells remain grey; repeated exact coordinates are averaged. HTML/print report maps use the same renderer and colours.

## Analysis options — engine 1.1.0
- Reference-first (default) preserves existing/Legacy interpolation order. Forward-first interpolates a piecewise-linear forward family across dependencies, then inverts the resulting curve. Strict/clamp policies use the common reference X interval; extrapolation policies use the union. Ambiguous or flat combined branches are rejected. Exact dependency slices ignore zero-weight reference slices.
- Weighted average uses inverse-distance squared with dependency coordinates normalised to their sampled ranges. It honours exact reference coordinates, is an explicit heuristic and does not claim superior physical accuracy. Domain-policy controls remain separate from method selection.
- Diagnostics retain component, characteristic, requested input and dependency intervals, reference ranges, iteration notes and affected query counts. Errors include the requested characteristic/input/dependencies.
- Sensitivity applies one parameter at a time to a selected combination and component, across all or one operating point. Vgs/Rg use ±percentage, reference temperature uses ±degrees Celsius, parallel count uses ±1 device. Frequency scales time for the whole converter and retains waveform shape. Total mean loss percentage and watt change, efficiency percentage-point change and elasticity are reported. Failed scenarios remain invalid; unrepresented dependencies can give zero response. This is a curve-model response with fixed imported waveforms, not circuit re-simulation or guaranteed savings.
- Report configuration selects combinations, operating points, title, notes and optional efficiency/comparison/loss/component/map/alternative/device/diagnostic/sensitivity sections. Metrics are recomputed for the selected scope. Summary metrics, operating-point results, model settings, warnings and limitations remain mandatory. Sensitivity retains its own clearly labelled analysis scope.
- Waveform/loss trace inspection is now implemented in engine 1.4.0; see the section below. Browser interaction/print-layout QA unavailable.

## MOSFET loss model editor — engine 1.2.0
- Components & curves → Loss models & curves groups channel, body-diode, turn-on, turn-off, recovery and temperature correction. Each displays real curve data, selected model, reference conditions, usage formula and status. Ready is a basic reference/configuration check, not full waveform-domain validation.
- Channel Vds/Id versus Rds/Id and recovery Err versus Qrr can be explicitly selected. Duplicate curves of one family require an explicit choice. Unselected stored curves are identified. Existing projects preserve previous Vds-first / Err-first precedence until a choice is saved. Stale or incompatible active IDs fail explicitly.
- Temperature correction can be disabled explicitly; double Tj correction is flagged and rejected by the engine. Voltage scaling, temperature-independent energy and recovery confirmation controls update the actual model.
- Add and digitise actions filter to the chosen loss group. New curves become the group's active characteristic without silently enabling a disabled loss category. Other component editors remain unchanged.
- Active choices are saved in project JSON. Engine notes record active semiconductor models for traceability in reports. Reference and configuration warnings are derived from the candidate, not illustrative states. Browser interaction/layout QA unavailable.

## All-component loss editors — engine 1.3.0
- All components use Loss models & curves. Diodes expose forward conduction and reverse recovery; capacitors expose ESR loss; inductors expose winding/copper and core loss. MOSFET groups remain unchanged.
- Explicit selections are used by the engine and saved in lossModels. Existing defaults remain constant-resistance first, then frequency resistance, then temperature resistance; core defaults to B/Pv before f/Pv; diode recovery defaults to Err before Qrr. Duplicate models require selection.
- Constant-resistance models show their SI value without fabricated curve plots. Passive reference checks use temperature/frequency as relevant and avoid transistor gate conditions. Normalised ESR imports retain their existing absolute-SI conversion.
- Inductor winding groups expose DC resistance; core groups expose turns, effective area, volume, initial flux, excitation frequency and sinusoidal-equivalent confirmation. Required dimensions and confirmation are checked.
- Add, digitise and edit actions are filtered by component and loss group. Numeric and unit input contracts are unchanged. Browser visual/layout QA unavailable.

## Annotated workflow improvements — engine 1.4.0
- Expandable interpolation help explains reference-first, forward-first, inverse-distance weighting and all four domain policies.
- Digitisation opens as a contextual dialog from a component loss group, with no main-menu entry. Add iteration retains the image, calibration, axes and units while clearing samples and reference dependencies; OK saves pending points and finishes. Clear samples retains calibration. New sessions and alternative targets start empty.
- Edit / inspect removes individual iterations while retaining at least one (remove the characteristic to remove the last).
- Every recorded dependency can be ignored explicitly in Edit / inspect, using a selected measured reference slice. Missing joint reference combinations fail. Disabled dependencies are removed from interpolation coordinates; assumptions appear in calculation notes and model details. Ignoring Vds disables energy voltage scaling. Original measured dependencies remain in the stored curve.
- Import component JSON accepts versioned candidate exports, typed instance JSON and legacy candidate JSON with an explicit type choice. Model settings, dependency assumptions and active choices survive import with remapped IDs. Waveform mappings start empty for the new component. Invalid types, categories, curve samples and stale active IDs fail before mutation.
- Debug results now link a sampled actual engine query to its waveform time, current, voltage and instantaneous conduction / body / constant-resistance power. Selected points are highlighted on the characteristic and time plots. Switching and recovery event energies are separate from instantaneous power; spectral resistance and core models provide no fabricated instantaneous power. Whole-window queries have no unique waveform time. Trace values are per physical device; tables retain bank loss totals.
- 119 automated tests pass. Browser layout, touch interaction, dialog focus/scroll and print visual QA remain unverified.

## Alternative reuse and loss inspection V2 — engine 1.5.0
- Import alternative JSON opens a preview with source alternative, destination and characteristic checkboxes. Reuse selected curves in a new alternative of the current component, append them to the current alternative, or create a new component. New alternatives retain the part name and selected characteristic/reference data, with blank installation settings. Existing alternative settings are preserved. Candidate and typed instance exports are supported; mixed component types and whole-project files are rejected. Legacy curve-library imports of candidate JSON open the same selection dialog.
- Switching queries now record the actual current and blocking-voltage values, their individual source indices/times, and final event energy. Turn-off current still uses the preceding sample; voltage still uses the maximum absolute blocking voltage in the original fixed window. Numerical loss calculations are unchanged. Markers use these engine values instead of the raw waveform value at the gate edge. Signed waveforms remain visible.
- Debug shows only the selected contribution's power (conduction/body/constant resistance) or event energy (turn-on/off/recovery). Switching energy curves do not specify switching pulse duration, so no instantaneous switching power is invented. Full-resolution power integrals and averages are retained independently of plot decimation; event energies and averages remain per physical device.
- Each curve/category independently keeps a bounded, adaptively thinned query list, preserving first/last queries and preventing long channel conduction from starving short body-diode intervals. Query counts and the range cursor expose the sampled points. Up to roughly 800 queries per curve/category are retained; display sampling does not affect loss integration.
- A persistent range cursor updates linked plots without recreating the slider during dragging. Selected points use large magenta markers with white outlines, reference-domain queries blue, outside-domain queries red. Input/output guides and the evaluated interpolation family show how the selected query is obtained before external voltage scaling. Small energy/time-axis ticks use range-dependent precision.
- 126 automated tests pass, including actual inspector HTML rendering. Touch, browser interaction and visual layout remain unverified.

## Startup repair — engine 1.5.1
- Restores the Method & compatibility page function accidentally removed during inspector replacement. Its missing reference prevented every main page from rendering at startup.
- A full app startup regression covers initialisation and all main navigation routes. All module imports and both worker entry points now use the same release query to avoid mixing cached releases.
- The entry loader reports startup errors visibly and offers a reload action without clearing browser-local projects.
- 128 automated tests pass; live browser verification follows deployment.

## Reviewable warnings and assumptions — engine 1.6.0
- Results and reports show short grouped warnings by device/part and characteristic. Numerical ranges and operating-point details are expandable. Full curve diagnostics start collapsed in the app; full JSON retains the original notes and diagnostics. Summary CSV warning cells contain only high-level actionable warnings.
- Expected curve extrapolation, selected interpolation methods, reverse gate-on conduction, voltage scaling, recovery detection/Qrr approximation, temperature independence, ignored dependencies, spectral/core assumptions and thermal convergence are separated from warnings. Active models have a details table/list without internal curve IDs.
- Explicit voltage-scaling opt-out is an assumption, not a fixed-voltage warning. Missing energy-curve scaling flags default to enabled, consistent with imports and the editor.
- Zero-current Eon/Eoff are forced to zero for the Id→energy queries used by the engine, regardless of curve intercept. Negative event current remains mapped to zero. This is the selected current-driven switching model; separate no-load/output-capacitance energy is not added.
- Multidimensional dependency extrapolation now projects grid boundary segments instead of silently clamping. Sparse families use a nearby nondegenerate simplex for linear projection outside the hull. Explicit clamp remains available only as a selected policy; strict error mode still rejects out-of-domain inputs. Invalid negative physical outputs remain rejected, except the existing reported Legacy channel-voltage zero-floor rule.
- 138 automated tests pass, covering grouped notes, hidden diagnostic ranges, model summary, switching zero rule, scaling choices and grid/sparse projection.

## Early input checks — engine 1.7.0
- Persistent readiness status and Check inputs page group missing inputs by component and alternative, with Open & fix navigation and inline field feedback. Blocking inputs are reviewed before starting a worker; reference notes remain nonblocking.
- Characteristic editors validate live and identify duplicate lookup inputs by iteration and row, with red graph markers. Selected active curves are checked; unused stored curves do not block analysis.
- Capacitors, diodes and inductors no longer require hidden MOSFET gate-resistance settings. MOSFET checks follow the enabled loss categories and selected gate model.
- Selected-window spectral DC, output sign and core volt-second checks catch predictable failures early. Exact waveform-dependent curve queries and thermal convergence remain runtime checks.
- 151 automated tests pass.

## Projection review and failure inspection — engine 1.8.0
- Exact engine-query screening runs after setup validation and before full analysis. Negative projected physical magnitudes are grouped by device/alternative/characteristic, with dependency conditions, affected operating-point count and a graph. No universal (0,0) rule is imposed on resistance or temperature curves.
- Edit characteristic or explicitly accept a per-characteristic zero floor. Consent persists in project JSON and is reversible in the characteristic editor. Legacy mode no longer silently floors negative channel-voltage projections. Raw and corrected values remain inspectable; accepted floors are assumptions in reports.
- Screening uses temporary zeros only to discover further issues; provisional thermal conditions are not final results. Screening losses and efficiency are withheld. Full-run runtime guards remain active, including for sensitivity studies.
- Failed device calculations preserve queries, error conditions, signed waveforms and device identity. Failed devices are selectable in debug. Failed queries with no output are marked explicitly. Setup failures before signal acquisition cannot supply waveform traces. Thermal failures retain the last evaluated trace.
- Frequency-dependent capacitor ESR now supports a separate explicit DC equivalent series resistance, adding mean-current squared times this resistance to the harmonic sum. Constant ESR continues to use total RMS current. Significant capacitor mean current requires a mapping/window check or this explicit resistance; no DC resistance is inferred from an AC datasheet value or insulation resistance.
- 158 automated tests pass, including exact negative query screening, opt-in persistence/assumptions, strict-domain and thermal failure traces, and an analytic DC-plus-AC capacitor loss test.

### Screening labels — 1.8.1
- Provisional debug selections are labelled SCREENING, rather than implying all components failed. The review explains temporary zeros and provisional thermal conditions. Live browser QA verified negative-projection review, raw values, debug access and successful explicit-consent rerun.

## V4 workflow improvements — engine 1.9.0
- Forward flat outputs remain valid. Inverse ambiguity names the actual lookup input/output; identical duplicate pairs are review notes and deduplicated for calculation.
- Separate opt-in controls for calculation-only (0,0) zero-current voltage/energy and for negative-output flooring. The origin rule resolves ambiguous zero-current outputs, retains raw samples, is excluded from resistance/temperature curves, and is reported as an assumption. Nonzero ambiguity still needs correction.
- Project import shows a cancellable progress dialog. File reading reports byte progress; worker parsing, hydration and input checks show named indeterminate stages. The current project is replaced only after success. Calculation/screening/sensitivity show prominent cancellable progress dialogs.
- Heatmap coordinates group numerical integration round-off at eight significant digits. Continuous view uses bilinear interpolation only within completely sampled neighbouring grid rectangles, with original sample markers and grey unsupported gaps. No extrapolation or fabricated missing data. Sampled-value tables remain available. Reports use fixed-other-voltage slices and the same grouping.
- 166 automated tests pass, including a real worker import, malformed-file handling, inverse zero-current policy, unchanged samples, independent floor/origin settings, duplicate handling and supported-only heatmap interpolation.

## Independent sensitivity steps — engine 1.10.0
- Every parameter has its own perturbation input. Temperature supports percent of absolute Kelvin or °C; parallel count supports percent or whole-device steps. Too-small count percentages are flagged instead of silently changed.
- Requested and actual changes are displayed and exported; used perturbations remain in result controls after a run. Existing shared-percentage configurations remain compatible. 168 automated tests pass.

### Sensitivity parameter correction — 1.10.1
- Removed waveform frequency; added series device count with independent percent or whole-device steps. Total device count scales proportionally; engine uses per-device voltage division. Waveforms/frequency stay fixed, with ideal sharing assumed. 169 automated tests pass, including series voltage/scaling loss checks.

## Connected engineering results — engine 2.1.0
- Shared operating-point selection persists across results, warning/coverage panels and debug. Heatmap samples and summary rows open the point dashboard. Complete, complete-with-assumptions, incomplete and failed states are distinct; missing loss totals remain unavailable.
- Selected-point power flow uses calculated input = delivered output + included model losses. Mapped input discrepancy is separate and never becomes fabricated component loss. Per-component/category breakdown and temperature views accompany alternative efficiency slice curves, stacked losses and temperatures.
- Characteristic coverage overlays retained engine queries on reference curves and shows out-of-range/reference-condition notes and accepted zero floors. Counts refer to retained display samples, not time-weighted coverage percentages.
- Shared display-sample time cursor spans signed current, voltage, gate (where present) and selected contribution power/event energy, with a common time domain. Original event-source markers remain exact; no switching-pulse power is invented.
- Thermal trial/target/residual/limit history survives convergence and failures. Fixed-temperature models explicitly have no iterative trace.
- Study summary reviews counts, active losses, temperature models and explicit curve assumptions before user-initiated runs. New dashboard, thermal and coverage report sections are selectable.
- Component-specific sensitivity exposes gate settings only for applicable enabled MOSFET models; passive resistance and core-loss characteristic scales and iterative thermal resistance are supported. Zero response distinguishes absent/disabled dependencies from represented no-response conditions. Chosen-step and normalised tornado views, per-category mean watt changes and saved sensitivity settings are available. Scaling characteristics does not redesign a component or re-simulate the circuit.
- 179 automated tests pass, including analytic contribution changes, failure-history retention, saved settings, power reconciliation and actual application rendering after worker results.


## Results explorer (2.1.0)

Results open on whole-range comparisons with independent Vin, Vout and Pout filters and alternative selection. Rankings use equal weighting; incomplete alternatives are visible but cannot receive the best label. Loss charts group fixed Vin/Vout slices, with mean or individual point views. Each group has paired stacked charts for contributions and component instances, sharing totals and watt scales, with W/% controls.

A separate point explorer compares alternatives, inspects only applicable selected-component loss categories (Excluded vs 0 W), and preserves query debugging, characteristic coverage, warnings, thermal traces, power flow and sensitivity. Select a component segment to inspect that bank; component identity is never merged by type. Failed/incomplete totals stay unavailable. No numerical loss model changed in this release.


## Combined breakdown and clearer setup (2.2.0)

Each alternative now has one aligned two-level loss chart. Coloured contributions are grouped within the component bank they belong to; the lower row labels each component's proportional share. Hover or keyboard focus shows watts and share of total immediately. Clicking either row opens the relevant component breakdown. W/% views and fixed-voltage groupings are retained; failed results remain unavailable.

New studies explicitly select forward-family interpolation before inversion. Previously saved explicit methods remain unchanged; older projects without a method retain reference-curve interpolation. Gate configuration displays analog hysteresis thresholds only for analog signals and mapped on/off voltages only for logic signals. User-facing explanations use descriptive reference/legacy terminology while persisted compatibility identifiers and import function names remain stable.

194 automated tests cover numerical models, import, rendering, actual-app navigation and tooltip behaviour. Browser visual checks were unavailable for this release.


## Component scope and integrated help (2.3.0)

Independent component and combination checkboxes apply to whole-range and selected-point loss comparisons. All/clear controls are explicit. Selected loss totals and shares are recomputed from existing results without invoking the calculation worker; converter efficiency and original records are retained. Full-converter views and export/report scopes are labelled separately. Empty selections do not become fabricated zero results.

Persistent Help opens a local setup assistant. Field and page help links, input-issue explanations, search and 18 documentation topics share help-content.js. The printable/offline manual.html is generated from the same articles. Guidance covers waveform preparation, mapping, component models, counts, curves, interpolation, zero-floor decisions, gates, switching/recovery, passives, thermal models, results, debug, sensitivity, troubleshooting, exports and calculation limits. Optional guided tours are not part of this release.

201 automated checks pass, including selected-loss reconciliation, unchanged converter efficiency, no-worker display filtering, empty selections, failed-result treatment, content/search/link consistency and actual-app Help navigation. Browser visual checks were unavailable.

The downloadable source/test ZIP remains explicitly labelled version 2.2.0. This release updates deployed tool and manual assets; the source/test archive was not republished.

Validation scope: 201 local checks; the existing public CI suite retains 194 checks. New local regression tests and the documentation generator were not included in this deployment-only update.


## Detailed component calculation reference (2.4.0)

The Help Centre and manual now share five detailed calculation guides: MOSFET, diode, capacitor, inductor and numerical methods. Twenty native MathML equations, nine deterministic SVG graphs, characteristic-selection tables, units and worked examples explain every supported component loss path. Graphs are explicitly synthetic.

Coverage includes Vds/Id versus Rds/Id channel methods, normalised temperature correction and reverse masks; Eon/Eoff event sampling and optional single-reference voltage scaling; direct Err versus Qrr times blocking voltage, with current-slope units and double-counting cautions; constant versus spectral ESR/winding resistance including DC; balanced voltage integration and ΔB/2 core-density lookup; trapezoidal integration, physical-count scaling, inverse-order interpolation and thermal fixed-point equations.

Worked examples were checked with the numerical engine. All 209 local checks pass. SVG graphs were rendered for layout inspection and MathML structures validated; full browser/manual visual verification was unavailable. The existing public CI baseline remains 194 tests. The source/test ZIP remains labelled 2.2.0 and is not republished.

## 2.5.0 documentation screen guides

20 annotated SVG UI illustrations across all 23 help topics and the offline manual. Three numbered callouts per illustration explain the controls and checks. Illustrations are clearly labelled as examples rather than browser screenshots. 212 local tests pass; hosted CI retains its baseline suite.



## 2.5.2 Study overview contextual help

Every analysis setting and input/output mapping field now opens its own detailed Help Centre topic. Conversion-mode help explains average/RMS reporting and the shared loss engine; window, FFT, interpolation and domain-policy help describes calculation effects and worked examples. Balanced input/output ×3 help explains phase selection, real-power scaling and the separate treatment of physical component losses. The duplicated inline interpolation section is removed. All topics are also in the printable offline manual. 197 automated checks pass; browser visual QA was unavailable.


## 2.5.3 V6 quick help refinement

Help buttons sit beside field labels across Study overview, Waveforms operating conditions and component/thermal settings. Dedicated component count, orientation, gate and thermal quick helpers contain no illustrations; full documentation retains existing figures. Study helper wording follows V6, with engine-verified interpolation examples and an explicit explanation of frequency-dependent spectral resistance calculations. Conversion-mode wording remains consistent with its actual average/RMS reporting role. Existing calculation behaviour is unchanged.


## 2.5.4 · V7 component guidance

Shortens component, series, parallel and orientation help per V7. Uses body diode conduction and reverse recovery terminology. Check inputs and setup-assistant issue help now reuse the compact field helper articles, including V6 study guidance. 203 automated tests pass, including actual application issue-help interactions.

## 2.5.5 · Quick-helper documentation recap

Help Centre Documentation now collects the quick helpers into searchable expandable topics, grouped by study settings, component settings, and workflow/loss models. In-tool Help Centre articles use compact text rendering without visualisations. 204 tests pass.

## UI 2.5.13 · Restore visible pre-analysis checks

History audit:
- `d75ac9c` (1.7.0, 17 October 2026) introduced live characteristic validation and the Check inputs page.
- `d135117` (1.8.0, 17 October 2026) added exact waveform-dependent negative-projection screening before analysis.
- `cabfab5` (2.0.0, 17 October 2026) moved that screening behind a study-summary confirmation. Check inputs still displayed only static checks, so opening it did not reveal interpolated-value problems. The screening engine was retained.
- Duplicate checks historically inspected only the engine's lookup axis. Inverse lookups could therefore miss conflicting stored X-axis samples; 2.2.0 (`c108a23`) made forward-family interpolation the default for new studies, exposing this gap more directly.
- `279e1d5` through `53ef1b8` (26 October 2026, module revision 2.5.12) restored automatic exact screening in Check inputs and validation of both stored and inverse axes. Its cached failed-screen path still prevented Run from opening the existing projection-decision dialog.

This revision restores immediate screening on Run, before the study confirmation. Check inputs and Run both provide the projection-review dialog with edit, explicit per-characteristic zero-floor decisions, and screening-only debug. Saving a decision rechecks the inputs; full analysis remains user initiated. Debug preparation copies screening data instead of changing the retained evidence. The readiness banner distinguishes pending, failed and passed interpolation checks. Input changes invalidate the screening result. Conflicting duplicate samples block analysis; redundant identical pairs remain review notes. Existing interpolation method names and calculation policies remain unchanged.

Validation: 222 automated tests pass, including actual-app routes, worker messages, duplicate blockers, immediate Run screening, negative-value review, explicit consent and recheck, successful confirmation, input invalidation and worker-error retry. Numerical engine version remains 2.5.5; this is UI revision 2.5.13.

## UI 2.5.14 · Show screening errors on the characteristic

The 2.5.13 restoration covered Check inputs, Run and the projection-review dialog, but did not connect exact-query failures to the characteristic's own loss-model status. `lossModelEditor` still derived its Ready status from static checks, and `baseCurvePlot` printed a green point-validation message before a separate projection-only graph. The projection wrapper dates to 1.8.0 (`d135117`); the v2.0.0 confirmation change explains the upfront workflow change, not this incomplete inline status. The previous regression tests checked screening and the dialog but did not verify the same failed characteristic in the component view and edit preview.

A shared characteristic-feedback path now combines static row issues and actual recorded screening queries. Negative projections, their evaluated families and duplicate/negative source-point markers appear on the characteristic's original graph. The affected loss group shows Needs review and a red inline message with the raw value, query input and units. Strict-domain interpolation failures retain their actual input and message without inventing an output coordinate. Accepted zero floors remain visible as assumptions with the raw negative values.

Feedback is scoped to component, alternative and curve. Screening records a fingerprint of calculation-relevant curve inputs; edited drafts discard obsolete projection markers and require a recheck. Explicit editor defaults do not invalidate unchanged data. Pending interpolation is labelled separately from passed reference-point checks. Numerical calculations are unchanged.

Validation: 228 automated tests pass, including the actual component-page rendering with a failed screened curve, same-graph overlays, identity scoping, stale draft handling, strict-domain failures, accepted-floor evidence and exact negative source rows. Live verification follows deployment.

## 2.5.15 · Method A validation and calculation-only origin

Method A retains its numerical order: interpolate the stored forward family at the requested dependencies, then invert the combined family once. Its static precheck previously also required each reference Y axis to be individually invertible. That restriction belongs to Query-First/IDW; a flat or turning source reference can combine with another into a valid monotonic family. Method A now validates stored X-axis conflicts immediately and checks combined-family invertibility at screening conditions. An actually flat/nonmonotonic combined family still fails; Method B/IDW keep their per-reference inverse checks.

The explicit (0,0) boundary option could previously add a duplicate stored X=0 point when an inverse-oriented curve contained a nonzero current at zero voltage. The calculation copy now replaces zero-current and stored-X-zero samples with one origin. Original samples are retained. This applies only when the user explicitly chooses the origin policy; resistance/temperature curves remain excluded. Measured-origin extrapolations may still be negative and require review.

Repeated characteristic query errors are grouped by cause and lookup direction, showing the affected input/dependency ranges and operating-point count instead of repeating one message for every retained query. All module URLs use release 2.5.15 to prevent mixed cached calculation modules.

Reproduction: using the provided NSF040120T2A1 forward reference family at 25 °C, Vgs=15 V, Id=2.3380979 A and linear extrapolation, measured-origin Method A yields Vds=-0.3735717151 V (a physical-value error). Explicit-zero-origin Method A previously raised Duplicate curve-axis values; it now yields Vds=0.1174352392 V. No original reference points are modified. A successful Method A family is no longer blocked merely by an individual reference's flat current segment.

Validation: 232 automated tests pass, including the A/B order distinction, method-specific prechecks, combined-family plateaus and turns, zero-origin insertion with nonzero intercepts, raw-data preservation and grouped query diagnostics.
