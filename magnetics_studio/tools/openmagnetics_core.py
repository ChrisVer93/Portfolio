"""Explicit optional-backend CLI; no dependency installation or executable build."""
import argparse  #: Parse explicit source-form user requests.
import json  #: Read the versioned native-core request and print its real outputs.
import pathlib  #: Resolve the source root and selected input/output paths.
import sys  #: Make the source package importable from tools/ and expose an exit status.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  #: Import this checkout's engine rather than an unrelated installed package.
from engine.openmagnetics_bridge import create_case, dependency_status  #: Route to the actual pinned optional backend.


def main():  #: Keep CLI execution separate from imports and numerical tests.
    parser = argparse.ArgumentParser(description='OpenMagnetics E-core screening and checked core CAD; not FEM')  #: State the limited physical method at the entry point.
    parser.add_argument('--status', action='store_true')  #: Allow dependency inspection without loading native libraries.
    parser.add_argument('--request', help='Versioned core-screening JSON file')  #: Require a reproducible explicit physical input for calculations.
    parser.add_argument('--output', default='openmagnetics_result')  #: Keep generated data separate from read-only source resources.
    args = parser.parse_args()  #: Apply the declared argument contract.
    if args.status:  #: A diagnostic request must not accidentally start a solve.
        print(json.dumps(dependency_status(), indent=2))  #: Print the actual installed/expected optional packages.
        return 0  #: A completed inspection is successful even if optional packages are absent.
    if not args.request:  #: Prevent a guessed default model from being presented as the user's design.
        parser.error('Supply --request, or use --status')  #: Explain the required input before entering native code.
    try:  #: Convert native/schema failures into a clear nonzero CLI outcome.
        request = json.loads(pathlib.Path(args.request).read_text(encoding='utf-8-sig'))  #: Read source-form JSON with optional UTF-8 BOM.
        result = create_case(request, args.output)  #: Delegate calculation, CAD generation and verification to the bridge.
        print(json.dumps({'values': result['values'], 'cad': result['cad'], 'output': str(pathlib.Path(args.output).resolve())}, indent=2))  #: Summarise supported numerical outputs and real CAD verification.
        return 0  #: Report success only after the full checked case is written.
    except (ValueError, RuntimeError, OSError) as error:  #: Handle expected input, dependency and filesystem failures without fabricating fallback results.
        print(str(error), file=sys.stderr)  #: Preserve the actual actionable failure for the user.
        return 1  #: Make failure visible to regression runners and scripts.


if __name__ == '__main__':  #: Avoid executing the CLI when a report/test imports its source.
    sys.exit(main())  #: Return the actual operation status to the shell.
