"""Solve a two-terminal DC verification conductor."""
import argparse  #: Parse explicit input and output paths.
import json  #: Read a DC model and write fields and diagnostics.
from pathlib import Path  #: Resolve local files.
import sys  #: Load the sibling engine.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  #: Use this source checkout.

from engine.dc_conduction import solve_dc  #: Use the isolated DC solver.


def main():  #: Run one DC conduction operation.
    parser = argparse.ArgumentParser(description=__doc__)  #: Describe the limited source operation.
    parser.add_argument('model', type=Path)  #: Require explicit SI model input.
    parser.add_argument('output', type=Path)  #: Select the result JSON destination.
    parser.add_argument('--conserve-current', action='store_true')  #: Reconstruct charge-conserving face currents with SciPy.
    args = parser.parse_args()  #: Validate command syntax before solving.
    if args.model.resolve() == args.output.resolve():  #: Protect the input path.
        parser.error('Output must differ from the input model')  #: Refuse in-place overwrite.
    result = solve_dc(json.loads(args.model.read_text(encoding='utf-8')))  #: Read and solve the model.
    if args.conserve_current:  #: Apply only the explicitly selected postprocessing.
        from engine.current_flux import reconstruct_current  #: Load the optional reconstruction.
        result['conservative_current'] = reconstruct_current(result)  #: Add conservative current fields.
    args.output.write_text(json.dumps(result, allow_nan=False) + '\n', encoding='utf-8')  #: Publish finite values only.


if __name__ == '__main__':  #: Permit import without CLI side effects.
    main()  #: Run as a source command.
