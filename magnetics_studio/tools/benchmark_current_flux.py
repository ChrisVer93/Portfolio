"""Measure flux conservation and analytical-field convergence on solved DC cases."""
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.current_flux import reconstruct_current
from engine.dc_conduction import solve_dc
from engine.mesh import dot, sub, tetra_geometry

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    sector = json.loads((ROOT/'sample_results/dc_conduction/sector.json').read_text())
    series = []
    for n in (4,8,16,32):
        result = solve_dc(dict(sector,cells=[n,n//2,2]))
        recovered = reconstruct_current(result)
        exact_norm, raw_error, projected_error = [], [], []
        for t, j, k in zip(result['mesh']['tetrahedra'], result['current_density_A_m2'],
                           recovered['current_density_at_cell_centroid_A_m2']):
            points = [result['mesh']['nodes_m'][i] for i in t]
            x, y = (sum(p[d] for p in points)/4 for d in (0,1))
            scale = sector['conductivity_S_m']*sector['voltage_V']/sector['angle_rad']
            exact = (-scale*y/(x*x+y*y), scale*x/(x*x+y*y), 0.)
            volume, _ = tetra_geometry(points)
            exact_norm.append(volume*dot(exact,exact))
            raw_error.append(volume*dot(sub(j,exact),sub(j,exact)))
            projected_error.append(volume*dot(sub(k,exact),sub(k,exact)))
        denominator = math.fsum(exact_norm)
        series.append(dict(cells=[n,n//2,2],tetrahedra=len(result['mesh']['tetrahedra']),
                           raw_relative_centroid_error=math.sqrt(math.fsum(raw_error)/denominator),
                           projected_relative_centroid_error=math.sqrt(math.fsum(projected_error)/denominator),
                           correction=recovered['relative_centroid_field_correction'],
                           max_relative_balance_defect=recovered['max_relative_balance_defect']))

    windings = []
    for folder, name in (('cad_dc','foil_result'),('round_dc','round_result')):
        path = ROOT/f'sample_results/{folder}/{name}.json'
        result = json.loads(path.read_text())
        recovered = reconstruct_current(result)
        raw_jump, raw_wall = [], []
        for face, left, right, area_vector in zip(recovered['faces'],recovered['first_cell'],
                recovered['second_cell_or_electrode'],recovered['face_area_vectors_m2']):
            a = dot(result['current_density_A_m2'][left],area_vector)
            if 0 <= right < len(result['mesh']['tetrahedra']):
                b = dot(result['current_density_A_m2'][right],area_vector)
                raw_jump.append(abs(a-b))
            elif right == -1:
                raw_wall.append(abs(a))
        old_power, new_power = [], []
        sigma = result['input']['conductivity_S_m']
        for t, raw, projected in zip(result['mesh']['tetrahedra'],result['current_density_A_m2'],
                                     recovered['current_density_at_cell_centroid_A_m2']):
            volume, _ = tetra_geometry([result['mesh']['nodes_m'][i] for i in t])
            old_power.append(volume*dot(raw,raw)/sigma)
            new_power.append(volume*dot(projected,projected)/sigma)
        windings.append(dict(source=path.relative_to(ROOT).as_posix(),
                             tetrahedra=len(result['mesh']['tetrahedra']),
                             max_raw_internal_face_jump_A=max(raw_jump),
                             max_raw_insulated_face_current_A=max(raw_wall),
                             max_cell_current_defect_A=recovered['max_cell_current_defect_A'],
                             max_relative_balance_defect=recovered['max_relative_balance_defect'],
                             correction=recovered['relative_centroid_field_correction'],
                             terminal_adjustment_A=recovered['terminal_input_adjustment_A'],
                             raw_joule_power_W=math.fsum(old_power),
                             projected_centroid_joule_power_W=math.fsum(new_power)))
    args.output.write_text(json.dumps(dict(sector=series,windings=windings),indent=2,allow_nan=False)+'\n',
                           encoding='utf-8')


if __name__ == '__main__':
    main()
