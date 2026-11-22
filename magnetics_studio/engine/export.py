"""Portable VTK and CSV exports (no third-party code)."""
import csv
import io
import json
from .mesh import dot


def field_csv(result):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    header = ['element','region','x_m','y_m','z_m','Bx_T','By_T','Bz_T','Bmag_T','Hx_A_per_m','Hy_A_per_m','Hz_A_per_m','volume_m3']  #: Build the existing spatial field-column order before adding analysis-specific data.
    if result.get('ac'):  #: Apply the following export additions only to actual AC results; ordinary static exports retain their schema.
        header = [name.replace('_T','_snapshot_T').replace('_A_per_m','_snapshot_A_per_m') if name.startswith(('B','H')) else name for name in header]  #: Label generic B/H components explicitly as instantaneous snapshots in AC CSV files.
        header += ['frequency_Hz','snapshot_phase_deg','B_rms_norm_T','Jz_rms_real_Apm2','Jz_rms_imag_Apm2','ohmic_loss_density_Wpm3']  #: Add solved frequency, observation phase, RMS norms, axial current phasors and average loss-density columns.
        header += [field+'_'+part+'_rms_'+unit for field,unit in [('B','T'),('H','Apm')] for part in ['x_real','y_real','z_real','x_imag','y_imag','z_imag']]  #: Generate explicit real/imaginary RMS B and H component column names in the same order as their data.
    writer.writerow(header)  #: Emit the complete validated analysis-specific CSV header once.
    mesh = result['mesh']
    for i,(e,b,h,vol,tag) in enumerate(zip(mesh['elements'],result['fields']['B'],result['fields']['H'],result['fields']['measures'],mesh['tags'])):
        center = [sum(mesh['nodes'][n][k] for n in e)/len(e) for k in range(mesh['dimension'])]
        if len(center)==2:
            center.append(0.)
        region = result['project']['regions'][tag]['name'] if tag>=0 else 'Background air'
        row = [i,region,*center,*b,dot(b,b)**.5,*h,vol]  #: Start each row with the same geometry, instantaneous fields and effective volume as ordinary exports.
        if result.get('ac'):  #: Apply the following export additions only to actual AC results; ordinary static exports retain their schema.
            ph = result['fields']['phasor']  #: Resolve the complete complex-field data without recomputing or discarding phase.
            row += [result['ac']['settings']['frequency_Hz'],result['ac']['settings']['phase_deg'],ph['B_rms_magnitude_T'][i],ph['Jz_real'][i],ph['Jz_imag'][i],ph['ohmic_loss_density_Wpm3'][i]]  #: Append run settings, RMS B norm, axial current components and exactly integrated element-average Joule density.
            row += [value for field in ['B','H'] for part in ['real','imag'] for value in ph[field+'_'+part][i]]  #: Flatten B/H real and imaginary components in exactly the order declared by the CSV header.
        writer.writerow(row)  #: Write one physical element's complete data into the CSV stream.
    return stream.getvalue()


def vtk(result):
    mesh = result['mesh']
    nodes,elements = mesh['nodes'],mesh['elements']
    dim = mesh['dimension']
    lines = ['# vtk DataFile Version 3.0','Magnetics Studio FEM','ASCII','DATASET UNSTRUCTURED_GRID',f'POINTS {len(nodes)} double']
    if result.get('ac'):  #: Make standalone VTK snapshots identifiable without the source JSON file.
        lines[1] = 'Magnetics Studio AC RMS phasors; snapshot phase '+str(result['ac']['settings']['phase_deg'])+' deg; frequency '+str(result['ac']['settings']['frequency_Hz'])+' Hz'  #: Record the observation phase and solved frequency in the VTK title.
    for p in nodes:
        lines.append(' '.join(str(v) for v in (list(p)+[0.] if dim==2 else p)))
    lines.append(f'CELLS {len(elements)} {sum(len(e)+1 for e in elements)}')
    lines.extend(str(len(e))+' '+' '.join(map(str,e)) for e in elements)
    lines.append(f'CELL_TYPES {len(elements)}')
    lines.extend([str(5 if dim==2 else 10)]*len(elements))
    lines.append(f'CELL_DATA {len(elements)}')
    lines.append('VECTORS B_snapshot_T double' if result.get('ac') else 'VECTORS B_T double')  #: Give the generic VTK B field a snapshot label for AC while preserving the static name otherwise.
    lines.extend(' '.join(str(v) for v in b) for b in result['fields']['B'])
    lines.append('VECTORS H_snapshot_A_per_m double' if result.get('ac') else 'VECTORS H_A_per_m double')  #: Give the generic VTK H field an instantaneous label without changing ordinary static export names.
    lines.extend(' '.join(str(v) for v in h) for h in result['fields']['H'])
    lines.extend(['SCALARS region_id int 1','LOOKUP_TABLE default'])
    lines.extend(map(str,mesh['tags']))
    if result.get('ac'):  #: Apply the following export additions only to actual AC results; ordinary static exports retain their schema.
        for key in ['B_real','B_imag','H_real','H_imag']:  #: Export separate real and imaginary RMS magnetic vector arrays.
            lines.append('VECTORS '+key+'_rms double')  #: Declare each extra RMS vector array using standard VTK syntax.
            lines.extend(' '.join(str(v) for v in vector) for vector in result['fields']['phasor'][key])  #: Write all three components of each element's stored RMS phasor part.
        for key in ['Jz_real','Jz_imag','ohmic_loss_density_Wpm3']:  #: Export real/imaginary axial current and averaged loss as independent cell scalar arrays.
            lines.extend(['SCALARS '+key+' double 1','LOOKUP_TABLE default'])  #: Declare one scalar field and its VTK lookup table.
            lines.extend(map(str,result['fields']['phasor'][key]))  #: Write the stored scalar values without replacing integrated loss by a cell-centre approximation.
    if 'Az' in result['fields']:
        lines.extend([f'POINT_DATA {len(nodes)}','SCALARS Az_snapshot_Wb_per_m double 1' if result.get('ac') else 'SCALARS Az_Wb_per_m double 1','LOOKUP_TABLE default'])  #: Label the nodal Az array as a snapshot in AC files while preserving existing static scalar naming.
        lines.extend(map(str,result['fields']['Az']))
    return '\n'.join(lines)+'\n'


def report_html(result):
    """Self-contained read-only field viewer; all plots use solved FEM data."""
    from pathlib import Path
    import html
    import re
    summary = {k:result[k] for k in ['stats','windings','inductance_H','regions','warnings']}
    if result.get('adaptive'):
        summary['adaptive'] = result['adaptive']
    if result.get('ac'):  #: Apply the following export additions only to actual AC results; ordinary static exports retain their schema.
        summary['ac'] = result['ac']  #: Keep source phasors, port definitions, average power and physical balance in the offline report summary.
    values = {'DATA':json.dumps(result,allow_nan=False).replace('<','\\u003c'),
              'NAME':html.escape(result['project']['name']),
              'SUMMARY':html.escape(json.dumps(summary,indent=2)),
              'CAD_SCRIPT':(Path(__file__).resolve().parents[1]/'web'/'cad-view.js').read_text(encoding='utf-8'),
              'FIELD_SCRIPT':(Path(__file__).resolve().parents[1]/'web'/'field-view.js').read_text(encoding='utf-8')}
    template = (Path(__file__).resolve().parents[1]/'web'/'report.html').read_text(encoding='utf-8')
    return re.sub(r'@@(DATA|NAME|SUMMARY|CAD_SCRIPT|FIELD_SCRIPT)@@',lambda m:values[m.group(1)],template)


def write_report(result, path):
    from pathlib import Path
    Path(path).write_text(report_html(result),encoding='utf-8')
