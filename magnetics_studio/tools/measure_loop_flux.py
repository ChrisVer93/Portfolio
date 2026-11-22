"""Solve a checked finite-loop frame and measure oriented triangular pickup flux."""
import argparse  #: Require explicit frame, surface and output paths.
import json  #: Read and save detached reproducible physical observations.
from pathlib import Path  #: Bind this CLI to the delivered engine and distinct files.
import sys  #: Use the exact checked-out source rather than another installed Studio.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Resolve engine imports from the delivered source root.
from engine.loop_native import solve_native_transfer  #: Re-solve the actual checked frame with the selected native order.


def main():  #: Complete preflight, real solve and flux integration before replacing output.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('frame',type=Path);parser.add_argument('surfaces',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--order',type=int,choices=(0,2,3),default=2);args=parser.parse_args()  #: Expose explicit physical inputs and bounded native approximation order.
    if args.output.resolve() in (args.frame.resolve(),args.surfaces.resolve()):parser.error('Output must differ from both inputs')  #: Preserve original solved frames and pickup definitions.
    frame=json.loads(args.frame.read_text());surfaces=json.loads(args.surfaces.read_text())  #: Read the actual stored SI mesh/current frame and ordered pickups.
    if frame.get('format') in ('magnetics-studio.adaptive-loop/1','magnetics-studio.flux-adaptive-loop/1'):frame=frame['frame']  #: Select either adaptive workflow’s final accepted frame explicitly rather than an earlier enriched mesh.
    native=solve_native_transfer(frame,order=args.order,flux_surfaces=surfaces)  #: Compute genuine native fields and clipped surface integrals, failing before output on invalid input.
    result=dict(format='magnetics-studio.loop-flux/1',frame=frame,native=native)  #: Retain the exact mesh/current provenance alongside the new measurement.
    args.output.write_text(json.dumps(result,allow_nan=False)+'\n');print(json.dumps(native['surface_flux'],allow_nan=False))  #: Save only a fully completed finite result and display physical signed fluxes.


if __name__=='__main__':main()  #: Keep module imports free of solve or file-writing side effects.
