"""Source CLI for explicit editable E-shape/gap exchange, not a complete MAS root."""
import argparse  #: Separate geometry export and explicit apply operations.
import json  #: Read actual source designs and native subdocument edits as data.
from pathlib import Path  #: Keep user input/output paths explicit.
import sys  #: Resolve the delivered engine from this source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  #: Avoid accidentally importing another installed Studio package.
from engine.mas_core_geometry import export_core_geometry, apply_core_geometry  #: Share exact API/runtime validation and mapping code.


def main():  #: Complete one bounded exchange operation before opening its output.
    parser = argparse.ArgumentParser(description='Editable symmetric EE MAS shape/gaps; no full assembly or catalogue resolution')  #: State the supported geometry and material limitations.
    parser.add_argument('action', choices=['export', 'apply'])  #: Make destructive interpretation changes explicit in the command vocabulary.
    parser.add_argument('input', type=Path)  #: Accept a source recipe/project or the versioned exchange packet.
    parser.add_argument('output', type=Path)  #: Require the caller to choose where successful results are written.
    parser.add_argument('--mode', choices=['2d', '3d'])  #: Allow an explicit dimensional conversion only when applying native geometry.
    args = parser.parse_args()  #: Refuse unknown switches before reading model data.
    source = json.loads(args.input.read_text(encoding='utf-8'))  #: Treat imported JSON as finite validated model data, never executable Python.
    if args.action == 'export' and args.mode is not None: parser.error('--mode is only for apply')  #: Do not change a model dimension implicitly during export.
    result = export_core_geometry(source.get('builder', source)) if args.action == 'export' else apply_core_geometry(source, args.mode)  #: Run actual shared builder validation and native projection decoding.
    encoded = json.dumps(result, indent=2, allow_nan=False)  #: Complete finite serialization before publishing output.
    args.output.write_text(encoded + '\n', encoding='utf-8')  #: Leave an existing output untouched on validation/build failure.


if __name__ == '__main__':  #: Keep imports free of CLI execution.
    main()  #: Execute only the caller-requested source operation.
