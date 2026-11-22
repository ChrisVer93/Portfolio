"""Requirements-driven two-winding transformer candidates using pinned OpenMagnetics."""
import copy  #: Preserve source requirements and externally supplied waveform data.
import hashlib  #: Bind catalogue metadata and generated designs to exact selected data.
from importlib import metadata  #: Detect the optional compiled dependency without importing it in the GUI server.
import json  #: Serialize finite source/model provenance and stable catalogue identity.
import math  #: Integrate explicit piecewise-linear excitation data and check finite component results.
from .project import number  #: Reuse strict finite scalar validation and boolean rejection.
FORMAT='magnetics-studio.transformer-design/1'  #: Keep requirements synthesis distinct from original FEM/builder request schemas.
PIN='1.7.35'  #: Use the actual inspected and tested upstream component-model interface.


def target(value,label,lower,upper):  #: Validate an explicit minimum/nominal/maximum design band.
    if not isinstance(value,dict) or set(value)!={'minimum','nominal','maximum'}:raise ValueError(label+' requires minimum, nominal and maximum')  #: Reject hidden tolerances and silently dropped requirement fields.
    r={k:number(v,label+' '+k,lower,upper) for k,v in value.items()}  #: Retain native SI target values and explicit physical bounds.
    if not r['minimum']<=r['nominal']<=r['maximum'] or r['maximum']==r['minimum']:raise ValueError(label+' band must contain its nominal and have positive width')  #: Require a meaningful ordered feasible interval.
    return r  #: Keep the exact declared target rather than replacing it with a nominal-only search.


def waveform(value,frequency,label):  #: Validate one externally specified periodic piecewise-linear signal.
    if not isinstance(value,dict) or set(value)!={'time_s','values'}:raise ValueError(label+' requires time_s and values')  #: Distinguish explicit waveform data from invented processed descriptors.
    t=value['time_s'];y=value['values'];period=1/frequency  #: Interpret every winding on the same declared operating-point period.
    if not isinstance(t,list) or not isinstance(y,list) or not 3<=len(t)<=1025 or len(t)!=len(y):raise ValueError(label+' requires 3..1025 paired samples')  #: Bound processing memory and reject incomplete waveform axes.
    t=[number(x,label+' time',0,period*(1+1e-9)) for x in t];y=[number(v,label+' value',-1e5,1e5) for v in y]  #: Check every physical coordinate and signed voltage/current value before native execution.
    if t[0]!=0 or abs(t[-1]/period-1)>1e-9 or any(a>b for a,b in zip(t,t[1:])) or any(t[i]==t[i+1]==t[i+2] for i in range(len(t)-2)):raise ValueError(label+' must cover one period in nondecreasing time; at most two samples per jump')  #: Allow explicit switching discontinuities without reordered or ambiguous time data.
    mean=math.fsum((b-a)*(u+v)/2 for a,b,u,v in zip(t,t[1:],y,y[1:]))/period  #: Integrate signed volt-seconds/current bias independently of upstream waveform processing.
    rms=math.sqrt(math.fsum((b-a)*(u*u+u*v+v*v)/3 for a,b,u,v in zip(t,t[1:],y,y[1:]))/period)  #: Integrate the square of the actual piecewise-linear waveform exactly in each interval.
    return {'time_s':t,'values':y},dict(mean=mean,rms=rms,peak=max(abs(v) for v in y))  #: Keep explicit samples and independent physical waveform diagnostics together.


def validate_request(request):  #: Keep unsupported or inconsistent synthesis input out of the native worker.
    if not isinstance(request,dict) or set(request)!={'format','requirements','operating_points','limits','max_results'} or request['format']!=FORMAT:raise ValueError('Use complete '+FORMAT+' request')  #: Reject ambiguous schemas and ignored root options.
    r=copy.deepcopy(request);req=r['requirements'];limits=r['limits']  #: Detach all physical target and waveform arrays from later caller edits.
    if not isinstance(req,dict) or set(req)!={'magnetizing_inductance_H','turns_ratio','leakage_inductance_primary_H'}:raise ValueError('Declare Lm, Np/Ns and nullable primary-referred leakage bands')  #: Preserve exact winding-reference definitions and optional leakage intent.
    req['magnetizing_inductance_H']=target(req['magnetizing_inductance_H'],'Lm H',1e-9,10.);req['turns_ratio']=target(req['turns_ratio'],'Np/Ns',.01,1000.)  #: Validate positive primary-referred magnetising inductance and turns ratio.
    if req['leakage_inductance_primary_H'] is not None:req['leakage_inductance_primary_H']=target(req['leakage_inductance_primary_H'],'Primary leakage H',0.,1.)  #: Leave an omitted leakage target explicitly unrequested rather than assume zero.
    if not isinstance(limits,dict) or set(limits)!={'max_flux_density_T','max_total_loss_W','max_temperature_C','max_core_dimensions_m'}:raise ValueError('Declare B, total-loss, temperature and core-envelope limits')  #: Require every exposed physical limit to be explicit and recheckable.
    for key,low,high in [('max_flux_density_T',.001,2.),('max_total_loss_W',1e-6,1e6),('max_temperature_C',0.,250.)]:limits[key]=number(limits[key],key,low,high)  #: Validate finite model-screening limits with physical units.
    if not isinstance(limits['max_core_dimensions_m'],list) or len(limits['max_core_dimensions_m'])!=3:raise ValueError('Core width/height/depth require three SI values')  #: Keep core envelope separate from an unverified complete transformer bounding box.
    limits['max_core_dimensions_m']=[number(v,'Core dimension m',.001,2.) for v in limits['max_core_dimensions_m']]  #: Bound actual native core-width/height/depth checks.
    if type(r['max_results']) is not int or not 1<=r['max_results']<=5:raise ValueError('Use 1..5 returned design candidates')  #: Preserve a small explicit component-search/result budget.
    if not isinstance(r['operating_points'],list) or not 1<=len(r['operating_points'])<=4:raise ValueError('Supply 1..4 operating points')  #: Bound worst-case model re-evaluation work.
    names=set()  #: Reject ambiguous operating-point result identities.
    for op in r['operating_points']:  #: Check every complete winding excitation set before altering any accepted job.
        if not isinstance(op,dict) or set(op)!={'name','frequency_Hz','ambient_temperature_C','windings'}:raise ValueError('Each operating point needs name, frequency, ambient temperature and two windings')  #: Reject incomplete or ignored operating conditions.
        if not isinstance(op['name'],str) or not op['name'].strip() or len(op['name'])>80 or op['name'] in names:raise ValueError('Operating-point names must be unique bounded strings')  #: Retain stable per-point diagnostics and candidate checks.
        names.add(op['name']);op['frequency_Hz']=number(op['frequency_Hz'],'Frequency Hz',1000,1e6);op['ambient_temperature_C']=number(op['ambient_temperature_C'],'Ambient C',0,120)  #: Scope the initial adviser to explicit high-frequency component-model operating conditions.
        if op['ambient_temperature_C']>limits['max_temperature_C']:raise ValueError('Ambient temperature exceeds the declared temperature limit')  #: Reject an already impossible thermal condition rather than invoke a search.
        if not isinstance(op['windings'],list) or len(op['windings'])!=2:raise ValueError('This designer requires primary then secondary excitation data')  #: Make the first implementation’s two-winding ownership explicit.
        for i,winding in enumerate(op['windings']):  #: Keep each winding’s current/voltage orientation and waveform data independent.
            if not isinstance(winding,dict) or set(winding)!={'voltage','current'}:raise ValueError('Each winding requires explicit voltage and current waveforms')  #: Never infer missing excitation from rated power alone.
            for kind in ['voltage','current']:  #: Validate and preserve both externally specified signals.
                winding[kind],stats=waveform(winding[kind],op['frequency_Hz'],op['name']+' winding '+str(i)+' '+kind)  #: Use the actual SI samples and switching jumps.
                if kind=='voltage' and (stats['rms']==0 or abs(stats['mean'])>max(1e-9,stats['peak']*1e-5)):raise ValueError('This initial transformer designer requires nonzero balanced winding volt-seconds')  #: Reject unsupported DC terminal-voltage models instead of guessing core reset.
    return r  #: Return complete detached requirements with no automatic physical changes.


def mas_inputs(request):  #: Map declared requirements and all operating-point samples to the native MAS input structure.
    r=validate_request(request);q=r['requirements'];requirements=dict(magnetizingInductance=q['magnetizing_inductance_H'],turnsRatios=[q['turns_ratio']],insulation={'insulationType':'Functional','pollutionDegree':'P2','overvoltageCategory':'OVC-II'})  #: Declare nominal functional insulation screening explicitly, without a safety-compliance claim.
    if q['leakage_inductance_primary_H'] is not None:requirements['leakageInductance']=[q['leakage_inductance_primary_H']]  #: Pass the primary-referred leakage band into candidate generation as well as the final gate.
    ops=[]  #: Preserve operating-point order and two independent winding excitations.
    for op in r['operating_points']:  #: Include every user-selected operating corner in the native problem.
        excitations=[]  #: Keep winding order primary then secondary throughout the adapter.
        for name,w in zip(['Primary','Secondary'],op['windings']):  #: Bind stable winding identities independently of display names in an existing FEM project.
            e=dict(name=name,frequency=op['frequency_Hz'])  #: Use the same explicit common period for both winding waveforms.
            for kind in ['voltage','current']:e[kind]={'waveform':{'time':w[kind]['time_s'],'data':w[kind]['values']}}  #: Transfer exact native waveform samples with no RMS/peak conversion or phase assumption.
            excitations.append(e)  #: Preserve both complete physical waveform definitions.
        ops.append(dict(name=op['name'],conditions={'ambientTemperature':op['ambient_temperature_C']},excitationsPerWinding=excitations))  #: Preserve operating temperature and corner identity.
    return r,dict(designRequirements=requirements,operatingPoints=ops)  #: Return exact Studio and native input provenance side by side.


def _value(value,label,minimum=0.):  #: Reject missing/nonfinite native model values instead of replacing them with zero.
    return float(number(value,label,minimum,1e12))  #: Keep scalar physical output bounded and JSON-finite.


def _check(name,value,low,high):  #: Represent every explicit numerical gate in independently inspectable form.
    return dict(name=name,value=value,minimum=low,maximum=high,passed=low<=value<=high)  #: Preserve unfavorable values and exact pass/fail decisions.


def recheck(om,item,processed,request):  #: Re-simulate and independently call the native inductance APIs on each returned candidate.
    magnetic=copy.deepcopy(item['mas']['magnetic']);simulated=om.simulate(processed,magnetic,{'coreLosses':'IGSE','reluctance':'ZHANG'})  #: Use the actually tested inputs-first API order, contrary to the pinned function’s misleading docstring.
    outputs=simulated['outputs'];magnetic=simulated['magnetic'];coil=magnetic['coil'];windings=coil['functionalDescription'];q=request['requirements'];limits=request['limits'];checks=[];points=[]  #: Inspect the actual fully processed component and all simulated operating points.
    if len(windings)!=2 or len(outputs)!=len(processed['operatingPoints']):raise ValueError('Native candidate has incomplete winding or operating-point outputs')  #: Reject silently omitted physical conditions.
    turns=[w['numberTurns'] for w in windings]  #: Retain native integer physical turn choices and independent parallel counts.
    if any(type(n) is not int or not 1<=n<=10000 for n in turns):raise ValueError('Native candidate has invalid turn counts')  #: Reject invalid or fractional generated winding turns.
    ratio=turns[0]/turns[1];checks.append(_check('Np/Ns',ratio,q['turns_ratio']['minimum'],q['turns_ratio']['maximum']))  #: Recheck the actual generated turns ratio rather than the requested ratio.
    fit=om.are_sections_and_layers_fitting(coil);checks.append(dict(name='Native nominal winding fit',value=bool(fit),passed=fit is True))  #: Require the generated sections/layers to fit their actual native bobbin window.
    bounds=[_value(magnetic['core']['processedDescription'][k],'Core '+k,1e-12) for k in ['width','height','depth']]  #: Read actual native core-only SI envelope dimensions.
    for name,value,limit in zip(['Core width m','Core height m','Core depth m'],bounds,limits['max_core_dimensions_m']):checks.append(_check(name,value,0,limit))  #: Check every explicitly declared core-envelope limit.
    for op,out,user in zip(processed['operatingPoints'],outputs,request['operating_points']):  #: Re-evaluate every actual user operating corner.
        lm=_value(om.calculate_inductance_from_number_turns_and_gapping(magnetic['core'],coil,op,{'reluctance':'ZHANG'}),'Lm H',1e-15);reported=_value(out['inductance']['magnetizingInductance']['magnetizingInductance']['nominal'],'Reported Lm H',1e-15)  #: Compare a separate direct reluctance call with the re-simulated component output.
        leakage=om.calculate_leakage_inductance(magnetic,user['frequency_Hz'],0);lp=_value(leakage['leakageInductancePerWinding'][1]['nominal'],'Primary-referred leakage H')  #: Explicitly select source winding zero and target winding one.
        reverse=om.calculate_leakage_inductance(magnetic,user['frequency_Hz'],1);ls=_value(reverse['leakageInductancePerWinding'][0]['nominal'],'Secondary-referred leakage H')  #: Independently repeat the reverse referral to check actual Np/Ns squared scaling.
        referral=abs(lp-ratio**2*ls)/max(lp,ratio**2*ls,1e-30);inductance_agreement=abs(lm/reported-1)  #: Record physical referral and model-call agreement rather than assuming the docstring convention.
        b=out['coreLosses']['magneticFluxDensity']['processed'];peak=max(abs(_value(b[k],'B '+k,-1e12)) for k in ['positivePeak','negativePeak','peak'])  #: Preserve the largest absolute native core-flux excursion across both polarities.
        core_loss=_value(out['coreLosses']['coreLosses'],'Core loss W');copper_loss=_value(out['windingLosses']['windingLosses'],'Winding loss W');temperature=_value(out['temperature']['maximumTemperature'],'Model temperature C',-273.15)  #: Require genuine finite component-model loss and thermal outputs.
        prefix=user['name']+' / ';checks.extend([_check(prefix+'Lm H',lm,q['magnetizing_inductance_H']['minimum'],q['magnetizing_inductance_H']['maximum']),_check(prefix+'Resimulated Lm H',reported,q['magnetizing_inductance_H']['minimum'],q['magnetizing_inductance_H']['maximum']),_check(prefix+'Leakage referral error',referral,0,1e-5),_check(prefix+'Peak B T',peak,0,limits['max_flux_density_T']),_check(prefix+'Total loss W',core_loss+copper_loss,0,limits['max_total_loss_W']),_check(prefix+'Model temperature C',temperature,-273.15,limits['max_temperature_C'])])  #: Gate both native Lm evaluations against the actual requested band and preserve every per-corner failed estimate.
        if q['leakage_inductance_primary_H'] is not None:checks.append(_check(prefix+'Primary leakage H',lp,q['leakage_inductance_primary_H']['minimum'],q['leakage_inductance_primary_H']['maximum']))  #: Gate every requested leakage band at every supplied frequency.
        points.append(dict(name=user['name'],frequency_Hz=user['frequency_Hz'],magnetizing_inductance_H=lm,resimulated_magnetizing_inductance_H=reported,relative_native_Lm_difference=inductance_agreement,leakage_inductance_primary_H=lp,leakage_inductance_secondary_H=ls,referral_relative_error=referral,peak_flux_density_T=peak,core_loss_W=core_loss,winding_loss_W=copper_loss,total_loss_W=core_loss+copper_loss,model_temperature_C=temperature))  #: Retain all calculated physical metrics with exact operating-point ownership.
    core=magnetic['core']['functionalDescription'];identity=hashlib.sha256(json.dumps(magnetic,sort_keys=True,allow_nan=False).encode()).hexdigest()  #: Bind candidate identity to the actual generated core/gap/winding specification.
    return dict(id=identity[:16],sha256=identity,core_shape=core['shape']['name'],core_material=core['material']['name'],turns=turns,parallels=[w['numberParallels'] for w in windings],wires=[w['wire'] for w in windings],gaps=core['gapping'],core_dimensions_m=bounds,layout_counts={k:len(coil.get(k) or []) for k in ['sectionsDescription','layersDescription','turnsDescription']},checks=checks,passes_component_checks=all(c['passed'] for c in checks),operating_points=points,worst_total_loss_W=max(p['total_loss_W'] for p in points),mas=simulated,upstream_score=item.get('scoring'))  #: Return a complete rechecked generated design, preserving failures and neutral MAS data.


def design(request):  #: Generate and recheck real bounded OpenMagnetics transformer candidates from physical requirements.
    request,inputs=mas_inputs(request)  #: Apply the same strict preflight contract at direct/native worker boundaries.
    if metadata.version('PyOpenMagnetics')!=PIN:raise ValueError('Transformer designer requires PyOpenMagnetics=='+PIN)  #: Never silently substitute an unqualified native version.
    import PyOpenMagnetics as om  #: Keep all compiled catalogue/model state inside the isolated worker.
    om.load_databases({});om.set_settings({'useOnlyCoresInStock':False,'useToroidalCores':False,'usePowderCores':False,'useConcentricCores':True,'coreAdviserIncludeStacks':False,'coilAdviserMaximumNumberWires':3,'coreAdviserMaximumMagneticsAfterFiltering':8})  #: Declare a bounded standard concentric ferrite search, not an exhaustive global optimisation or stock check.
    shapes=om.get_core_shapes();materials=om.get_core_materials();bobbins=om.get_bobbins();wires=om.get_wires()  #: Use the actual installed upstream catalogues without copying a full database into Studio.
    index=dict(shapes=sorted(s['name'] for s in shapes),materials=sorted(m['name'] for m in materials),bobbins=sorted(str(b.get('name')) for b in bobbins),wires=sorted(w['name'] for w in wires))  #: Fingerprint the resolved catalogue identity independently of candidate selection.
    catalogue=dict(provider='PyOpenMagnetics embedded catalogue',version=PIN,counts={k:len(v) for k,v in index.items()},name_index_sha256=hashlib.sha256(json.dumps(index,sort_keys=True).encode()).hexdigest(),stock_availability_checked=False,scope='Standard concentric ferrite shapes; no toroids, powder cores or stacked cores')  #: Report actual database provenance and supported search scope without a purchasing/availability claim.
    processed=om.process_inputs(inputs);print('Processed '+str(len(processed['operatingPoints']))+' waveform operating points; running bounded native adviser',flush=True)  #: Compute real harmonics and preserve exact input/processed provenance.
    advised=om.calculate_advised_magnetics(processed,request['max_results'],'standard cores');candidates=[];errors=[]  #: Invoke the actual full native design adviser, not a hand-written inductance-only surrogate.
    for i,item in enumerate(advised.get('data',[])):  #: Recheck each returned generated magnetic component separately.
        try:candidates.append(recheck(om,item,processed,request))  #: Preserve failed numerical gates alongside passing re-simulated designs.
        except Exception as error:errors.append(dict(index=i,error=str(error)))  #: Keep model/data failures explicit rather than replace missing results with zeros.
    candidates.sort(key=lambda c:(not c['passes_component_checks'],c['worst_total_loss_W'],c['id']));passed=sum(c['passes_component_checks'] for c in candidates)  #: Rank passing candidates first, then by worst supplied-corner estimated total loss within this limited pool.
    return dict(kind='transformer_design',format='magnetics-studio.transformer-design-result/1',request=request,processed_inputs=processed,catalogue=catalogue,settings=om.get_settings(),models={'coreLosses':'IGSE','reluctance':'ZHANG'},candidates=candidates,candidate_errors=errors,passed_count=passed,status='component_candidates_found' if passed else 'no_candidate_met_checked_requirements',method='OpenMagnetics adviser and component-model recheck; not FEM',limitations=['Bounded two-winding catalogue search; no guarantee of a global optimum or a feasible design outside the searched pool','Functional insulation screening only; safety compliance, manufacturing clearance and complete transformer envelope are unqualified','Component-model flux/loss/temperature estimates; no new FEM, hardware or Maxwell validation','Candidate MAS and original Studio FEM geometry are separate; no automatic overwrite or matched FEM conversion','Catalogue/transitive redistribution audit and final Windows packaging remain pending'])  #: Publish finite generated designs, every checked requirement and all material remaining qualification limits.
