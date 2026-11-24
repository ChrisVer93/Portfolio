"""Source CLI for actual reference multiwinding mesh and air-domain studies."""
import argparse  #: Require explicit source, electrical ports, factors and output destination.
import json  #: Read original project data and save exact finite reproducible study inputs/results.
from pathlib import Path  #: Resolve delivered source and explicit user file paths.
import sys  #: Import this checkout instead of an installed application copy.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Bind execution to the delivered numerical implementation.
from engine.port_study import port_study  #: Share the exact GUI/browser field study and resource/source guards.
if __name__=='__main__':  #: Keep importing this development entry point free of work and file writes.
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project',type=Path);p.add_argument('output',type=Path);p.add_argument('--input-id',required=True);p.add_argument('--short',action='append',default=[]);p.add_argument('--mesh-factors',default='1,2');p.add_argument('--air-factors',default='1');p.add_argument('--mesh-mode',choices=['target','interval'],default='interval')  #: Expose distinct independent electrical IDs and mesh/air factor axes.
    a=p.parse_args();options=dict(mesh_mode=a.mesh_mode,input_id=a.input_id,shorted_ids=a.short,mesh_factors=[int(v) for v in a.mesh_factors.split(',')],air_factors=[int(v) for v in a.air_factors.split(',')])  #: Preserve exact declared integer factors and every selected short.
    value=port_study(json.loads(a.project.read_text(encoding='utf-8')),options,print);a.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')  #: Execute genuine bounded field solves before saving any completed study result.
