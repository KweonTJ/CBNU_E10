"""Report fixture geometry outside the union of corridor and alcove interiors."""
import json
from pathlib import Path
from pxr import Usd, UsdGeom

ROOT = Path(__file__).resolve().parents[1]


def allowed_rectangles(config):
    w = config['measured']['corridor_clear_width']
    e = config['estimated']
    a, b = e['alcove_x_range']
    return [(0, e['corridor_length'], -w/2, w/2), (a, b, -w/2-e['alcove_depth'], -w/2)]


def inspect_fixtures(stage, config):
    rects = allowed_rectangles(config)
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render', 'proxy'])
    failures, count = [], 0
    for p in Usd.PrimRange(stage.GetPrimAtPath('/World/Fixtures')):
        if not p.IsA(UsdGeom.Gprim):
            continue
        count += 1
        path = str(p.GetPath())
        box = cache.ComputeWorldBound(p).ComputeAlignedRange()
        lo, hi = box.GetMin(), box.GetMax()
        if any(not any(a-.001<=x<=b+.001 and c-.001<=y<=d+.001 for a,b,c,d in rects)
               for x in [lo[0], hi[0]] for y in [lo[1], hi[1]]):
            failures.append({'prim': path, 'min': list(lo), 'max': list(hi)})
    return {'success': not failures, 'geometry_count': count, 'tolerance_m': .001,
            'interior_rectangles_xy': rects, 'outside_geometry': failures}


def main():
    world = ROOT/'worlds/cbnu_e10/cbnu_e10.usda'
    stage = Usd.Stage.Open(str(world))
    config = json.loads((world.parent/'config/layout.json').read_text())
    report = inspect_fixtures(stage, config)
    out = ROOT/'outputs/validation'
    out.mkdir(parents=True, exist_ok=True)
    (out/'containment_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['success'] else 1)


if __name__ == '__main__':
    main()
