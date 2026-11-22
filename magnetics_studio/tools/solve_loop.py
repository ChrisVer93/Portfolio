"""Solve a closed finite copper loop with free-space magnetic probes."""
import argparse  #: Require explicit source model and result paths.
import json  #: Decode SI requests and serialize exact source and field results.
from pathlib import Path  #: Resolve paths and preserve the input file.
import sys  #: Load the engine from this source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  #: Use the delivered sibling engine modules.
from engine.closed_loop import solve_loop  #: Run the closed-current source and magnetic integration.


def main():  #: Execute a single source-form closed-loop solve.
    parser = argparse.ArgumentParser(description=__doc__)  #: Describe the limited free-space operation.
    parser.add_argument('model', type=Path)  #: Read one explicit SI request.
    parser.add_argument('output', type=Path)  #: Select the detached solved JSON output.
    args = parser.parse_args()  #: Reject invalid command syntax before solving.
    if args.model.resolve() == args.output.resolve():  #: Protect the original model from overwrite.
        parser.error('Output must differ from input model')  #: Leave the input bytes unchanged.
    result = solve_loop(json.loads(args.model.read_text(encoding='utf-8')))  #: Run actual scalar, conservative-current and volume-field calculations.
    args.output.write_text(json.dumps(result, allow_nan=False)+'\n', encoding='utf-8')  #: Publish finite values only after all calculations pass.


if __name__ == '__main__':  #: Keep imports free of command side effects.
    main()  #: Run when invoked as a source CLI.
