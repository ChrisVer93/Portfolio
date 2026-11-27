"""Reference-only JSON bridge for the original interface inside a Pyodide worker."""
import importlib  #: Resolve only explicitly whitelisted original metadata/model adapters.
import json  #: Keep browser requests and numerical results finite and portable.
from pathlib import Path  #: Read the same bundled examples and original builder data.
from .project import validate  #: Preserve all original material/source/electrical membership guards.
from .connections import require_static_sources  #: Reject AC solids on every static field action.
from .analysis import solve_project,convergence,current_sweep,mesh_public  #: Reuse exact original field, study and export data.
from .adaptive import adaptive_solve  #: Reuse actual original reference refinement.
from .ac import solve_ac,frequency_sweep  #: Preserve dedicated reference complex-field solving.
from .mesh import build_mesh  #: Preserve original mesh generation.
from .export import field_csv,vtk,report_html  #: Reuse exact field export schemas and physical units.
ROOT=Path(__file__).resolve().parents[1]  #: Resolve the actual virtual source tree, not remote files.
ACTIONS={'mesh','solve','convergence','sweep','adaptive','ac','ac_sweep','port_study'}  #: Keep unavailable native code visibly outside browser capabilities.
ROUTES={'/api/builder/catalog':('builder','catalog',[]),'/api/builder/upgrade':('workflow','upgrade',['specification']),'/api/builder/build':('builder','build',['specification']),'/api/builder/mas-export':('mas_exchange','export_exchange',['specification','options']),'/api/builder/mas-restore':('mas_exchange','restore_exchange',['packet','mode']),'/api/builder/mas-core-export':('mas_core_geometry','export_core_geometry',['specification']),'/api/builder/mas-core-apply':('mas_core_geometry','apply_core_geometry',['packet','mode']),'/api/builder/mas-material-export':('mas_material','export_material',['specification']),'/api/builder/mas-material-apply':('mas_material','apply_material',['packet','mode']),'/api/bobbin-draft':('bobbin_cad','draft_bobbin',['project']),'/api/turn-ports-draft':('turn_ports','draft_ports',['project']),'/api/turn-links-draft':('turn_links','draft_links',['project','turn_ports']),'/api/turn-links-plan':('turn_links','link_plan',['project','turn_ports','turn_links'])}  #: Share original builder/MAS/source-draft functionality through an explicit callable whitelist.


def preflight(request):  #: Validate before the browser replaces its previous accepted job or result.
    action=request.get('action','solve')  #: Preserve the original default reference solve.
    if action not in ACTIONS:raise ValueError('This native action requires the Windows desktop build; online preview runs reference solvers')  #: Never fabricate native adviser/CAD/FEM availability.
    project=validate(request['project'])  #: Validate a detached complete original FEM model.
    if action in {'solve','convergence','sweep','adaptive'}:require_static_sources(project)  #: Preserve static/AC source separation and independent winding identity.
    if action=='port_study':  #: Preflight all actual fitted study cases before replacing an accepted browser job.
        from .port_study import plan_study  #: Share physical translation and bounded-work validation with desktop execution.
        plan_study(project,request.get('options'))  #: Reject unsupported physics, ports and fitted mesh budgets transactionally.
    d=project['domain'];cells=d['nx']*d['ny']*(d.get('nz',1)*6 if project['mode']=='3d' else 2)  #: Bound initial reference work using actual grid dimensions.
    if cells>24000:raise ValueError('Online preview initial mesh budget is 24000 cells; use the desktop build for larger studies')  #: Make the additional browser resource ceiling explicit rather than truncate geometry.
    return project  #: Retain original project semantics without editing the source design.


def run(request,progress=None):  #: Perform genuine numerical work inside the cancellable browser worker.
    project=preflight(request);action=request.get('action','solve');matrix=bool(request.get('matrix',True))  #: Reuse authoritative physical preflight at execution time too.
    if action=='port_study':  #: Execute genuine reference study matrices inside the terminable Python worker.
        from .port_study import port_study  #: Reuse the exact shared linear field study.
        return port_study(project,request.get('options'),progress)  #: Retain both physical axes and real numerical provenance in the browser result.
    if action=='mesh':return {'project':project,'mesh':mesh_public(build_mesh(project,progress)),'kind':'mesh'}  #: Return an actual original mesh, never a display-only placeholder.
    if action=='convergence':return convergence(project,progress)  #: Execute the original complete reference mesh study.
    if action=='sweep':return current_sweep(project,request.get('winding_id'),request.get('values'),progress)  #: Retain canonical electrical keys and actual bias-reference solves.
    if action=='adaptive':return adaptive_solve(project,request.get('options'),matrix,progress)  #: Preserve original error-indicator/refinement semantics.
    if action=='ac':return solve_ac(project,request.get('options'),progress)  #: Solve genuine reference AC fields.
    if action=='ac_sweep':return frequency_sweep(project,request.get('frequencies'),request.get('options'),progress)  #: Retain actual frequency-dependent complex studies.
    return solve_project(project,matrix,progress)  #: Execute unchanged reference 2D/3D field formulations.


def rpc(path,data=None):  #: Share original metadata/validation/import adapters without a Python HTTP server.
    data=data or {}  #: Keep read-only metadata calls independent of a request body.
    if path=='/api/session':return dict(token='browser-local',version='0.9.36',examples=[p.stem for p in sorted((ROOT/'examples').glob('*.json')) if p.name!='transformer_design_request.json'])  #: Preserve original menu contents and explicit browser build identity.
    if path=='/api/backends':return dict(design_transformer=False,ngsolve=False,openmagnetics=False,geometry_cad=False,packages={},geometry_cad_packages={},runtime='Pyodide reference preview')  #: Make unavailable compiled native dependencies explicit to existing controls.
    if path.startswith('/api/example/') or path=='/api/designer/example':  #: Return the exact original source examples through the virtual filesystem.
        name=path.rsplit('/',1)[-1] if path!='/api/designer/example' else 'transformer_design_request';allowed={p.stem:p for p in (ROOT/'examples').glob('*.json')}  #: Bind reads to known example names, preventing traversal.
        if name not in allowed:raise ValueError('Unknown example')  #: Reject arbitrary virtual filesystem reads.
        value=json.loads(allowed[name].read_text());return validate(value) if value.get('mode') in ['2d','3d'] else value  #: Canonicalise genuine FEM imports while retaining separate request schemas.
    if path=='/api/port-reduction':  #: Offer the same genuine Python matrix reduction in WebAssembly without starting a field job.
        from .port_reduction import reduce_ports  #: Preserve identical matrix/passivity/electrical identity checks online and on desktop.
        return reduce_ports(data['circuits'],data['input_id'],data['shorted_ids'])  #: Return explicit linear lossless short conditions and exact matrix provenance.
    if path=='/api/validate':return {'project':validate(data['project'])}  #: Preserve actual original project validation.
    if path=='/api/validate-material':  #: Keep digitised material application tied to the original magnetic-law guards.
        from .materials import validate_material  #: Use the exact existing material implementation.
        validate_material(data['material']);return {'valid':True}  #: Reject invalid B-H data instead of marking it accepted.
    if path=='/api/builder/layout':  #: Preserve original explicit winding/interleaving generation.
        from .workflow import definitions  #: Reuse exact original winding ownership/order semantics.
        spec=data['specification'];spec['custom_sections']=False;return {'layout':definitions(spec)[1]}  #: Return the requested original layout without starting a field job.
    if path in ROUTES:  #: Limit metadata dispatch to the actual supported source adapters.
        module,name,args=ROUTES[path];value=getattr(importlib.import_module('.'+module,__package__),name)(*[data.get(a) for a in args])  #: Call only a declared function with declared JSON argument keys.
        return {'specification':value} if path=='/api/builder/upgrade' else value  #: Preserve the original HTTP response envelope expected by the shared interface.
    raise ValueError('Unsupported browser API route')  #: Keep unimplemented endpoints actionable rather than silently succeeding.


def export(result,kind):  #: Reuse the original field export on an exact accepted solved result.
    if not result or 'fields' not in result:raise ValueError('Solve a field model before exporting')  #: Never export an incomplete/cancelled candidate field.
    return {'json':lambda r:json.dumps(r,allow_nan=False),'csv':field_csv,'vtk':vtk,'html':report_html}[kind](result)  #: Preserve original units, field arrays and downloadable report content.
