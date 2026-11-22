"""Solve a fixed-source native adaptive loop with optional budget-aware p enrichment."""
import argparse  #: Require explicit model/result paths and an optional actual enrichment order.
import json  #: Save complete accepted meshes, fields and stopping evidence.
from pathlib import Path  #: Protect input bytes and resolve local source files.
import sys  #: Load this exact source checkout.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Pin imports to the delivered engine.
from engine.loop_adaptive import solve_adaptive_loop,enrich_adaptive  #: Run the actual conservative native adaptive/enrichment pipeline.


def main():  #: Execute one standalone bounded adaptive source operation.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('model',type=Path);parser.add_argument('output',type=Path)  #: Require distinct explicit SI input and result paths.
    parser.add_argument('--enrich-order',type=int,choices=(2,3));args=parser.parse_args()  #: Select only a qualified optional native approximation order.
    if args.model.resolve()==args.output.resolve():parser.error('Output must differ from input model')  #: Reject an in-place overwrite before any source or field solve.
    result=solve_adaptive_loop(json.loads(args.model.read_text(encoding='utf-8')))  #: Solve, measure, mark and actually refine the fixed current source.
    if args.enrich_order is not None:result['enrichment']=enrich_adaptive(result,args.enrich_order)  #: Keep the higher-order solution separate and bind it to its own actual accepted mesh.
    args.output.write_text(json.dumps(result,allow_nan=False)+'\n',encoding='utf-8')  #: Publish only complete finite results after every selected operation succeeds.


if __name__=='__main__':main()  #: Preserve import without command side effects.
