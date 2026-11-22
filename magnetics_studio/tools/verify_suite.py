"""Q001: isolated, resumable verification with fail-closed completion evidence."""
import argparse  #: Expose explicit profile/output/budget/resume controls through a source CLI.
from contextlib import contextmanager  #: Hold one explicit exclusive writer lock around a whole profile invocation.
import hashlib  #: Record exact code, log and completion-receipt identity.
import importlib.metadata as metadata  #: Fingerprint installed versions without importing native CAD/FEM libraries.
import json  #: Store durable finite profile checkpoints and child receipts.
import math  #: Validate finite positive resource budgets.
import os  #: Preserve the current qualified environment and terminate POSIX process groups.
from pathlib import Path  #: Keep all attempt output local to an explicit verification directory.
import platform  #: Identify the actual Python/platform profile used for testing.
import signal  #: Terminate isolated POSIX process groups on cancellation or timeout.
import subprocess  #: Execute every test module in a fresh interpreter without shell evaluation.
import sys  #: Reuse the actual selected Python interpreter and expose CLI exit codes.
import time  #: Use monotonic wall time for real execution budgets.
import uuid  #: Prevent stale receipts/logs from another attempt being accepted.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Import the exact delivered verification transport when this source CLI is launched directly.
from verification.evidence_io import capture  #: Keep seekable output-file ownership exclusively in the supervising parent.

ROOT = Path(__file__).resolve().parents[1]  #: Pin application and QA-worker source relative to this delivered CLI.
FORMAT = 'magnetics-studio.verification-profile/2'  #: Version this evidence protocol independently of application project formats.
OUTCOMES = ('passed', 'passed_with_subtest_skips', 'skipped', 'expected_failure', 'failed', 'error', 'unexpected_success', 'unverified')  #: Keep limitations, failures and incomplete execution distinct from real passes.


def digest(path):  #: Bind actual local bytes to an evidence record.
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()  #: Use the same hash for source, logs and receipts.


def atomic_json(path, value):  #: Save a durable checkpoint without a partially written success record.
    temporary=path.with_suffix('.tmp')  #: Stage finite checkpoint data beside its final destination.
    with temporary.open('w',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())  #: Synchronise actual checkpoint bytes before installing them.
    temporary.replace(path)  #: Replace the checkpoint atomically; directory/power-loss durability is not claimed.


def fingerprint(test_root, files):  #: Freeze relevant source, dependency versions and selected execution semantics.
    paths = [ROOT/'studio.py', ROOT/'verification/unittest_worker.py', ROOT/'verification/runner_fixture.py',ROOT/'verification/evidence_io.py',ROOT/'verification/integrity_fixture.py',ROOT/'verification/numerical_fixture.py']  #: Include application entry, worker and synthetic failure-injection source explicitly.
    paths += [p for directory in ('engine','web','tools','tests') for p in (ROOT/directory).rglob('*') if p.is_file() and p.suffix in ('.py','.js','.cjs','.css','.html')]  #: Exclude generated results, caches, documentation and report-authoring snapshots.
    sources = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths) if p.is_file()}  #: Record exact relevant source bytes without importing test modules in the parent.
    versions = {}  #: Missing optional packages are an explicit profile property.
    for name in ('numpy','scipy','cadquery','cadquery-ocp','ngsolve','netgen-mesher','PyOpenMagnetics','OpenMagneticsVirtualBuilder','jsonschema'):  #: Fingerprint the numerical/CAD/schema combinations actually selected.
        try: versions[name] = metadata.version(name)  #: Read installed distribution metadata only.
        except metadata.PackageNotFoundError: versions[name] = None  #: Do not install or silently substitute an unavailable backend.
    return {'test_root': str(test_root), 'selected_files': {p.name:digest(p) for p in files}, 'source_sha256': sources, 'python': sys.version, 'executable': str(Path(sys.executable).resolve()), 'platform': platform.platform(), 'versions': versions, 'environment': {n:os.environ.get(n) for n in ('MAGNETICS_PURE_PYTHON','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','PYTHONPATH','STUDIO_VERIFICATION_FIXTURE','STUDIO_VERIFICATION_INTEGRITY_FIXTURE','STUDIO_VERIFICATION_NUMERICAL_OUTPUT')}}  #: Record only named relevant settings, not arbitrary environment secrets.


def validate_receipt(path, record):  #: Accept only genuine complete evidence tied to this exact attempt and source.
    proof = json.loads(path.read_text(encoding='utf-8'))  #: Malformed/missing evidence is rejected by the supervising caller.
    if proof.get('format') != 'magnetics-studio.verification-shard/1' or proof.get('token') != record['token'] or proof.get('test_file') != record['test_file'] or proof.get('test_sha256') != record['test_sha256'] or proof.get('finished') is not True or type(proof.get('successful')) is not bool: raise ValueError('Receipt identity/source/completion mismatch')  #: Require exact typed completion/success evidence, not stale or truthy text values.
    expected, cases = proof.get('expected_ids'), proof.get('cases')  #: Compare discovered identities against cases actually started and stopped.
    if not isinstance(expected,list) or not expected or any(not isinstance(x,str) for x in expected) or len(set(expected)) != len(expected) or not isinstance(cases,list) or any(not isinstance(c,dict) for c in cases): raise ValueError('Receipt needs unique nonempty discovered case IDs')  #: Reject malformed/empty discovery and non-object case records explicitly.
    ids = [c.get('id') for c in cases]  #: Retain top-level case identity separately from subtest failure/skip events.
    if any(not isinstance(x,str) for x in ids) or len(ids) != len(set(ids)) or not set(ids).issubset(expected) or (proof['successful'] and sorted(ids) != sorted(expected)) or proof.get('tests_run') != len(cases): raise ValueError('Discovered cases lack complete execution proof')  #: Successful claims require every expected case; failed fixtures retain genuinely unexecuted cases without inventing passes.
    if any(c.get('outcome') not in OUTCOMES or c['outcome']=='unverified' or 'seconds' not in c for c in cases): raise ValueError('Receipt contains unfinished or unknown case outcomes')  #: Require actual stop/outcome evidence for every credited case.
    summary = proof.get('summary', {})  #: Fixture/subtest events may outnumber top-level cases.
    if set(summary) != {'failures','errors','skip_events','expected_failures','unexpected_successes'} or any(type(v) is not int or v<0 for v in summary.values()): raise ValueError('Malformed unittest event summary')  #: Reject missing, negative, boolean or fabricated-type event counts.
    failed = any(c['outcome'] in ('failed','error','unexpected_success') for c in cases) or any(summary[k] for k in ('failures','errors','unexpected_successes'))  #: Class/module fixture failures also prevent success even when no case starts.
    if proof['successful'] == failed: raise ValueError('Receipt success conflicts with case outcomes')  #: Require consistency with actual case and fixture/subtest events.
    if proof.get('successful') and any(summary.get(k,0) for k in ('failures','errors','unexpected_successes')): raise ValueError('Receipt hides unsuccessful unittest events')  #: Fixture errors cannot be erased by otherwise passing cases.
    return proof  #: Return only structurally complete, source-bound actual evidence.


def verify_record(output,record):  #: Recheck actual completed bytes, observed exit and full case/summary accounting without repairing them.
    root=Path(output).resolve();paths={}  #: Bound every evidence read to its explicit profile directory.
    for key in ('log','receipt'):  #: Both human diagnostics and machine completion proof must remain exact.
        relative=Path(record[key])  #: Interpret only the declared relative evidence member path.
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('Evidence path must remain inside profile')  #: Reject accidental or forged traversal before reading external bytes.
        path=(root/relative).resolve()  #: Resolve symlinks before checking the allowed read boundary.
        if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size>16*1024*1024:raise ValueError('Missing, external or oversized evidence')  #: Refuse absent/escaped/unbounded files rather than reading or crediting them.
        if digest(path)!=record[key+'_sha256']:raise ValueError('Evidence '+key+' bytes changed')  #: Preserve the recorded digest; never rewrite it to match altered output.
        paths[key]=path  #: Retain only independently verified bounded local paths.
    if record.get('stdout_eof') is not True or type(record.get('captured_bytes')) is not int or record['captured_bytes']!=paths['log'].stat().st_size:raise ValueError('Evidence transport closure/length mismatch')  #: Require the real recorded EOF and retained byte length, not only a successful process exit.
    proof=validate_receipt(paths['receipt'],record)  #: Recheck actual token/source/case completion and unittest events.
    if record.get('status')!='completed' or record.get('returncode')!=0 or not proof['successful'] or record.get('cases')!=proof['cases'] or record.get('unittest_events')!=proof['summary'] or record.get('executed_cases')!=proof['tests_run'] or record.get('discovered_cases')!=len(proof['expected_ids']):raise ValueError('Evidence record/receipt accounting mismatch')  #: A stale success/count label cannot supersede the real observed complete receipt.
    lines=paths['log'].read_text(encoding='utf-8',errors='replace').splitlines()  #: Decode diagnostics only after checking the exact byte hash.
    if not any(line.startswith('Ran '+str(proof['tests_run'])+' test') for line in lines) or not any(line=='OK' or line.startswith('OK (') for line in lines):raise ValueError('Evidence lacks matching unittest completion summary')  #: A prefix log plus a complete receipt is insufficient even if hashes were captured consistently.
    return proof  #: Credit only one intact actual module; skips/expected failures remain explicit outcomes.


def audit_ledger(output,ledger,require_complete=False):  #: Audit all reusable evidence and return exact integrity errors without mutating any record or hash.
    errors=[];selected=ledger['identity']['selected_files'];counts={n:0 for n in OUTCOMES}  #: Derive qualified counts from actual validated receipts, not claimed totals.
    if set(ledger['shards'])-set(selected):errors.append({'module':None,'error':'Unexpected module in evidence selection'})  #: Extra module records cannot stand in for a missing selected source.
    for name,record in ledger['shards'].items():  #: Inspect all earlier successful modules again before a final or resumed success.
        if record.get('status')!='completed':continue  #: Failure/timeout/partial records remain nonpassing without pretending their evidence is complete.
        try:  #: Collect integrity defects so the parent can preserve a useful failed checkpoint.
            if name not in selected or record['test_sha256']!=selected[name] or Path(record['test_file']).name!=name:raise ValueError('Evidence selected-source identity changed')  #: Bind the module record to the originally selected source hash and filename.
            proof=verify_record(output,record)  #: Re-read exact log/receipt bytes after subsequent modules have run.
            for case in proof['cases']:counts[case['outcome']]+=1  #: Count each genuinely validated top-level case exactly once.
        except (OSError,ValueError,KeyError,TypeError) as error:errors.append({'module':name,'error':str(error)})  #: Missing/changed/malformed proof cannot retain an unqualified success label.
    if require_complete and (set(ledger['shards'])!=set(selected) or any(r.get('status')!='completed' for r in ledger['shards'].values())):errors.append({'module':None,'error':'Incomplete selected evidence'})  #: A partial selection cannot pass the independent full-profile audit.
    if require_complete and counts!=ledger.get('counts'):errors.append({'module':None,'error':'Evidence aggregate counts changed'})  #: Detect forged or stale ledger totals independently of its success flag.
    return {'valid':not errors,'qualified_counts':counts,'errors':errors}  #: Keep actual evidence integrity distinct from test-function outcomes and physical accuracy.


def audit_profile(output):  #: Provide a read-only post-run/package audit with no test execution or evidence repair.
    output=Path(output).resolve();ledger=json.loads((output/'profile.json').read_text(encoding='utf-8'))  #: Read the actual delivered ledger without locking/writing or launching children.
    if ledger.get('format')!=FORMAT or ledger.get('status')!='completed' or ledger.get('successful') is not True or ledger.get('complete') is not True:raise ValueError('Audit requires a completed current-format profile')  #: Old, partial, failed or truthy-string success markers do not qualify as a current intact run.
    for name,expected in ledger['identity']['source_sha256'].items():  #: Recheck actual delivered source bytes independently of historical absolute test-root paths.
        relative=Path(name);path=(ROOT/relative).resolve()  #: Keep source comparison rooted at this checkout.
        if relative.is_absolute() or '..' in relative.parts or not path.is_relative_to(ROOT.resolve()) or digest(path)!=expected:raise ValueError('Audit source bytes changed')  #: Refuse escaped or changed implementation/test inputs without requiring the old scratch location to exist.
    result=audit_ledger(output,ledger,True)  #: Require every originally selected module, full summaries and independently derived counts.
    if not result['valid']:raise ValueError('Evidence audit failed: '+json.dumps(result['errors']))  #: Return a failure without changing ledger status, timestamps or recorded hashes.
    return result  #: A successful audit proves intact bounded evidence, not FEM accuracy or resistance to a malicious local test.


def stop_process(process):  #: Bound cleanup for real child work, including POSIX subprocess descendants.
    if process.poll() is not None: return  #: An already reaped process needs no signal.
    try:  #: Allow a child that exits during the polling-to-signal race to be reaped normally.
        if os.name == 'posix': os.killpg(process.pid, signal.SIGTERM)  #: Keep native workers/server descendants in the isolated shard's process group.
        else: process.terminate()  #: Direct-child Windows cleanup exists but descendant behavior is not qualified here.
    except ProcessLookupError: process.wait(); return  #: Do not turn a natural exit into a leaking supervisor exception.
    try: process.wait(timeout=1)  #: Give ordinary cleanup a small explicit grace interval.
    except subprocess.TimeoutExpired:  #: Escalate only after a genuinely unresponsive child exceeds the grace period.
        if os.name == 'posix': os.killpg(process.pid, signal.SIGKILL)  #: Reap a stuck POSIX group instead of leaving a native worker running.
        else: process.kill()  #: Stop the direct child on other platforms without claiming full process-tree qualification.
        process.wait()  #: Observe actual process termination before returning a cancellation/timeout record.


def run_shard(path, directory, timeout, cancel):  #: Supervise one actual test module and preserve complete diagnostics on every outcome.
    token = uuid.uuid4().hex; attempt = directory/(path.stem+'_'+token); attempt.mkdir()  #: Use unique attempt paths, including after an interrupted parent's resume.
    log, receipt = attempt/'output.log', attempt/'receipt.json'  #: Never overwrite a previous attempt's logs or partial evidence.
    record = {'token':token,'test_file':str(path),'test_sha256':digest(path),'log':str(log.relative_to(directory)),'receipt':str(receipt.relative_to(directory)),'status':'running'}  #: Bind this attempt's source and output identity before launching native code.
    record.update(capture([sys.executable,str(ROOT/'verification/unittest_worker.py'),str(path),str(receipt),token],ROOT,log,timeout,cancel))  #: Observe actual child exit plus complete bounded parent-owned pipe transport before validating evidence.
    reason=record['status'] if record['status']!='unverified' else None  #: Keep timeout, cancellation and output-open/limit failures nonpassing.
    record['log_sha256'] = digest(log)  #: Tie raw diagnostics to the durable attempt record.
    if not reason:  #: A timeout/cancellation remains nonpassing even if a receipt appeared during cleanup.
        try:  #: Validate exact completion evidence only after observing child exit.
            proof = validate_receipt(receipt,record); record.update(receipt_sha256=digest(receipt),cases=proof['cases'],unittest_events=proof['summary'],discovered_cases=len(proof['expected_ids']),executed_cases=proof['tests_run'])  #: Preserve case and fixture/subtest accounting separately while binding exact receipt bytes.
            record['status'] = ('completed' if proof['successful'] else 'failed') if record['returncode'] == (0 if proof['successful'] else 1) else 'crashed'  #: Require process exit and unittest success/failure to agree.
        except (OSError,ValueError,KeyError,TypeError) as error: record.update(status='crashed' if record['returncode'] else 'unverified',error=str(error))  #: Missing/malformed/stale evidence never becomes a pass, even after exit0.
    return record  #: Return a complete observed outcome; no partial test result is promoted to success.


def _run_locked_profile(test_root, output, timeout=90, max_shards=0, resume=False, cancel=None):  #: Execute a profile only while its wrapper owns the output writer lock.
    if not math.isfinite(timeout) or not .05 <= timeout <= 600 or type(max_shards) is not int or max_shards < 0: raise ValueError('Use finite timeout 0.05–600 s and nonnegative max_shards')  #: Reject invalid resource settings before creating evidence.
    test_root, output = Path(test_root).resolve(), Path(output).resolve()  #: Normalize caller-selected local test/output locations once.
    files = sorted(test_root.glob('test_*.py')); identity = fingerprint(test_root,files)  #: Select every actual unittest source module without importing native packages in the supervisor.
    if not files: raise ValueError('No test_*.py modules selected')  #: Empty discovery is never a successful verification run.
    ledger_path = output/'profile.json'  #: Keep one atomically updated durable checkpoint per explicit output directory.
    if resume:  #: Resume only evidence tied to the exact same code/environment/test selection.
        ledger = json.loads(ledger_path.read_text(encoding='utf-8'))  #: Missing or malformed previous state is an explicit failure.
        if ledger.get('format') != FORMAT or ledger.get('identity') != identity or ledger.get('timeout_s') != timeout: raise ValueError('Resume source/environment/budget mismatch')  #: Never reuse an old passing result after code or profile changes.
        if ledger.get('status') not in ('paused','completed'): raise ValueError('Resume only intentionally paused or completed profiles; use a new output after failure, cancellation or unknown interruption')  #: Do not hide a failed/flaky or unobserved attempt behind a later automatic retry.
        audit=audit_ledger(output,ledger)  #: Recheck all earlier actual module bytes/case summaries before any resume credit.
        if not audit['valid']:raise ValueError('Resume evidence changed: '+json.dumps(audit['errors']))  #: Preserve prior evidence instead of silently repairing or retrying it.
    else:  #: A fresh run never clobbers an earlier accepted profile.
        if output.exists() and any(p.name!='.profile.lock' for p in output.iterdir()): raise ValueError('Output is not empty; use explicit --resume or a new directory')  #: Ignore only the held lock file while preserving every previous profile/log/result on accidental reuse.
        output.mkdir(parents=True,exist_ok=True); ledger={'format':FORMAT,'identity':identity,'timeout_s':timeout,'shards':{},'attempt_history':[]}  #: Establish a finite source-bound profile before executing tests.
    ledger.update(status='running',successful=False,complete=False); atomic_json(ledger_path,ledger)  #: A parent crash leaves visible incomplete state, not the previous success label.
    count = 0  #: Bound the number of actual new shards in this invocation for restartable long verification work.
    for path in files:  #: Run deterministically in source filename order.
        if ledger['shards'].get(path.name,{}).get('status') == 'completed': continue  #: Reuse only completion evidence already verified against source, logs and observed exit.
        if (cancel and cancel()) or (max_shards and count >= max_shards): break  #: Pause between modules without pretending all selected tests ran.
        ledger['shards'][path.name]={'status':'running','test_file':str(path)}; atomic_json(ledger_path,ledger)  #: Record an outstanding module before launch, so an interrupted parent cannot certify the profile.
        record = run_shard(path,output,timeout,cancel); ledger['shards'][path.name]=record; ledger['attempt_history'].append(record); count+=1  #: Preserve every actual attempt and never overwrite old attempt files.
        atomic_json(ledger_path,ledger)  #: Make each observed module completion durable before moving to the next one.
        if record['status'] == 'cancelled': break  #: Respect cancellation without starting further test work.
    counts = {name:0 for name in OUTCOMES}  #: Count actual top-level case outcomes, not discovered names or log text.
    for record in ledger['shards'].values():  #: Keep partial/failing profiles explicit while still reporting observed executed cases.
        for case in record.get('cases',[]): counts[case['outcome']]+=1  #: Do not count skips or expected failures as clean passes.
    audit=audit_ledger(output,ledger);ledger['integrity_audit']=audit  #: Recheck every completed earlier module immediately before computing final/paused success.
    for error in audit['errors']:  #: Preserve concrete integrity failures without rewriting content hashes or claimed original case outcomes.
        if error['module'] in ledger['shards']:ledger['shards'][error['module']]['status']='evidence_changed'  #: Invalidated evidence cannot remain a completed reusable module.
    complete = audit['valid'] and len(ledger['shards'])==len(files) and all(r['status']=='completed' for r in ledger['shards'].values())  #: Completion requires observed successful exit and valid receipts for every selected source module.
    unchanged = fingerprint(test_root,files)==identity  #: Detect a test or concurrent edit changing relevant source/environment during execution.
    cancelled = any(r['status']=='cancelled' for r in ledger['shards'].values()) or bool(cancel and cancel())  #: Keep actual cancellation separate from an intentional max-shard pause.
    bad = any(r['status'] not in ('completed','running') for r in ledger['shards'].values())  #: Any failed/crashed/timed-out/unverified shard prevents success.
    ledger.update(counts=counts,complete=complete and unchanged,successful=complete and unchanged,status='evidence_changed' if not audit['valid'] else 'source_changed' if not unchanged else 'cancelled' if cancelled else 'completed' if complete else 'failed' if bad else 'paused')  #: Never expose a success state for partial or changed-source verification.
    atomic_json(ledger_path,ledger); return ledger  #: Persist final or resumable state with all exact diagnostic evidence.


@contextmanager  #: Keep cleanup exception-safe across normal completion, pauses and failed setup.
def profile_lock(output):  #: Prevent two ordinary supervisors from overwriting the same evidence checkpoint concurrently.
    if os.name!='posix': raise ValueError('Verification writer locking is qualified on POSIX only; Windows runner qualification pending')  #: Do not claim untested Windows locking/process-tree behavior; application runtime is unaffected.
    import fcntl  #: Use the standard POSIX kernel lock, released automatically if the parent process exits.
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)  #: Prepare only the explicit verification output directory.
    with (output/'.profile.lock').open('a+') as handle:  #: Keep a stable lock inode; deleting it could let two writers lock different files.
        try: fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)  #: Refuse a concurrent writer immediately instead of blocking automation indefinitely.
        except BlockingIOError: raise ValueError('Verification output is already locked by another supervisor')  #: Preserve the active writer's ledger and attempt files.
        try: yield  #: Hold the kernel lock across all profile reads, shard execution and checkpoint writes.
        finally: fcntl.flock(handle.fileno(),fcntl.LOCK_UN)  #: Release the writer lock on every ordinary exit path.


def run_profile(test_root, output, timeout=90, max_shards=0, resume=False, cancel=None):  #: Run/resume only with exclusive ownership of the evidence directory.
    with profile_lock(output): return _run_locked_profile(test_root,output,timeout,max_shards,resume,cancel)  #: Keep the public programmatic/CLI entry point source-bound and concurrency-safe.


def main():  #: Expose the same supervised verification implementation as a source command.
    parser=argparse.ArgumentParser(description='Isolated resumable unittest verification; no numerical accuracy/parity certification')  #: State that test execution evidence is not a physical validation claim.
    parser.add_argument('--test-root',type=Path,default=ROOT/'tests'); parser.add_argument('--output',type=Path,required=True); parser.add_argument('--timeout',type=float,default=90); parser.add_argument('--max-shards',type=int,default=0); parser.add_argument('--resume',action='store_true')  #: Keep all source, budget, output and reuse choices explicit.
    parser.add_argument('--audit',action='store_true')  #: Check an existing completed profile without running tests, taking a writer lock or changing any file.
    args=parser.parse_args()  #: Refuse unknown CLI switches before starting any work.
    if args.audit:  #: A read-only evidence check must never resume or silently rerun selected tests.
        if args.resume or args.max_shards or args.test_root!=ROOT/'tests':parser.error('--audit cannot change selection or resume a run')  #: Keep audit semantics distinct from execution options.
        try:print(json.dumps(audit_profile(args.output),indent=2));return 0  #: Report independently checked counts only for an intact current-source profile.
        except (OSError,ValueError,KeyError,TypeError) as error:print(str(error),file=sys.stderr);return 1  #: Invalid/missing/changed evidence fails without any mutation or success repair.
    try: ledger=run_profile(args.test_root,args.output,args.timeout,args.max_shards,args.resume)  #: Execute real isolated tests and source-bound evidence validation.
    except (OSError,ValueError) as error: print(str(error),file=sys.stderr); return 1  #: Report setup/resume errors without erasing previous accepted profile files.
    print(json.dumps({'status':ledger['status'],'successful':ledger['successful'],'counts':ledger['counts'],'qualified_counts':ledger['integrity_audit']['qualified_counts'],'profile':str(args.output/'profile.json')},indent=2))  #: Show actual executed outcomes and where exact evidence is retained.
    return 0 if ledger['successful'] else 2 if ledger['status']=='paused' else 130 if ledger['status']=='cancelled' else 1  #: Exit0 is reserved for a fully completed unchanged-source profile.


if __name__ == '__main__':  #: Keep importing verification helpers free of test execution.
    raise SystemExit(main())  #: Propagate actual complete/pause/failure/cancellation status to automation/CI.
