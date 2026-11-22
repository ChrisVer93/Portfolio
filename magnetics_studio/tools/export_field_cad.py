"""Source CLI for checked field-region STEP export; no executable packaging."""
import argparse  #: Require explicit input and output paths for this source operation.
import base64  #: Decode only the fixed-name verified archive returned by the worker.
import json  #: Read a real Studio field project.
from pathlib import Path  #: Resolve local imports and explicit user destinations.
import sys  #: Import the sibling engine from this source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  #: Avoid importing a different global Studio engine.
from engine.backend_process import run_backend  #: Use the same isolated native export path and limits as the GUI.


def main():  #: Execute one explicitly requested checked STEP export.
    parser = argparse.ArgumentParser(description='Export planar polygon prisms or spatial boxes/source sheets; optional closed turns; no finite-copper solve')  #: Expose the expanded CAD scope without claiming new field physics.
    parser.add_argument('project', type=Path)  #: Accept a real saved field project rather than a separate geometry approximation.
    parser.add_argument('output', type=Path)  #: Require the destination ZIP path explicitly.
    parser.add_argument('--no-envelopes', action='store_true')  #: Allow omission of decorative winding solids while retaining true source sheets.
    parser.add_argument('--turn-solids',action='store_true')  #: Explicitly request source-associated closed turns/sleeves, not finite-copper solving.
    parser.add_argument('--sleeves',action='store_true')  #: Explicitly request inferred full-height sleeves, which may fail native collision checks.
    parser.add_argument('--bobbin',type=Path)  #: Load an explicit source-bound SI part packet independently of inferred sleeves.
    parser.add_argument('--ports',type=Path)  #: Load an explicit source-bound slit-turn packet independently of bobbin geometry.
    parser.add_argument('--links',type=Path)  #: Load explicit same-owner connection paths independently of the original cut packet.
    args = parser.parse_args()  #: Reject unsupported command-line options before native execution.
    if args.sleeves and not args.turn_solids: parser.error('--sleeves requires --turn-solids')  #: Do not infer sleeves without the deliberate closed-turn geometry operation.
    if args.bobbin and (not args.turn_solids or args.sleeves):parser.error('--bobbin requires --turn-solids and excludes --sleeves')  #: Refuse conflicting or silently ignored explicit geometry options before any output write.
    if args.ports and not args.turn_solids:parser.error('--ports requires --turn-solids')  #: Prevent ignored geometric terminal intent before any output write.
    if args.links and (not args.turn_solids or not args.ports or args.bobbin or args.sleeves):parser.error('--links requires --turn-solids and --ports; bobbin/sleeves are outside the connection pilot')  #: Reject ignored or conflicting connection intent before native execution or output replacement.
    project = json.loads(args.project.read_text(encoding='utf-8'))  #: Do not execute imported project data as code.
    extra={'bobbin_parts':json.loads(args.bobbin.read_text(encoding='utf-8'))} if args.bobbin else {}  #: Parse explicit finite declarative part data before starting native work.
    if args.ports:extra['turn_ports']=json.loads(args.ports.read_text(encoding='utf-8'))  #: Parse declared cuts before the isolated native job and preserve prior output on failure.
    if args.links:extra['turn_links']=json.loads(args.links.read_text(encoding='utf-8'))  #: Parse the deliberately supplied connection packet before launching native work.
    result = run_backend('geometry_cad', {'project': project, 'include_envelopes': not args.no_envelopes,'include_turn_solids':args.turn_solids,'include_bobbin_sleeves':args.sleeves,**extra})  #: Complete the actual requested isolated field/turn CAD export and all reimport checks first.
    args.output.write_bytes(base64.b64decode(result['cad_files']['model_geometry.zip'], validate=True))  #: Publish only the fully produced verified neutral CAD archive.


if __name__ == '__main__':  #: Keep importing this CLI free of command execution.
    main()  #: Run the explicit source command.
