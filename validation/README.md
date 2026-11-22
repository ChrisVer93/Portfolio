# Loss Lab validation

**Status: physical accuracy is NOT established.** The engine is verified against analytic cases (`tests/loss-lab/`) but has
not been compared with measurements or a manufacturer calculator. That comparison needs data that only the tool's owner
has; this folder is the place to put it.

## What counts as validation
1. **Hand calculation / analytic** — covered by the automated tests (I²R, scaling, thermal fixed point, flux scaling,
   harmonic ESR, switching energy, iGSE, power-law interpolation).
2. **Manufacturer calculator** — run the same operating point in the vendor tool (Wolfspeed, Infineon, onsemi, ...) with the
   same curves and compare conduction and switching losses separately.
3. **Measurement** — input–output efficiency (high-accuracy power analyser) or calorimetry at a known operating point.
   Report the measurement uncertainty; a 99 % efficient converter needs about 0.05 % power-measurement accuracy to resolve losses.

## How to add a case
1. Build the case in Loss Lab (same devices, curves, waveforms and settings as the measurement) and **Save project**.
2. Copy `measurements/TEMPLATE.json` to `measurements/<your-case>.json`, paste the project JSON under `project`, and fill in
   `expected.totalLoss_W`, `tolerancePercent` (at least your measurement uncertainty) and `source`.
3. Run `npm run validate`. The table shows tool value, expected value and error; the exit code is 1 when a case is outside
   its tolerance.

`examples/analytic-conduction.json` shows the format (an analytic example, not a measurement).

## Suggested minimum before professional use
* One hard-switched case (MOSFET/IGBT) and one soft-switched (ZVS) case, each within the measurement uncertainty.
* One magnetics case (core + winding) at the operating frequency, with the loss separated by calorimetry or open/short-circuit tests.
* A written "validated for / not validated for" statement (topology, frequency range, device technology, temperature).
