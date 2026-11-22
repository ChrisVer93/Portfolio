"""Source CLI for checked editable material-point exchange, not full MAS import."""
import argparse  #: Make export, explicit apply and dimension selection separate user choices.
import json  #: Treat all imported points and source recipes as data.
from pathlib import Path  #: Resolve explicit input and output files portably.
import sys  #: Import the delivered engine from this source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  #: Avoid using an unrelated installed Studio package.
from engine.mas_material import export_material, apply_material  #: Share the actual builder and material validation with API/UI.


def main():  #: Finish validation and serialization before touching an existing output.
    parser = argparse.ArgumentParser(description='Editable MAS material points; no catalogue/loss/thermal inference')  #: State the narrow supported material semantics.
    parser.add_argument('action', choices=['export','apply']); parser.add_argument('input', type=Path); parser.add_argument('output', type=Path)  #: Require explicit operation and file destinations.
    parser.add_argument('--mode', choices=['2d','3d']); args = parser.parse_args()  #: Support only deliberate dimensional conversion during apply.
    if args.action == 'export' and args.mode is not None: parser.error('--mode is only for apply')  #: Avoid silently changing dimensions during export.
    source = json.loads(args.input.read_text(encoding='utf-8'))  #: Read the entire input before validation or output writing.
    result = export_material(source.get('builder',source)) if args.action=='export' else apply_material(source,args.mode)  #: Run the real shared mapping and builder checks.
    encoded = json.dumps(result, indent=2, allow_nan=False)  #: Reject nonfinite serialization before publishing output.
    args.output.write_text(encoded+'\n', encoding='utf-8')  #: Preserve an existing output if parsing/validation/building fails.


if __name__ == '__main__': main()  #: Execute only the explicitly invoked source CLI.
