# Magnetics Studio 0.9 — source-form test guide

The application executable is deliberately deferred. This source version adds an optional Netgen/NGSolve linear 2D/3D magnetostatic backend and exposes the verified OpenMagnetics core/CAD bridge in Analysis. It retains the previous builder, digitiser, reference solvers, 2D nonlinear B–H and dedicated 2D AC features. Full FEMM/Maxwell/COMSOL/Flux parity is not achieved.

## Start the existing source profile

From the extracted magnetics_studio folder, run `python studio.py` (or the existing START_WINDOWS.bat). Python 3.9+ and a modern browser suffice for the reference profile. The optional native buttons remain disabled unless the exact tested package metadata is detected. No packages are installed or downloaded by the application.

## Optional native development profile

On a permitted development machine, create an isolated Python 3.12 environment and explicitly install:

```sh
python -m venv dev_env
# Activate the environment using the platform's normal activation command.
python -m pip install ngsolve==6.2.2608 PyOpenMagnetics==1.7.35 cadquery==2.6.1
python -m pip install --no-deps OpenMagneticsVirtualBuilder==0.6.12
python studio.py
```

The complete profile was executed on Linux x86_64/Python 3.12.14. Windows native-library loading, package installation, real browser file pickers and final packaging remain unverified. These commands describe a source development environment, not a packaged executable or a way around managed-device controls. The prior MVB legacy dependency note in OPENMAGNETICS_DEV_SETUP.md still applies: only the tested core CAD path is integrated, and full transitive/data-licence audit remains pending. Version locks and actual native module hashes are saved with the numerical evidence.

## What to try

1. Open example `native_transformer_2d`; open Analysis and use **Solve with Netgen / NGSolve**. Inspect mesh, fields, matrix, regions and Studies. The native maximum element size is in mm, independent of the reference mesh subdivisions.
2. Open `native_air_coil_3d`, run the same native button, then inspect **Volume field**, B/H arrows/paths, cutaway and mesh. This is an actual tetrahedral vector field. Sources are ideal closed rectangular current sheets, not finite copper/eddy currents.
3. Open `native_cllc_static_3d`. Its current pilot mesh can stop at the conservative budget before the requested recovery indicator is met. The result displays `budget_limit`; it is not a validated CLLC operating/loss design.
4. In Analysis, use **Calculate and generate core CAD**. The supported E42/N97 example actually runs MKF and MVB, shows a projection of the checked STEP and downloads STEP/STL and model JSON. This separate core-screening model does not replace or automatically match the current FEM geometry; winding/bobbin solids are not generated.
5. Use Cancel during a native job. The native worker is a separate process and must return cancelled without replacing the previous field result.
6. Existing nonlinear 2D and AC actions remain separate. Selecting the native button on a nonlinear/solid-AC project produces an explicit unsupported-physics error rather than a silent linear/static substitute.

### Offline review without native dependencies

Open these files directly in a browser:
- sample_results/native/Native_2D_Transformer_Fields.html
- sample_results/native/Native_3D_Coil_Fields.html
- sample_results/native/Native_3D_CLLC_Fields.html

They contain actual solved mesh/field data and require no new solver run. For prior nonlinear/AC examples see sample_results/nonlinear_2d.html and sample_results/ac/. Offline results are read-only; solving edited geometry requires the relevant source environment.

## Actual numerical controls and limits

- Netgen unstructured triangles/tetrahedra; linear isotropic material law; scalar H1 P1 in 2D, lowest-order HCurl edge elements in 3D.
- Homogeneous Az=0 on the finite 2D exterior; tangential A=0 on the finite 3D exterior. Internal material interfaces remain free.
- Explicit 3D numerical gauge regularisation epsilon/Lmax², epsilon default 1e-8. Artificial energy fraction and field sensitivity are checked; this is not a general nonlinear gauge qualification.
- Maximum 60 regions, 500 disjoint geometry pieces, 30000 3D or 46000 2D elements, 45000 total space DOFs, 1–4 accepted passes, 64 probes, and a 240-second worker limit. Conservative pre-refinement growth checks can stop early.
- Recovery indicators use HDiv recovery in 2D and HCurl recovery of H−T in 3D. They are uncalibrated indicators, not guaranteed physical error bounds. Stopping requires both the indicator and inter-pass energy change; limits remain explicit.
- Refinement follows the chosen operating point. Unit-excitation matrix accuracy and local singular peaks are not established by the operating-point stopping criteria.
- The current native action does not provide nonlinear 3D, AC 3D, force, voltage-driven circuit coupling, litz/core losses, electrostatics or thermal solving. It does not import general STEP geometry into the field model yet.

## Reproduction

```sh
python tools/benchmark_native.py
python -m unittest discover -s tests -v
python -m unittest discover -s tests -p test_native_backend.py -v
python tools/native_solve.py --project examples/native_air_coil_3d.json --maxh-mm 25 --passes 2 --output coil_fields.html --json coil_fields.json
```

The delivered native UI test uses jsdom 26.1.0 and @napi-rs/canvas as test-only Node dependencies. Run `tests/native-ui.test.cjs` with NODE_PATH pointing to those test packages and MAGNETICS_TEST_PYTHON pointing to the qualified Python executable. It starts its own real local server on port 8877, runs actual native jobs and checks DOM/canvas/results/download handlers. It is not a native Windows browser test.
