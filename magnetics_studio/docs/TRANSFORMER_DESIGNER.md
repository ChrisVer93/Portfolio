# Transformer design from requirements — D001 / v0.9.31

The separate **Design transformer** button beside Builder generates actual two-winding transformer candidates through PyOpenMagnetics 1.7.35's full adviser. It uses its installed core/material/bobbin/conductor catalogues. Studio then re-simulates each returned component and separately checks its declared targets at every supplied operating point. This is component design and screening, not a new FEM inverse solver or a manufacturing release.

The original Builder, source winding/container/interleaving/material/gap semantics, project, meshes and FEM results remain separate. There is deliberately no automatic candidate-to-Studio-FEM conversion: matched geometry, source, terminals and independent accuracy qualification are still needed. Generated MAS contains native core/material/gap data, actual turn counts, parallel conductors, wires, sections, layers and individual turns.

## What to enter

Use minimum, nominal and maximum values for primary-referred magnetising inductance Lm [H] and turns ratio Np/Ns. Primary-referred leakage [H] has the same explicit band or is null when not constrained. Primary and secondary order is fixed. These are native two-winding component-model inductances, not an arbitrary circuit's entire resonant inductance. State the intended equivalent-circuit/reference convention before relying on leakage for a converter.

Supply 1–4 operating points, each with frequency [Hz], ambient [°C], and **both voltage and current waveforms on both windings**. Each waveform has `time_s` in seconds and signed `values` in volts or amperes. All signals span exactly one common period. Arrays contain 3–1025 paired samples, start at zero, finish at 1/f and use nondecreasing time. Two equal timestamps represent an explicit switching jump. Values between samples are piecewise linear. Signed current phases/dot orientation must be physically consistent; primary current should include magnetising current when applicable. The component adviser does not close a loaded resonant network, calculate converter control, or repair inconsistent input waveforms.

The initial supported frequency range is 1 kHz–1 MHz and ambient range 0–120 °C. Nonzero, balanced winding volt-seconds are required; unsupported DC terminal voltage is rejected. Current DC bias is retained. This does not establish native model validity for every frequency/material/temperature combination inside the input range. Sparse waveform samples may underresolve harmonics and core loss.

Declare maximum estimated |B| [T], total core+winding loss [W], maximum component-model temperature [°C], and **core-only** width/height/depth [m]. The UI displays inductances in µH, frequency in kHz for sine generation, and dimensions in mm, converting once to SI. These limits are checked estimates; the full transformer envelope, construction clearances and specified cooling are not qualified. Max temperature is an output gate, not proof that user-specific cooling has been modeled. The native thermal network's default assumptions apply.

The optional sine generator explicitly creates a sinusoidal approximation from frequency, ambient, primary RMS voltage, primary/secondary RMS currents and their signed phases. Secondary voltage is primary voltage divided by the requested nominal Np/Ns. It is not a CLLC waveform simulation. Alternatively paste or import actual external waveform JSON. All operating points and explicit tolerance bands are saved with every result.

## Native catalogue and models

This tested installation resolved 2,107 shapes, 1,073 materials, 525 bobbins and 4,340 wires. These are complete installed catalogue counts, not the number searched or current vendor stock. The sorted name index SHA256 is `d65fa1cecd230dc5f8f915139a7b0c77c7b7402358d8f1081de059e123fbc279`.

The initial search is deliberately bounded to standard concentric ferrite cores. Toroids, powder cores and stacked cores are excluded; stock checking is off. At most eight magnetics are retained after native filtering, three wire alternatives are allowed, and 1–5 final returned candidates are requested. This bounded pool is not an exhaustive search or global optimum. A no-match result does not prove infeasibility. User loss, temperature and envelope limits are post-generation gates; Studio does not repeatedly widen the native pool until one passes.

Native MAS input declares **Functional insulation, pollution degree P2 and overvoltage category OVC-II** for nominal screening. Reinforced/basic safety insulation, regulatory compliance, insulation system lifetime and manufacturing clearance are unqualified. Do not use this initial workflow as a safety insulation designer. Catalogue and transitive redistribution/data-rights audit remains pending. No whole upstream database or native runtime binary is added to this source archive; selected candidate MAS necessarily includes selected component data. Existing exact licence notices are preserved.

Studio invokes `calculate_advised_magnetics(processed_inputs, max_results, 'standard cores')`, then the actually tested **inputs-first** `simulate(inputs, magnetic, models)`. The pinned `simulate` docstring's argument naming is misleading; reversing these arguments fails in the tested package. Explicit models are `IGSE` core loss and `ZHANG` reluctance; native defaults for winding loss and thermal estimation are retained in the full MAS/settings. These are upstream component calculations rather than resolved FEM fields or a new in-house thermal solver.

## Rechecks and equations

For samples (t_i,y_i), T=1/f:

- mean = sum[(t_(i+1)-t_i)(y_i+y_(i+1))/2] / T;
- RMS² = sum[(t_(i+1)-t_i)(y_i²+y_i*y_(i+1)+y_(i+1)²)/3] / T.

These exactly integrate the declared piecewise-linear signal; zero-duration jumps contribute no interval. Nonzero voltage RMS and |mean(V)| <= max(1e-9 V, 1e-5*peak(V)) are required. Native waveform processing computes its own descriptors/harmonics; source samples and processed inputs are retained for comparison.

The conceptual component relations are Lm ≈ Np²/Rmag [H], ΔB = integral(v dt)/(Np*Ae) [T] under the component voltage/flux assumptions, and primary/secondary leakage referral Llk,p = (Np/Ns)² Llk,s. They do not turn an arbitrary terminal voltage into a resolved local core field. IGSE estimates waveform-dependent material loss; native conductor models estimate DC/skin/proximity loss, and the native thermal network estimates temperature. Leakage uses the native component leakage calculation. This release adds no PDE/discretisation or local-field accuracy claim.

Every candidate must have two positive integer turn counts, every operating-point output, finite physical metrics, and nominal sections/layers passing the native winding-fit API. Actual Np/Ns and core envelope are checked. At every operating point, Studio separately calls the direct reluctance Lm API and checks both it and the re-simulated Lm against the user band. Their difference is reported, not arbitrarily required to be zero. On the illustrative passing case it is approximately 0.04824%, reflecting different native processing paths; this is not an external accuracy bound.

Studio calls leakage with source winding 0 and reads target winding 1, then reverses source/target and requires the referral identity within 1e-5 relative. Largest absolute reported positive/negative/peak B, total core+winding loss and maximum reported temperature are checked at every supplied corner. Missing/nonfinite or incomplete native outputs are candidate model errors, never zeros. All failed checks and per-candidate errors are preserved. Returned candidates are sorted by pass/fail, then worst supplied-corner estimated total loss, then exact generated-data identity. Native adviser scores are retained as provenance, not trusted as proof of all requirements.

## Actual examples and verification

`examples/transformer_design_request.json` is an illustrative 50 W sinusoidal model: primary 50 Vrms, secondary 25 Vrms, 100 kHz, 25 °C, Np/Ns 1.9–2.1, Lm 180–220 µH, primary leakage 0.5–1.5 µH, B <=0.2 T, loss <=10 W and maximum model temperature <=100 °C. Primary current is a 1 Arms load component plus ideal magnetising quadrature for nominal 200 µH; secondary current is -2 Arms. These are declared approximate waveforms, not a solved converter or hardware measurement.

Actual native CLI output returned two passing RM 6-R/material 97 candidates with 28:14 turns. The lowest-loss candidate has direct Lm 193.426981853 µH, primary leakage 0.639741510 µH, peak B 0.133092900 T, estimated total loss 0.947996172 W and model maximum temperature 93.653537 °C. A third RM 6-S/material 95 design is rejected for leakage 2.391018366 µH and temperature 149.478489 °C. This directly demonstrates why native ranking alone is insufficient.

`sample_results/transformer_designer/two_corner_request.json` adds a 150 kHz, 40 °C reduced-amplitude corner. All three returned candidates fail the 100 °C gate: the first reaches 102.912228 °C at the added corner. `changed_targets_request.json` changes Lm to 360–440 µH and Np/Ns to 2.85–3.15 with corresponding illustrative current/voltage samples and no leakage target. The actual adviser generates 60:20 and 65:22 designs with Lm approximately 403–414 µH; all fail the unchanged 100 °C gate. These are honest bounded-search misses, not proof that either problem has no solution. Full requests, generated MAS, settings, every check and actual CLI logs are retained.

Five focused Python methods cover exact waveform integration, detached MAS mapping, malformed physical inputs, actual native CLI generation/re-simulation/gates/output retention, and actual protected HTTP design, cancellation and previous solved-field retention. Real DOM + raster canvas + actual HTTP/native integration covers the visible form, SI conversion, requirements/result/MAS Blob downloads, rejected input/stale labeling, native cancellation, multi-corner no-match and escaping of adversarial names. DOM layout dimensions and file delivery are explicitly synthetic; no native browser layout, OS picker, Windows or security-bypass execution is claimed. Full source regression and raw receipts are recorded separately in the task report.

## Run it

```text
python -m zipfile -e magnetics_studio_v0_9_31.zip extracted
cd extracted/magnetics_studio
python studio.py
# Click Design transformer beside Builder.
python tools/design_transformer.py examples/transformer_design_request.json design_results.json
python tools/design_transformer.py sample_results/transformer_designer/two_corner_request.json two_corner_results.json
python tools/design_transformer.py sample_results/transformer_designer/changed_targets_request.json changed_results.json
python -m unittest tests.test_transformer_designer -v
```

The source environment needs pinned PyOpenMagnetics==1.7.35 for the designer. This dependency is independent of MVB/CadQuery and NGSolve. No installation runs automatically. The compiled adviser runs in the existing isolated, cancellable worker, with the existing 240-second and output budgets. CLI input overwrite is rejected and prior output is retained on preflight/computational failure. Source CLI file writing does not add a new transactional filesystem guarantee. The original server token/origin protection and single-job limit apply. Invalid input does not replace an accepted job; successful component work and cancellation preserve previous FEM exports. Old candidate results remain visibly associated with the previous requirements after edits/failure.

Download complete results to retain source requirements/provenance; download a candidate MAS for its complete neutral component definition. Requirements JSON can be reopened. Native designer JSON is not a normal FEM project and is excluded from its ordinary example list.

No FEM/Maxwell/hardware benchmark, qualified candidate-to-field mapping, full CLLC synthesis, safety/commercial parity or clean-Windows result is established. No application executable, installer, frozen bundle or packaging-test executable is generated. Final Windows qualification remains deferred until feature completion. ZIP_LZMA extraction through Windows Explorer remains unqualified.
