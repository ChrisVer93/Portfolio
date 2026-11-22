# Loss Lab changelog

## 2.5.17 — numerical review fixes

### Changed numerical behaviour
- **Frequency-dependent ESR and winding loss use adaptive spectral sampling.** The window used to be resampled to
  `fftSize` (default 1024) points, so ripple above the resulting band limit was folded to low frequency where R is small
  (−93 % error for 100 kHz ripple in a 20 ms window). The resampling size is now chosen from the finest sample spacing of
  the log (up to 2^19 points); `fftSize` is only a lower bound. Dense spectra are merged while preserving current mean square to keep
  evaluation fast. Core-loss excitation-frequency detection uses the same adaptive size (up to 2^17). The engine warns whenever the band limit is capped or the spectrum differs from original waveform mean square by more than 1%. It also flags a discontinuity at the window boundary.
- **Whole-period analysis window.** When enabled, preflight and full project analysis align the window to whole switching periods of the MOSFET gate
  signal, so event energy and averages are no longer biased by a partial period (up to +4.8 % before). A note reports the adjustment. The requested duration is the default. With irregular or conflicting detected gate periods, the tool retains the requested window.
- **Eon/Eoff current timing.** If the current in the log steps sharply (≥ 50 % of the local peak) a few samples after the
  turn-on gate edge, or just before the turn-off edge, the step side is used. The look-around window defaults to 1 % of the
  switching period (at least 4 samples) and can be set per candidate (`eventLookahead`, seconds). A warning remains when the
  step lies farther away. Aligned logs and smooth ZCS/ZVS ramps are unchanged.
- **Power-law (log–log) interpolation.** New project option `curveScale` (`linear` | `power-law`). It applies only to energy,
  loss and ESR curves against current, flux density, frequency or di/dt; temperature, Vgs, Rds, Vf and Vds axes stay linear.
  Energy curves that start at the origin continue as a power law. **Linear remains the default.**
- **iGSE core loss.** New candidate option `coreModel` (`sinusoidal` default | `igse`). iGSE takes local Steinmetz exponents
  from the datasheet curves around the operating flux and frequency (needs curves at ≥ 2 frequencies, or ≥ 2 flux densities for
  loss-vs-frequency curves) and integrates |dB/dt|^α over the actual flux waveform. It reproduces the datasheet value for a
  sinusoid. No DC-bias correction.
- **Reverse recovery.** Err is scaled linearly with blocking voltage / reference voltage (like Eon/Eoff) when the curve has a
  single reference voltage. New candidate options: `recoveryFactor` (multiplies Qrr·V, default 1 = upper bound) and
  `recoveryWindow` (detection window in samples, default 3).

### Added
- `tests/loss-lab/audit-regressions.test.mjs`: 30 analytic regression tests (264 in total). A deliberate factor-2 error in the
  core-flux calculation, which the old suite did not detect, now fails the suite.
- `validation/` folder with a runner (`npm run validate`) and a template for measurement or manufacturer-calculator cases.
  No measurement cases are included: physical accuracy is still not established.
- UI: curve interpolation scale, event current look-around, core loss model, recovery factor and detection window. These were
  checked by the DOM start-up harness only, not in a real browser.

### Known limitations
- Core loss: no DC-bias or minor-loop correction.
- Recovery energy remains a model (Qrr·V × factor, or Err curve); no softness model beyond the curves.
- Event-timing correction cannot fix logs whose current appears much later than the look-around window (a warning is shown).
- Physical accuracy has not been validated against measurements or manufacturer tools.
