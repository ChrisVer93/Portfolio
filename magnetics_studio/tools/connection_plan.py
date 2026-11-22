"""Inspect source-bound connection coverage; source CLI only,no executable packaging."""
import argparse  #: Require explicit source,cut,route and destination paths.
import json  #: Read finite declarative data and serialize actual validated coverage.
from pathlib import Path  #: Resolve this checkout and explicit user output.
import sys  #: Prioritize the exact delivered sibling engine.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Avoid importing a different installed project model.
from engine.turn_links import link_plan  #: Share exact source,graph,path and chain coverage validation with HTTP/native preflight.


def main():  #: Inspect metadata only;native contact and FEM terminals remain separate qualification.
    parser=argparse.ArgumentParser(description='Inspect declared source-bound turn/section chain coverage;no native/FEM solve')  #: State planned-only physical meaning before writing output.
    for name in ('project','ports','links','output'):parser.add_argument(name,type=Path)  #: Keep every input/output intent explicit.
    args=parser.parse_args();plan=link_plan(json.loads(args.project.read_text(encoding='utf-8')),json.loads(args.ports.read_text(encoding='utf-8')),json.loads(args.links.read_text(encoding='utf-8')))  #: Complete all common validation before replacing a prior user inspection.
    args.output.write_text(json.dumps(plan,indent=2,allow_nan=False)+'\n',encoding='utf-8')  #: Publish only a completed finite source-bound inspection;failed validation leaves prior output intact.


if __name__=='__main__':main()  #: Keep imports free of source execution or file writes.
