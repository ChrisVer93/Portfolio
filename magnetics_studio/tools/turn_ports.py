"""Write a source-bound empty turn-port draft; no native CAD or executable packaging."""
import argparse  #: Require explicit source and output paths.
import json  #: Read/write finite declarative data without executing project input.
from pathlib import Path  #: Resolve this source checkout and user-selected files.
import sys  #: Import the exact sibling engine rather than a global package.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Pin imports to the delivered source tree.
from engine.turn_ports import draft_ports  #: Share the same source binding as API, GUI and native preflight.


def main():  #: Export a deliberately empty dimensional draft for explicit review/editing.
    parser=argparse.ArgumentParser(description='Create an empty source-bound turn-port cuts draft; edit SI dimensions explicitly')  #: Do not advertise automatic turn-port design or a solved insulation model.
    parser.add_argument('project',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()  #: Keep input/output intent explicit.
    packet=draft_ports(json.loads(args.project.read_text(encoding='utf-8')))  #: Validate the real retained builder source before writing any output.
    args.output.write_text(json.dumps(packet,indent=2,allow_nan=False)+'\n',encoding='utf-8')  #: Save only the complete finite draft; no native job or source mutation occurs.


if __name__=='__main__':main()  #: Keep importing this CLI free of file writes.
