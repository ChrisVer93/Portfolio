"""Offline GUI and command-line launcher. Python 3.9+, standard library only."""
import argparse
import csv
import io
import json
import os
import pathlib
import secrets
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from engine.analysis import solve_project, convergence, current_sweep, mesh_public
from engine.adaptive import adaptive_solve
from engine.backend_process import run_backend, backend_status  #: Import lightweight optional-backend orchestration without loading native libraries.
from engine.ac import solve_ac, frequency_sweep  #: Import actual AC and frequency-study engines into the shared local launcher.
from engine.mesh import build_mesh
from engine.project import validate
from engine.connections import require_static_sources  #: Preflight static source compatibility before mutating the accepted server job state.
from engine.export import field_csv, vtk, write_report, report_html
from engine.sparse import Cancelled
from engine.builder import build as build_from_inputs, catalog as builder_catalog

ROOT = pathlib.Path(__file__).resolve().parent
MAX_BODY = 2_000_000


class Workspace:
    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.job = None
        self.result = None
        self.field_result = None
        self.cancel = threading.Event()
        self.result_job = None

    def start(self, request):
        action = request.get('action','solve')  #: Identify separate component synthesis before requiring an unrelated FEM project.
        project = None if action=='design_transformer' else validate(request['project'])  #: Preserve all existing project validation while keeping requirements-driven design independent.
        if action not in ['solve','mesh','convergence','sweep','adaptive','ac','ac_sweep','ngsolve','openmagnetics','geometry_cad','design_transformer','port_study']:  #: Accept explicit isolated transformer design while preserving existing field and CAD actions.
            raise ValueError('Unknown analysis action')
        if action=='ngsolve':  #: Reject unsupported native-order combinations before replacing an accepted job or field.
            from engine.ngsolve_backend import check_native_order  #: Keep all compiled imports isolated from lightweight server validation.
            check_native_order(project,request.get('options'))  #: Preserve accepted state for wrong dimensions, noninteger/duplicate orders and unsupported higher-order adaptation.
        if action=='port_study':  #: Preflight all physical mesh/air cases without replacing the accepted workspace state.
            from engine.port_study import plan_study  #: Keep compiled native libraries outside reference-study validation.
            plan_study(project,request.get('options'))  #: Reject nonlinear/AC, unsupported geometry, invalid ports and excessive actual fitted work transactionally.
        if action=='design_transformer':  #: Validate catalogue design transactionally before replacing any accepted job or result.
            from engine.transformer_designer import validate_request as validate_design  #: Keep compiled libraries out of HTTP preflight.
            validate_design(request.get('design_request'))  #: Reject invalid targets, waveforms and constraints without changing the accepted workspace state.
            if not backend_status()['design_transformer']:raise ValueError('Transformer designer requires optional PyOpenMagnetics==1.7.35')  #: Make a missing native dependency an actionable preflight failure.
        if action in ['solve', 'adaptive', 'convergence', 'sweep', 'ngsolve']:  #: Mesh-only and dedicated AC/core-screening actions retain their distinct purposes.
            require_static_sources(project)  #: Return an actionable client error without replacing the previous job or field result.
        if action == 'geometry_cad':  #: Reject unsupported geometry before replacing an accepted job or result.
            from engine.geometry_cad import geometry_plan  #: Use lightweight preflight without loading a native CAD kernel into the server.
            if type(request.get('include_turn_solids',False)) is not bool: raise ValueError('include_turn_solids must be boolean')  #: Refuse ambiguous options before replacing a previous accepted job.
            if type(request.get('include_bobbin_sleeves',False)) is not bool or request.get('include_bobbin_sleeves',False) and not request.get('include_turn_solids',False): raise ValueError('Boolean include_bobbin_sleeves requires closed turns')  #: Keep inferred sleeve completion explicit and transaction-safe before native work.
            if request.get('include_turn_solids',False):  #: Bind optional turn geometry to the actual complete builder recipe before starting native work.
                from engine.turn_cad import turn_plan  #: Run lightweight packing/source-consistency checks without importing CAD.
                turn_plan(project)  #: Reject stale raw field edits, unsupported dimensions and overfilled blocks transactionally.
            if 'bobbin_parts' in request:  #: Validate all declared explicit geometry before replacing an accepted job or field.
                if not request.get('include_turn_solids',False) or request.get('include_bobbin_sleeves',False):raise ValueError('Explicit bobbin parts require closed turns and exclude inferred sleeves')  #: Reject conflicting geometry modes transactionally.
                from engine.bobbin_cad import bobbin_plan  #: Keep native CAD out of the preflight server.
                bobbin_plan(project,request['bobbin_parts'])  #: Require exact source/anchor association and explicit typed SI dimensions.
            if 'turn_ports' in request:  #: Validate explicit cut dimensions/source binding before replacing accepted jobs or fields.
                if not request.get('include_turn_solids',False):raise ValueError('Turn ports require individual turns')  #: Do not silently ignore selected cuts in ordinary box/prism export.
                from engine.turn_ports import port_plan  #: Keep native CAD imports out of transactional HTTP preflight.
                port_plan(project,request['turn_ports'])  #: Reject stale, null, duplicate or geometrically invalid terminal packets.
            if 'turn_links' in request:  #: Validate exact connection incidence/path data before replacing an accepted job or field.
                if not request.get('include_turn_solids',False) or not isinstance(request.get('turn_ports'),dict) or request.get('include_bobbin_sleeves',False) or 'bobbin_parts' in request:raise ValueError('Links require individual turns and slit packet; bobbin/sleeves are outside this pilot')  #: Keep explicitly unsupported combinations and ignored packets transaction-safe.
                from engine.turn_links import link_plan  #: Run pure source/graph/path validation without loading native CAD into the server.
                link_plan(project,request['turn_ports'],request['turn_links'])  #: Reject stale cuts,wrong electrical owners,branches,cycles and invalid SI routes before starting a new job.
            geometry_plan(project, request.get('include_envelopes', True))  #: Keep polygon, complexity and thickness failures actionable and transaction-safe.
        with self.lock:
            if self.job and self.job['status']=='running':
                raise ValueError('An analysis is already running')
            job_id = secrets.token_hex(8)
            self.cancel.clear()
            self.job = {'id':job_id,'status':'running','action':action,'log':[], 'started':time.time()}
        def log(message):
            with self.lock:
                self.job['log'].append(str(message))
                self.job['log'] = self.job['log'][-250:]
        def worker():
            try:
                if action in ['ngsolve', 'openmagnetics', 'geometry_cad', 'design_transformer']:  #: Route transformer design, native FEM and CAD through the existing cancellable isolated process boundary.
                    result = run_backend(action, request, log, self.cancel.is_set)  #: Preserve real worker errors and avoid loading two CAD kernels into the GUI server.
                elif action=='mesh':  #: Preserve the original mesh-only branch after the new isolated backend dispatch.
                    result = {'project':project,'mesh':mesh_public(build_mesh(project,log,self.cancel.is_set)),'kind':'mesh'}
                elif action=='port_study':  #: Run the explicitly selected reference multiport study as an ordinary cancellable job.
                    from engine.port_study import port_study  #: Reuse the shared actual matrix/mesh/domain implementation.
                    result=port_study(project,request.get('options'),log,self.cancel.is_set)  #: Retain prior accepted fields when this separate study completes or is cancelled.
                elif action=='convergence':
                    result = convergence(project,log,self.cancel.is_set)
                elif action=='sweep':
                    result = current_sweep(project,request.get('winding_id'),request.get('values'),log,self.cancel.is_set)
                elif action=='ac':  #: Route a single accepted AC job to the dedicated frequency-domain branch.
                    result = solve_ac(project,request.get('options'),log,self.cancel.is_set)  #: Pass the model, run settings, progress callback and cancellation flag into the real complex-field solver.
                elif action=='ac_sweep':  #: Route a bounded AC frequency study separately from static current and mesh studies.
                    result = frequency_sweep(project,request.get('frequencies'),request.get('options'),log,self.cancel.is_set)  #: Pass the complete frequency list and common controls to independently recomputed AC solves.
                elif action=='adaptive':
                    result = adaptive_solve(project,request.get('options'),bool(request.get('matrix',True)),log,self.cancel.is_set)
                else:
                    result = solve_project(project,bool(request.get('matrix',True)),log,self.cancel.is_set)
                if self.cancel.is_set():
                    raise Cancelled('Analysis cancelled')
                with self.lock:
                    self.result = result
                    if 'fields' in result:
                        self.field_result = result
                    self.result_job = job_id
                    self.job['status'] = 'done'
                    log('Completed')
            except Cancelled as e:
                with self.lock:
                    self.job['status'] = 'cancelled'
                    self.job['error'] = str(e)
            except Exception as e:
                traceback.print_exc()
                with self.lock:
                    self.job['status'] = 'error'
                    self.job['error'] = str(e)
        threading.Thread(target=worker,daemon=True).start()
        return job_id


def make_server(port=0):
    state = Workspace()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass

        def reply(self,body,kind='application/json',status=200):
            if isinstance(body,(dict,list)):
                body = json.dumps(body,allow_nan=False)
            if isinstance(body,str):
                body = body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type',kind+'; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('X-Frame-Options','DENY')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):
                pass

        def authorized(self,mutating=False):
            host = self.headers.get('Host','')
            if host != f'127.0.0.1:{self.server.server_port}':
                self.reply({'error':'Invalid host'},status=403)
                return False
            if mutating and (self.headers.get('X-Studio-Token') != state.token or
               self.headers.get('Origin') not in [None,f'http://{host}']):
                self.reply({'error':'Invalid local session token or origin'},status=403)
                return False
            return True

        def do_GET(self):
            if not self.authorized():
                return
            path = urlparse(self.path).path
            try:
                if path=='/api/backends':  #: Expose actual optional package availability without importing native libraries.
                    return self.reply(backend_status())  #: Keep unavailable native features explicit in the browser.
                if path=='/api/builder/catalog':
                    return self.reply(builder_catalog())
                if path=='/api/designer/example':  #: Supply a complete balanced two-winding design request independently of FEM examples.
                    return self.reply(json.loads((ROOT/'examples/transformer_design_request.json').read_text(encoding='utf-8')))  #: Preserve explicit SI waveform/target provenance for both the form and downloadable request.
                if path=='/api/session':
                    return self.reply({'token':state.token,'version':'0.9.36','examples':[p.stem for p in sorted((ROOT/'examples').glob('*.json')) if p.name!='transformer_design_request.json']})  #: Identify the new release and keep inverse-design requests out of the ordinary FEM example selector.
                if path=='/api/status':
                    with state.lock:
                        return self.reply(state.job or {'status':'idle'})
                if path=='/api/result':
                    with state.lock:
                        return self.reply({'job_id':state.result_job,'result':state.result})
                if path.startswith('/api/example/'):
                    name = path.rsplit('/',1)[-1]
                    allowed = {p.stem:p for p in (ROOT/'examples').glob('*.json')}
                    if name not in allowed:
                        return self.reply({'error':'Unknown example'},status=404)
                    example = json.loads(allowed[name].read_text(encoding='utf-8'))  #: Read the selected model or separate core-screening request without changing its fixture file.
                    return self.reply(validate(example) if example.get('mode') in ['2d', '3d'] else example)  #: Canonicalise FEM imports for current editing; preserve the distinct upstream core-request schema.
                if path in ['/api/export/csv','/api/export/vtk','/api/export/html','/api/export/json']:
                    with state.lock:
                        r = state.field_result
                    if not r or 'fields' not in r:
                        raise ValueError('Solve a field model before exporting')
                    values = {'csv':field_csv,'vtk':vtk,'html':report_html,'json':lambda r:json.dumps(r,allow_nan=False)}
                    return self.reply(values[path.rsplit('/',1)[-1]](r),'text/plain')
                files = {'/':('index.html','text/html'),'/cad-view.js':('cad-view.js','application/javascript'),'/field-view.js':('field-view.js','application/javascript'),'/app.js':('app.js','application/javascript'),'/style.css':('style.css','text/css'),'/builder.js':('builder.js','application/javascript'),'/workflow-ui.js':('workflow-ui.js','application/javascript'),'/digitiser.js':('digitiser.js','application/javascript'),'/digitiser-example.png':('../data/digitiser-example.png','image/png')}
                files['/adaptive-ui.js'] = ('adaptive-ui.js', 'application/javascript')
                files['/digitiser.css'] = ('digitiser.css', 'text/css')  #: Serve the scoped digitiser layout through the same protected local asset router.
                files['/port-reduction-ui.js'] = ('port-reduction-ui.js', 'application/javascript')  #: Serve explicit simultaneous-short controls through the original protected asset router.
                files['/designer-ui.js'] = ('designer-ui.js', 'application/javascript')  #: Serve requirements-to-candidates controls through the protected local asset router.
                files['/designer.css'] = ('designer.css', 'text/css')  #: Keep transformer-design dialog layout scoped to its own stylesheet.
                files['/native-ui.js'] = ('native-ui.js', 'application/javascript')  #: Serve the additive external FEM/core-CAD controls through the protected asset router.
                files['/study-charts.js'] = ('study-charts.js', 'application/javascript')  #: Serve the shared signed-data SVG renderer through the existing protected asset router.
                files['/inductance-ui.js'] = ('inductance-ui.js', 'application/javascript')  #: Serve the missing current/frequency inductance-study views without relaxing local access checks.
                files['/ac-ui.js'] = ('ac-ui.js', 'application/javascript')  #: Serve the additive AC interface through the existing protected loopback asset router.
                files['/cad-export-ui.js'] = ('cad-export-ui.js', 'application/javascript')  #: Serve the additive checked CAD interface under the existing local asset policy.
                files['/mas-core-ui.js'] = ('mas-core-ui.js', 'application/javascript')  #: Serve the additive core-geometry builder controls through the same bounded asset route.
                if path in files:
                    name,kind = files[path]
                    return self.reply((ROOT/'web'/name).read_bytes(),kind)
                self.reply({'error':'Not found'},status=404)
            except Exception as e:
                self.reply({'error':str(e)},status=400)

        def do_POST(self):
            if not self.authorized(True):
                return
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= MAX_BODY:
                    raise ValueError('Request must contain at most 2 MB of JSON')
                data = json.loads(self.rfile.read(length))
                path = urlparse(self.path).path
                if path=='/api/port-reduction':  #: Postprocess an explicitly supplied electrical matrix without replacing accepted jobs or fields.
                    from engine.port_reduction import reduce_ports  #: Share the actual standard-library energy/cancellation implementation.
                    return self.reply(reduce_ports(data['circuits'],data['input_id'],data['shorted_ids']))  #: Retain token/origin/body guards and exact source-matrix provenance.
                if path=='/api/turn-links-plan':  #: Inspect actual source-bound declared connectivity without starting or replacing a field/native job.
                    from engine.turn_links import link_plan  #: Reuse the exact worker preflight,source binding and ordered coverage implementation.
                    return self.reply(link_plan(data['project'],data['turn_ports'],data['turn_links']))  #: Existing token,origin and request-size protections apply;no native topology or solved terminal is fabricated.
                if path=='/api/turn-links-draft':  #: Create source/cut-bound terminal metadata without guessing a route or replacing a result.
                    from engine.turn_links import draft_links  #: Share exactly the source CLI and export preflight draft contract.
                    return self.reply(draft_links(data['project'],data['turn_ports']))  #: Existing session,origin and body bounds protect this pure metadata route.
                if path=='/api/turn-ports-draft':  #: Create actual source-bound turn anchors without changing a job or inventing cut dimensions.
                    from engine.turn_ports import draft_ports  #: Reuse the source CLI and worker's exact draft contract.
                    return self.reply(draft_ports(data['project']))  #: Existing token, origin and body-size checks protect this metadata operation.
                if path=='/api/bobbin-draft':  #: Return source association only, with no field/job replacement or invented dimensions.
                    from engine.bobbin_cad import draft_bobbin  #: Share draft semantics with the source CLI and export preflight.
                    return self.reply(draft_bobbin(data['project']))  #: Existing session, origin and request-size checks protect this route.
                if path=='/api/run':
                    return self.reply({'job_id':state.start(data)})
                if path=='/api/cancel':
                    state.cancel.set()
                    return self.reply({'ok':True})
                if path=='/api/validate-material':
                    from engine.materials import validate_material
                    validate_material(data['material'])
                    return self.reply({'valid':True})
                if path=='/api/builder/upgrade':
                    from engine.workflow import upgrade
                    return self.reply({'specification':upgrade(data['specification'])})
                if path=='/api/builder/layout':
                    from engine.workflow import definitions
                    spec=data['specification']
                    spec['custom_sections']=False
                    return self.reply({'layout':definitions(spec)[1]})
                if path=='/api/builder/build':
                    return self.reply(build_from_inputs(data['specification']))
                if path=='/api/builder/mas-export':  #: Export explicitly declared MAS subdocuments without starting or replacing a field job.
                    from engine.mas_exchange import export_exchange  #: Keep the standard-library exchange path independent of optional native packages.
                    return self.reply(export_exchange(data['specification'], data['options']))  #: Validate real builder inputs before exposing native MAS projections.
                if path=='/api/builder/mas-restore':  #: Rebuild an integrity-checked packet through the selected dimensional builder.
                    from engine.mas_exchange import restore_exchange  #: Use the shared canonical winding and material workflow.
                    return self.reply(restore_exchange(data['packet'], data.get('mode')))  #: Reject stale or edited projections instead of silently ignoring them.
                if path=='/api/builder/mas-core-export':  #: Export exact supported E-shape/gap subdocuments without replacing an accepted field job.
                    from engine.mas_core_geometry import export_core_geometry  #: Keep native packages optional; this mapping uses the real shared builder.
                    return self.reply(export_core_geometry(data['specification']))  #: Preserve source hierarchy, material binding and explicit geometry coordinates.
                if path=='/api/builder/mas-core-apply':  #: Apply deliberately edited supported core geometry to its retained builder design.
                    from engine.mas_core_geometry import apply_core_geometry  #: Use the same checks and dimensional adapters as the source CLI.
                    return self.reply(apply_core_geometry(data['packet'], data.get('mode')))  #: Do not mutate current fields or job state during design preview/import.
                if path=='/api/builder/mas-material-export':  #: Validate native material points without replacing any accepted field job.
                    from engine.mas_material import export_material  #: Use the shared point semantics and real builder association.
                    return self.reply(export_material(data['specification']))  #: Export actual material data bound to generated core regions.
                if path=='/api/builder/mas-material-apply':  #: Apply deliberately edited native points to the packet's complete retained design.
                    from engine.mas_material import apply_material  #: Share exact CLI/UI dimensional and constitutive-law guards.
                    return self.reply(apply_material(data['packet'], data.get('mode')))  #: Return a preview while leaving accepted solver state unchanged.
                if path=='/api/validate':
                    return self.reply({'project':validate(data['project'])})
                self.reply({'error':'Not found'},status=404)
            except Exception as e:
                self.reply({'error':str(e)},status=400)
    server = ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads = True
    server.studio_state = state
    return server


def main():
    ap = argparse.ArgumentParser(description='Magnetics Studio 0.9.36 — MAS local native fit and limited magnetic FEM')  #: Identify the component-adviser release without claiming new FEM physics coverage.
    ap.add_argument('--project',help='JSON project for a command-line solve')
    ap.add_argument('--output',default='results.html',help='CLI self-contained HTML report')
    ap.add_argument('--json',dest='json_output',help='Full result JSON file')
    ap.add_argument('--vtk',dest='vtk_output',help='VTK field export file')
    ap.add_argument('--csv',dest='csv_output',help='CSV field export file')
    ap.add_argument('--port',type=int,default=0,help='Local GUI port (0 selects an available port)')
    ap.add_argument('--no-open',action='store_true')
    ap.add_argument('--pure-python',action='store_true',help='Disable acceleration even if SciPy is installed')
    ap.add_argument('--no-matrix',action='store_true',help='Skip unit solves for inductance extraction')
    ap.add_argument('--adaptive', action='store_true', help='Adaptive linear 2D solve, retaining ordinary solve as the default')
    ap.add_argument('--adaptive-passes', type=int, default=4, help='Maximum adaptive passes, 1–8')
    ap.add_argument('--ac', action='store_true', help='Linear 2D RMS phasor AC/eddy-current solve')  #: Add an explicit CLI switch for the limited linear planar AC analysis.
    ap.add_argument('--frequency-hz', type=float, help='AC solve frequency in Hz; otherwise use saved settings')  #: Allow a CLI frequency override; absent overrides retain the saved AC settings.
    args = ap.parse_args()
    if args.ac and args.adaptive:  #: Prevent unsupported mixing of the static adaptive loop with an AC analysis.
        ap.error('--ac and --adaptive are separate analyses; AC adaptation is not implemented')  #: Explain that AC-specific adaptation is not implemented instead of ignoring a requested analysis mode.
    if args.pure_python:
        os.environ['MAGNETICS_PURE_PYTHON']='1'
    if args.project:
        p = json.loads(pathlib.Path(args.project).read_text(encoding='utf-8-sig'))
        r = None if args.ac else (adaptive_solve(p, {'max_passes': args.adaptive_passes}, not args.no_matrix, print) if args.adaptive else solve_project(p,not args.no_matrix,print))  #: Skip any unnecessary static solve for an AC request; retain the existing static/adaptive paths otherwise.
        if args.ac:  #: Enter the explicit AC CLI branch only when requested.
            controls = {'frequency_Hz': args.frequency_hz} if args.frequency_hz is not None else None  #: Construct a named frequency override only when the user supplied it.
            r = solve_ac(p,controls,print)  #: Run the actual AC equations and forward progress to the terminal before ordinary result export.
        write_report(r,args.output)
        for file,value in [(args.json_output,json.dumps(r,allow_nan=False)),(args.vtk_output,vtk(r)),(args.csv_output,field_csv(r))]:
            if file:
                pathlib.Path(file).write_text(value,encoding='utf-8')
        print(json.dumps(r['stats'],indent=2))
        print('Report:',pathlib.Path(args.output).resolve())
        if not args.no_open:
            webbrowser.open(pathlib.Path(args.output).resolve().as_uri())
        return
    server = make_server(args.port)
    url = f'http://127.0.0.1:{server.server_port}/'
    print('Magnetics Studio 0.9.36\nOpen:',url,'\nLocal machine only. Press Ctrl+C to stop.',flush=True)  #: Report the actual source version without changing local launch/shutdown behaviour.
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.studio_state.cancel.set()
    finally:
        server.server_close()


if __name__=='__main__':
    main()
