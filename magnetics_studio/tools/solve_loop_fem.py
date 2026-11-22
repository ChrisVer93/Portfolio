"""Solve a matched finite-copper loop with reference and optional native magnetic FEM."""
import argparse  #: Require explicit SI request, output and optional native formulation controls.
import json  #: Save actual source, field, energy and qualification diagnostics.
from pathlib import Path  #: Resolve files and protect the input from overwrite.
import sys  #: Load the delivered sibling engine rather than an installed application copy.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Pin CLI imports to this source checkout.
from engine.loop_fem import solve_loop_fem  #: Run the conservative conforming reference transfer.


def main():  #: Execute one complete detached source-form magnetic FEM operation.
    parser = argparse.ArgumentParser(description=__doc__)  #: Describe the limited static, homogeneous-mu0 verification scope.
    parser.add_argument('model',type=Path);parser.add_argument('output',type=Path)  #: Require distinct input and solved-result paths.
    parser.add_argument('--native-order',type=int,choices=(0,2,3))  #: Select an explicitly qualified optional native curl approximation order.
    parser.add_argument('--full-gradients',action='store_true')  #: Request the complete higher-order mixed Coulomb gauge for comparison.
    args = parser.parse_args()  #: Validate syntax before expensive solving or native imports.
    if args.model.resolve()==args.output.resolve():parser.error('Output must differ from input model')  #: Preserve the exact input bytes.
    if args.full_gradients and args.native_order is None:parser.error('Full gradients requires a native order')  #: Reject an unused formulation control.
    result = solve_loop_fem(json.loads(args.model.read_text(encoding='utf-8')))  #: Solve the actual finite conductor, conforming magnetic source and reference field.
    if args.native_order is not None:  #: Load the compiled backend only for an explicitly requested operation.
        from engine.loop_native import solve_native_transfer  #: Keep optional compiled imports out of normal application startup.
        result['native'] = solve_native_transfer(result,args.native_order,args.full_gradients)  #: Solve the same exact source and magnetic mesh with the pinned native formulation.
    args.output.write_text(json.dumps(result,allow_nan=False)+'\n',encoding='utf-8')  #: Publish finite complete source/field/energy results only after all selected checks pass.


if __name__=='__main__':  #: Preserve import without command side effects.
    main()  #: Run only when invoked as a source CLI.
