"""Reconstruct conservative current from a solved DC conductor result."""
import argparse  #: Read local source result and destination paths.
import json  #: Decode numerical fields and encode reconstructed currents.
from pathlib import Path  #: Resolve both local paths.
import sys  #: Load the sibling engine package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  #: Run against this checkout.

from engine.current_flux import reconstruct_current  #: Use the shared conservative reconstruction.


def main():  #: Execute one saved-result reconstruction.
    parser = argparse.ArgumentParser(description=__doc__)  #: Describe the operation.
    parser.add_argument('result', type=Path)  #: Require a solved DC result.
    parser.add_argument('output', type=Path)  #: Choose a detached output file.
    args = parser.parse_args()  #: Validate arguments before reading the field.
    if args.output.resolve() == args.result.resolve():  #: Protect historical solved data.
        parser.error('Output must differ from the source result')  #: Refuse an in-place result rewrite.
    result = json.loads(args.result.read_text(encoding='utf-8'))  #: Load the source solve.
    result['conservative_current'] = reconstruct_current(result)  #: Add the face and cell fields.
    args.output.write_text(json.dumps(result, allow_nan=False)+'\n', encoding='utf-8')  #: Publish finite data.


if __name__ == '__main__':  #: Allow import without CLI effects.
    main()  #: Run the requested reconstruction.
