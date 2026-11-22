"""Internal source worker for optional FEM and core CAD; no executable packaging."""
import base64  #: Return checked CAD exchange bytes without exposing filesystem paths to HTTP clients.
import json  #: Read and write the fixed parent/child data protocol.
import pathlib  #: Keep source imports and private job output explicit.
import sys  #: Select the trusted operation requested by the parent.
import tempfile  #: Stage optional CAD output within this worker's lifetime.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  #: Import this exact source tree rather than a global engine package.


def execute(action, request):  #: Dispatch only supported native operations.
    if action == 'design_transformer':  #: Run catalogue synthesis in its own cancellable native process without touching FEM state.
        from engine.transformer_designer import design  #: Load the pinned component adviser only inside this explicit worker action.
        return design(request['design_request'])  #: Complete native design, re-simulation and every explicit component check before returning.
    if action == 'geometry_cad':  #: Keep new field-region CAD independent of older catalogue-core and FEM routes.
        from engine.geometry_cad import export_cad  #: Load the separate checked rectangular geometry adapter in this worker only.
        with tempfile.TemporaryDirectory(prefix='field_cad_') as temporary:  #: Keep every native STEP part private until the complete archive passes verification.
            if type(request.get('include_turn_solids',False)) is not bool: raise ValueError('include_turn_solids must be boolean')  #: Reject ambiguous direct-worker geometry requests before interpreting their scope.
            if type(request.get('include_bobbin_sleeves',False)) is not bool or request.get('include_bobbin_sleeves',False) and not request.get('include_turn_solids',False): raise ValueError('Boolean include_bobbin_sleeves requires closed turns')  #: Reject implicit or standalone sleeve completion at the direct worker boundary.
            if 'bobbin_parts' in request and (not isinstance(request['bobbin_parts'],dict) or not request.get('include_turn_solids',False)):raise ValueError('Explicit bobbin parts require closed turns')  #: Do not silently ignore declared bobbin geometry on another worker route.
            if 'turn_ports' in request and (not isinstance(request['turn_ports'],dict) or not request.get('include_turn_solids',False)):raise ValueError('Turn ports require individual turns')  #: Reject declared null or silently ignored cut packets at the direct worker boundary.
            if 'turn_links' in request:  #: Dispatch explicit connections without silently altering ordinary turn/bobbin exports.
                if not request.get('include_turn_solids',False) or not isinstance(request.get('turn_ports'),dict) or request.get('include_bobbin_sleeves',False) or 'bobbin_parts' in request:raise ValueError('Links require individual turns and slit packet; bobbin/sleeves are outside this pilot')  #: Reject ignored/conflicting connection modes at the direct worker boundary.
                from engine.turn_links import export_links  #: Keep native joining inside the existing isolated cancellable worker.
                return export_links(request['project'],temporary,request['turn_ports'],request['turn_links'])  #: Complete actual path,contact,collision,fusion and transferred STEP checks before returning a result.
            if request.get('include_turn_solids',False):  #: Generate explicitly requested closed geometry without changing field equations.
                from engine.turn_cad import export_turn_cad  #: Load the additive winding/sleeve adapter only for this optional worker operation.
                return export_turn_cad(request['project'],temporary,request.get('include_bobbin_sleeves',False),request.get('bobbin_parts'),request.get('turn_ports'))  #: Pass explicit bobbin and terminal packets through isolated native reimport/face/collision checks without changing fields.
            return export_cad(request['project'], temporary, request.get('include_envelopes', True))  #: Return checked fixed-name archive bytes, not arbitrary filesystem content.
    if action == 'ngsolve':  #: Keep native FEM imports isolated from OpenMagnetics CAD jobs.
        from engine.ngsolve_backend import solve_native  #: Load the actual qualified external FEM implementation.
        return solve_native(request['project'], request.get('options'), bool(request.get('matrix', True)), lambda line: print(line, flush=True))  #: Preserve current source options and stream numerical progress.
    if action == 'openmagnetics':  #: Keep CAD/OpenMagnetics native state out of the FEM process.
        from engine.openmagnetics_bridge import create_case  #: Reuse the previously verified component/core-CAD bridge.
        with tempfile.TemporaryDirectory(prefix='core_cad_') as temporary:  #: Retain native exports only long enough to transport checked bytes.
            result = create_case(request['core_request'], temporary)  #: Calculate and verify real core CAD using the pinned package versions.
            import cadquery as cq  #: Render a projection from the same checked STEP file, not a synthetic illustration.
            solid = cq.importers.importStep(str(pathlib.Path(temporary)/'screening_core.step')).val()  #: Reimport the exact core CAD being offered for download.
            result['cad_svg'] = cq.exporters.getSVG(solid, opts={'width': 640, 'height': 400, 'projectionDir': (1, -1, 1), 'showAxes': False, 'showHidden': False})  #: Provide an actual isometric CAD projection without inventing field data.
            result['cad_files'] = {name: base64.b64encode((pathlib.Path(temporary)/name).read_bytes()).decode('ascii') for name in result['files']}  #: Transport only verified fixed-name exchange files, not arbitrary user paths.
            return result  #: Preserve component-model provenance and applicability warnings.
    raise ValueError('Unsupported backend worker action')  #: Reject arbitrary native operations at the child boundary too.


if __name__ == '__main__':  #: Run this private protocol only when explicitly launched as a source script.
    request = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))  #: Read the parent-generated finite model request.
    result = execute(sys.argv[1], request)  #: Execute the whitelisted physical operation.
    pathlib.Path(sys.argv[3]).write_text(json.dumps(result, allow_nan=False), encoding='utf-8')  #: Publish only a complete finite JSON result after successful execution.
