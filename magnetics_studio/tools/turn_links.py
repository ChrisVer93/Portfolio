"""Write a source/cut-bound empty connection draft; no executable packaging."""
import argparse  #: Require explicit project,cut packet and output paths.
import json  #: Read/write finite declarative data without executing user input.
from pathlib import Path  #: Resolve this source checkout and selected user files.
import sys  #: Prioritize the exact sibling engine over installed packages.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Pin imports to delivered source.
from engine.turn_links import draft_links  #: Share exact API/frontend/native-preflight binding semantics.


def main():  #: Save metadata only; connection routes remain deliberately unspecified.
    parser=argparse.ArgumentParser(description='Create an empty source/cut-bound round/foil connection draft; edit links explicitly')  #: Do not advertise autorouting or a FEM circuit solve.
    parser.add_argument('project',type=Path);parser.add_argument('ports',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()  #: Keep all input/output intent explicit.
    packet=draft_links(json.loads(args.project.read_text(encoding='utf-8')),json.loads(args.ports.read_text(encoding='utf-8')))  #: Validate the actual source and selected cuts before writing any output.
    args.output.write_text(json.dumps(packet,indent=2,allow_nan=False)+'\n',encoding='utf-8')  #: Write only the completed finite empty draft and preserve prior output on validation failure.


if __name__=='__main__':main()  #: Keep importing the source CLI free of file writes.
