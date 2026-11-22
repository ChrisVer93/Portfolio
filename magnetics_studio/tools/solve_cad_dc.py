"""Solve DC conduction in a verified joined CAD winding."""
import argparse  #: Read the local source-study arguments.
import json  #: Decode the original project and encode the result.
from pathlib import Path  #: Handle archive, project and destination paths.
import sys  #: Find the engine from the source CLI.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  #: Load the checked-out project.

from engine.cad_dc import mesh_winding_dc  #: Reuse the bound winding solver.


def main():  #: Run a single joined-winding DC case.
    parser = argparse.ArgumentParser(description=__doc__)  #: Describe the standalone task.
    parser.add_argument('project', type=Path)  #: Require the original Studio project.
    parser.add_argument('archive', type=Path)  #: Require the existing joined CAD ZIP.
    parser.add_argument('winding')  #: Select the stable electrical winding ID.
    parser.add_argument('driven')  #: Select the measured terminal ID to drive.
    parser.add_argument('output', type=Path)  #: Write to an explicit JSON result path.
    parser.add_argument('--sigma', type=float, required=True)  #: Set conductivity in S/m.
    parser.add_argument('--voltage', type=float, required=True)  #: Set signed voltage in V.
    parser.add_argument('--maxh', type=float, required=True)  #: Set native mesh size in m.
    parser.add_argument('--curvature-safety', type=float, default=2.)  #: Tune Netgen curvature sizing, retaining the existing default.
    parser.add_argument('--linear-solver', choices=('pcg', 'scipy-direct'), default='pcg')  #: Choose the DC matrix solver explicitly.
    parser.add_argument('--conserve-current', action='store_true')  #: Reconstruct charge-conserving face currents with SciPy.
    args = parser.parse_args()  #: Check command syntax before executing.
    if args.output.resolve() in (args.project.resolve(), args.archive.resolve()):  #: Protect input paths.
        parser.error('Output must differ from both inputs')  #: Reject a destructive destination.
    result = mesh_winding_dc(json.loads(args.project.read_text(encoding='utf-8')), args.archive,
                             args.winding, args.driven, args.sigma, args.voltage, args.maxh,
                             curvature_safety=args.curvature_safety, linear_solver=args.linear_solver)  #: Set both controls.
    if args.conserve_current:  #: Apply only the explicitly selected postprocessing.
        from engine.current_flux import reconstruct_current  #: Load the optional reconstruction.
        result['conservative_current'] = reconstruct_current(result)  #: Add conservative current fields.
    args.output.write_text(json.dumps(result, allow_nan=False)+'\n', encoding='utf-8')  #: Save the verified SI result.


if __name__ == '__main__':  #: Allow import without running the CLI.
    main()  #: Execute one source study.
