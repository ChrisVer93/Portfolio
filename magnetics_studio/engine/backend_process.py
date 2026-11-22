"""Isolate optional native libraries and make cancellation independent of native calls."""
import importlib.metadata as metadata  #: Inspect optional package availability without loading native libraries.
import json  #: Transfer finite model/result data through explicit files.
import pathlib  #: Resolve only the trusted source worker script.
import subprocess  #: Run CAD/FEM libraries outside the local GUI server process.
import sys  #: Use the same explicitly selected Python environment as the server.
import tempfile  #: Keep each job's data and logs private and disposable.
import time  #: Poll cancellation and enforce a bounded job duration.
from .sparse import Cancelled  #: Preserve the application's existing cancellation outcome.
from .geometry_cad import CAD_PINS  #: Keep the new field-CAD qualification separate from the older OpenMagnetics version pins.

ROOT = pathlib.Path(__file__).resolve().parents[1]  #: Locate the worker inside this exact source checkout.
PINS = {'ngsolve': '6.2.2608', 'netgen-mesher': '6.2.2608', 'PyOpenMagnetics': '1.7.35', 'OpenMagneticsVirtualBuilder': '0.6.12', 'cadquery': '2.6.1'}  #: Report tested versions without implying other combinations are qualified.


def backend_status():  #: Offer lightweight source-environment diagnostics to the GUI.
    versions = {}  #: Preserve independent version checks per dependency.
    for name, expected in PINS.items():  #: Check both FEM and component-design/CAD dependencies.
        try:  #: Optional dependency absence is normal in the reference installation.
            installed = metadata.version(name)  #: Read package metadata only.
        except metadata.PackageNotFoundError:  #: Avoid importing a missing native package.
            installed = None  #: Keep absence explicit in the response.
        versions[name] = {'installed': installed, 'expected': expected, 'supported': installed == expected}  #: Distinguish detection from tested-version availability.
    cad_versions = {name: {'installed': versions[name]['installed'] if name in versions else None, 'expected': expected} for name, expected in CAD_PINS.items()}  #: Preserve the separate geometry adapter's expected versions without changing historical core-CAD qualification.
    for name in cad_versions:  #: Inspect the additional CAD-kernel package without importing its native modules.
        try: cad_versions[name]['installed'] = metadata.version(name)  #: Read actual installed distribution versions for this adapter.
        except metadata.PackageNotFoundError: cad_versions[name]['installed'] = None  #: Missing optional native packages disable only their own action.
    return {'design_transformer': versions['PyOpenMagnetics']['supported'], 'packages': versions, 'geometry_cad_packages': cad_versions, 'geometry_cad': all(row['installed'] == row['expected'] for row in cad_versions.values()), 'ngsolve': all(versions[n]['supported'] for n in ['ngsolve', 'netgen-mesher']), 'openmagnetics': all(versions[n]['supported'] for n in ['PyOpenMagnetics', 'OpenMagneticsVirtualBuilder', 'cadquery'])}  #: Enable component design independently of CAD dependencies while retaining every original backend pin.


def run_backend(action, request, progress=None, cancel=None):  #: Execute only the two explicitly supported optional worker actions.
    if action not in ['ngsolve', 'openmagnetics', 'geometry_cad', 'design_transformer']:  #: Whitelist the isolated transformer designer alongside existing FEM/CAD workers without arbitrary execution.
        raise ValueError('Unknown native backend action')  #: Fail at the parent process boundary.
    status = backend_status()  #: Inspect the selected source Python environment before launching a native job.
    if not status[action]:  #: Never substitute a different backend silently when packages are absent.
        raise ValueError('Optional backend unavailable; see docs/NATIVE_BACKEND_SETUP.md and /api/backends for tested package versions')  #: Provide an actionable source-environment diagnosis.
    with tempfile.TemporaryDirectory(prefix='magnetics_backend_') as temporary:  #: Give each job separate result and log paths.
        directory = pathlib.Path(temporary)  #: Keep all worker paths under the controlled temporary directory.
        source, target, logfile = [directory / n for n in ['request.json', 'result.json', 'worker.log']]  #: Define a fixed private protocol independent of user-supplied filenames.
        source.write_text(json.dumps(request, allow_nan=False), encoding='utf-8')  #: Validate finite JSON before native code sees it.
        with logfile.open('w', encoding='utf-8') as stream:  #: Capture native stdout/stderr without contaminating result JSON.
            command = [sys.executable, '--backend-worker', action, str(source), str(target)] if getattr(sys,'frozen',False) else [sys.executable, '-u', str(ROOT/'tools/backend_worker.py'), action, str(source), str(target)]  #: Use the private executable entry when frozen and retain the exact source interpreter path otherwise.
            process = subprocess.Popen(command, cwd=str(ROOT), stdout=stream, stderr=subprocess.STDOUT)  #: Preserve isolated cancellation, complete logs and argument separation without shell execution.
            started = time.monotonic()  #: Measure timeout independently of the wall clock.
            offset = 0  #: Forward new log data once rather than repeating earlier output.
            try:  #: Guarantee process cleanup even if cancellation or a progress callback fails.
                while process.poll() is None:  #: Native geometry/factorisation may block inside the child, never the GUI process.
                    if cancel and cancel():  #: Reuse the existing GUI cancel event.
                        raise Cancelled('Native backend cancelled')  #: Preserve a real cancelled outcome rather than returning partial fields.
                    if time.monotonic()-started > 240:  #: Bound pilot jobs before unbounded native work consumes the session.
                        raise RuntimeError('Native backend exceeded the 240-second pilot limit; simplify the model')  #: Report timeout as failure, not convergence.
                    if progress:  #: Forward ordinary native diagnostic/progress lines when requested.
                        with logfile.open(encoding='utf-8', errors='replace') as current:  #: Read the child log without loading its native libraries.
                            current.seek(offset); new = current.read(12000); offset = current.tell()  #: Bound each progress read and retain its exact position.
                        for line in new.splitlines():  #: Keep each emitted progress message short and readable.
                            progress(line[:500])  #: Prevent an uncontrolled native diagnostic from flooding the interface.
                    time.sleep(.1)  #: Allow responsive cancellation without a busy polling loop.
                if process.returncode:  #: The worker must finish successfully before any result is accepted.
                    raise RuntimeError(logfile.read_text(encoding='utf-8', errors='replace')[-4000:] or 'Native worker failed')  #: Preserve the actual child failure diagnostic.
                if not target.is_file() or target.stat().st_size > 64000000:  #: Bound accepted result size and reject missing output.
                    raise RuntimeError('Native backend did not produce a bounded result file')  #: Never treat stdout or a missing file as a field solution.
                return json.loads(target.read_text(encoding='utf-8'))  #: Accept only the child's completed JSON result.
            finally:  #: Do not leak native processes when the user cancels or the server handles an error.
                if process.poll() is None:  #: A finished worker needs no termination.
                    process.terminate()  #: Stop running native work through the operating-system process boundary.
                    try:  #: Allow ordinary cleanup before forcing termination.
                        process.wait(timeout=3)  #: Bound shutdown latency.
                    except subprocess.TimeoutExpired:  #: Some native operations cannot handle graceful termination promptly.
                        process.kill(); process.wait()  #: Reap the worker after a forced stop to avoid a zombie process.
