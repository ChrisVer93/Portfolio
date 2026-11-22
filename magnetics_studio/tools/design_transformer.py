"""Generate rechecked two-winding transformer candidates using the isolated native adviser."""
import argparse  #: Require explicit requirements and result file paths.
import json  #: Preserve complete physical requests and generated native MAS designs.
from pathlib import Path  #: Bind this CLI to the exact delivered source and distinct input/output files.
import sys  #: Import this checkout rather than another installed Studio.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Resolve the trusted local engine and worker.
from engine.transformer_designer import validate_request  #: Apply strict physical preflight before launching native work.
from engine.backend_process import run_backend  #: Reuse actual process isolation and the existing 240-second native budget.


def main():  #: Complete source validation and native synthesis before writing output.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('request',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()  #: Expose one complete SI design request and one separate result destination.
    if args.request.resolve()==args.output.resolve():parser.error('Output must differ from requirements input')  #: Protect original target and waveform files.
    request=validate_request(json.loads(args.request.read_text(encoding='utf-8')))  #: Reject nonfinite/unsupported/missing constraints before a native process runs.
    result=run_backend('design_transformer',{'design_request':request})  #: Run the actual full adviser, per-corner re-simulation and explicit component gates.
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')  #: Preserve previous output on computational/preflight failure and publish only a completed finite result.
    print(json.dumps(dict(status=result['status'],passed_count=result['passed_count'],candidates=len(result['candidates']))))  #: Report candidate outcome without a FEM/manufacturing certification claim.


if __name__=='__main__':main()  #: Keep imports free of native work and file writes.
