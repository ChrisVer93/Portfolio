# Feature parity and corrected behaviour
Version 1.0.0 — 9 October 2026

| MATLAB workflow | Web workflow | Status |
|---|---|---|
| Project setup and snapshots | Named study, browser autosave, downloadable/openable versioned project JSON | Implemented; old MATLAB results discarded |
| Device instances and alternatives | MOSFET/diode/capacitor/inductor instance editor and candidate models | Implemented with immutable IDs |
| Extract/import characteristic curves | MAT/JSON import, manual SI editor, image digitiser | Implemented |
| Image calibration, zoom, log axes | Three validated reference points, zoom/scroll, undo, linear/log axes | Implemented; MATLAB zero-start interpolation / extrapolation and forced energy origins |
| Curve iterations and dependencies | Multiple iterations, per-iteration canonical units, optional scaling policy | Implemented |
| Simulation files | CSV/TXT, numeric MAT level-5, JSON columns | Implemented |
| Saved MATLAB tables/snapshots | MATLAB JSON export helper and snapshot migration | Implemented conversion route; helper not executed in MATLAB here |
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
- A browser does not execute desktop MATLAB .m GUI code directly. This is a web
  implementation of its workflow and models, with intentional numerical fixes.
- Browser MAT import supports real primitive level-5 data, including cells,
  structs, characters, numeric types and zlib compression. MATLAB table/MCOS,
  complex, sparse and v7.3 HDF5 require conversion or explicit unsupported handling.
- JSON exporter is included for MATLAB tables and snapshots. Its source was
  inspected, but it could not be tested in MATLAB in this environment.
- Legacy normalised ESR is interpreted according to the supplied digitiser,
  which already multiplies samples by raw Rbase. Samples are then converted
  exactly once to ohms. Other exporters should supply canonical SI curve JSON.
- Curve families use linear 1D, multilinear full grids, and normalised simplex
  interpolation for sparse 2D/3D data. Sparse geometry can differ from MATLAB.
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
  not separate supported classes in the supplied MATLAB workflow or this port.
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
with the user's MATLAB datasets, execution of the exporter in MATLAB, hardware
validation and measured accuracy remain unverified.

MATLAB interpolation policy: linear per-iteration interpolation/extrapolation, first-occurrence duplicate-axis handling, sorted inverse axes, then linear interpolation across Vgs and temperature on rectangular families. Negative extrapolated channel Vds contributions clamp to zero as in the MATLAB source. Strict policy retains monotonic-branch and domain rejection. MATLAB runtime parity has not been executed. The supplied CLLC project produces 44/44 valid rows in this mode; extrapolation warnings remain.

## Workflow and reporting update — 2026-10-13
- Component-specific characteristic choices and quantity-specific axis-unit menus. Empty numeric inputs for new alternatives and digitiser sessions; no candidate cloning. Fresh digitiser on entry, image replacement, target/characteristic change and successful save.
- Origin synthesis remains part of saved analysis data; synthesized points are hidden from digitiser, device and reference-curve plots, with explanatory notes.
- Body-diode digitiser matches MATLAB characteristic axes, Tj/Vgs dependencies, negative-sample acceptance and magnitude storage. The engine retains its documented symmetric reverse gate-on channel approximation; full MATLAB event-mask parity is not claimed.
- Eon/Eoff voltage scaling defaults enabled for newly created/imported curves, preserves explicit import opt-out, and can be changed in the editor or digitiser.
- Eon/Eoff temperature-independent checkbox suppresses Tj mismatch only, retains the reference temperature and records the assumption. Multiple reference temperatures must first be resolved; unrelated dependency warnings remain.
- Waveform batches are parsed and consistency-checked before import; all files must share variables, independent of column order. One shared rename/time/unit confirmation applies to the complete batch. Conversion and validation finish before any file is added.
- Print/PDF renders a dedicated full report. MATLAB report categories are represented by combination efficiency plots, ranking charts, per-operating-point category stacks, per-component stacks, component alternative comparisons and Vin/Pout plus Vout/Pout efficiency maps. Exact points retained; missing map cells not fabricated. Tables repeat headings and maps split into printable column groups. SVGs and data are embedded in the HTML report. Browser visual QA unavailable.

Results presentation: operating points use calculated Vin, Vout and Pout, sorted numerically in that order. Tables, chart labels, debug selectors and CSVs share the same label. Combination comparisons display ascending IDs while the best candidate remains selected by mean efficiency. Original waveform names and IDs remain in full JSON for provenance.

Efficiency maps use a purple-to-yellow, perceptually ordered colour scale over the observed efficiency range, percentage labels and an explicit legend. Dashboard Vout slices share one scale per combination. Missing cells remain grey; repeated exact coordinates are averaged. HTML/print report maps use the same renderer and colours.

## Analysis options — engine 1.1.0
- Reference-first (default) preserves existing/MATLAB interpolation order. Forward-first interpolates a piecewise-linear forward family across dependencies, then inverts the resulting curve. Strict/clamp policies use the common reference X interval; extrapolation policies use the union. Ambiguous or flat combined branches are rejected. Exact dependency slices ignore zero-weight reference slices.
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
- Multidimensional dependency extrapolation now projects grid boundary segments instead of silently clamping. Sparse families use a nearby nondegenerate simplex for linear projection outside the hull. Explicit clamp remains available only as a selected policy; strict error mode still rejects out-of-domain inputs. Invalid negative physical outputs remain rejected, except the existing reported MATLAB channel-voltage zero-floor rule.
- 138 automated tests pass, covering grouped notes, hidden diagnostic ranges, model summary, switching zero rule, scaling choices and grid/sparse projection.

## Early input checks — engine 1.7.0
- Persistent readiness status and Check inputs page group missing inputs by component and alternative, with Open & fix navigation and inline field feedback. Blocking inputs are reviewed before starting a worker; reference notes remain nonblocking.
- Characteristic editors validate live and identify duplicate lookup inputs by iteration and row, with red graph markers. Selected active curves are checked; unused stored curves do not block analysis.
- Capacitors, diodes and inductors no longer require hidden MOSFET gate-resistance settings. MOSFET checks follow the enabled loss categories and selected gate model.
- Selected-window spectral DC, output sign and core volt-second checks catch predictable failures early. Exact waveform-dependent curve queries and thermal convergence remain runtime checks.
- 151 automated tests pass.
