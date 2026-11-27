"""Source-form command-line solve and field report using the isolated native backend."""
import argparse  #: Parse explicit model and mesh controls.
import json  #: Read the original shared project format.
import pathlib  #: Resolve source imports and selected output files.
import sys  #: Use this checkout's engine from tools/.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  #: Preserve source-tree identity for imports.
from engine.backend_process import run_backend  #: Reuse the same isolation/cancellation protocol as the GUI.
from engine.export import write_report  #: Reuse the actual offline 2D/3D field viewer and exports.


def main():  #: Keep CLI execution separate from imports and testing.
    parser = argparse.ArgumentParser(description='Netgen/NGSolve linear 2D/3D magnetostatics')  #: State current physical applicability explicitly.
    parser.add_argument('--project', required=True)  #: Require an actual shared-format model.
    parser.add_argument('--maxh-mm', type=float, default=15)  #: Expose native unstructured mesh size in familiar millimetres.
    parser.add_argument('--passes', type=int, default=1)  #: Bound local refinement through the validated backend controls.
    parser.add_argument('--output', default='native_fields.html')  #: Provide a read-only offline solved-field artifact.
    parser.add_argument('--json', default='native_result.json')  #: Preserve the exact mesh, fields and solve evidence.
    parser.add_argument('--no-matrix', action='store_true')  #: Allow a faster operating-point-only solve.
    parser.add_argument('--hcurl-order',type=int,choices=[0,2,3],default=0)  #: Expose explicitly qualified native spatial order parameters while preserving the original default.
    args = parser.parse_args()  #: Apply the declared source-form CLI contract.
    project = json.loads(pathlib.Path(args.project).read_text(encoding='utf-8-sig'))  #: Preserve the normal model schema and UTF-8 BOM support.
    result = run_backend('ngsolve', {'project': project, 'options': {'maxh_m': args.maxh_mm/1000, 'max_passes': args.passes, 'hcurl_order': args.hcurl_order}, 'matrix': not args.no_matrix}, print)  #: Run the same native physical path exposed by the GUI.
    write_report(result, args.output)  #: Generate a real offline field viewer from solved native data.
    pathlib.Path(args.json).write_text(json.dumps(result, allow_nan=False), encoding='utf-8')  #: Save complete reproducible result JSON.
    print(json.dumps(result['stats'], indent=2))  #: Show actual numerical evidence after successful export.


if __name__ == '__main__':  #: Avoid solving a model merely by importing this module.
    main()  #: Execute the explicit source-form user request.
