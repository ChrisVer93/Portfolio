"""Source CLI for the P002A exchange; not a packaged application executable."""
import argparse  #: Define separate explicit export and restore operations.
import json  #: Read caller-supplied source, mapping options and exchange packets.
import pathlib  #: Resolve the application root without changing the caller's directory.
import sys  #: Make the sibling engine package available to this source CLI.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  #: Import only the delivered application's local engine code.
from engine.mas_exchange import export_exchange, restore_exchange  #: Reuse exactly the API's checked exchange implementation.


def main():  #: Parse and run one requested exchange operation.
    parser = argparse.ArgumentParser(description='Checked Studio/MAS coil exchange; not full MAS/CAD integration')  #: Expose the deliberately limited scope in CLI help.
    parser.add_argument('action', choices=['export', 'restore'])  #: Prevent an implicit operation with ambiguous input types.
    parser.add_argument('input', type=pathlib.Path)  #: Accept a source project/recipe or an exchange packet.
    parser.add_argument('output', type=pathlib.Path)  #: Require a caller-chosen destination.
    parser.add_argument('--options', type=pathlib.Path)  #: Export needs explicit bobbin/isolation and optional operating-point declarations.
    parser.add_argument('--mode', choices=['2d', '3d'])  #: Restore may explicitly select the other dimensional builder.
    args = parser.parse_args()  #: Validate command-line vocabulary before reading data.
    data = json.loads(args.input.read_text(encoding='utf-8'))  #: Do not execute or evaluate imported data as Python.
    if args.action == 'export':  #: Require a distinct explicit mapping request.
        if args.options is None or args.mode is not None:  #: Do not silently invent mapping options or change dimension while exporting.
            parser.error('export requires --options and does not accept --mode')  #: Report the incomplete request before writing output.
        options = json.loads(args.options.read_text(encoding='utf-8'))  #: Read actual caller declarations from JSON.
        result = export_exchange(data.get('builder', data), options)  #: Support an existing Studio project as well as a raw builder recipe.
    else:  #: Restore applies the packet's own mapping options and integrity checks.
        if args.options is not None:  #: A second options file could conflict with the retained packet.
            parser.error('restore uses the options in the packet')  #: Refuse silent remapping during restoration.
        result = restore_exchange(data, args.mode)  #: Rebuild through the actual 2D or 3D builder.
    encoded = json.dumps(result, indent=2, allow_nan=False) + '\n'  #: Finish validation and serialization before opening the destination.
    args.output.write_text(encoded, encoding='utf-8')  #: Publish only a fully produced exchange or rebuilt project.


if __name__ == '__main__':  #: Do not run CLI parsing when imported by tooling.
    main()  #: Execute the explicit source command.
