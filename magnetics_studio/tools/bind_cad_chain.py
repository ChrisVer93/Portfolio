"""Bind a checked joined CAD bundle to a spatial Studio source."""
import argparse  #: Parse explicit input and output paths.
import json  #: Read the source and write the measurement report.
from pathlib import Path  #: Resolve local files.
import sys  #: Load the sibling engine.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  #: Use this source checkout.

from engine.cad_field_binding import bind_cad_chain  #: Reuse the verified CAD binding implementation.


def main():  #: Run one local CAD binding operation.
    parser = argparse.ArgumentParser(description=__doc__)  #: Describe the limited source operation.
    parser.add_argument('project', type=Path)  #: Require the independently supplied source project.
    parser.add_argument('archive', type=Path)  #: Require the checked joined CAD ZIP.
    parser.add_argument('winding')  #: Select by stable electrical winding key.
    parser.add_argument('output', type=Path)  #: Require an explicit report destination.
    args = parser.parse_args()  #: Validate command syntax before reading data.
    if args.output.resolve() in (args.project.resolve(), args.archive.resolve()):  #: Protect input files.
        parser.error('Output must differ from the project and archive')  #: Refuse destructive output aliasing.
    report = bind_cad_chain(json.loads(args.project.read_text()), args.archive, args.winding)  #: Finish all native checks.
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')  #: Write only verified finite data.


if __name__ == '__main__':  #: Preserve import without running the CLI.
    main()  #: Invoke one explicit command.
