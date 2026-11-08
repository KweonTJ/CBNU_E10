#!/usr/bin/env python3
"""Check the composed USD's dimensions, traversable volume and dependencies."""
import hashlib
import json
import math
from pathlib import Path
from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade, UsdUtils

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT/'worlds/cbnu_e10/cbnu_e10.usda'


def main():
    stage = Usd.Stage.Open(str(WORLD))
    config = json.loads((WORLD.parent/'config/layout.json').read_text())
    checks = []

    def check(label, condition, details=None):
        checks.append({'check': label, 'passed': bool(condition), 'details': details})

    def close(a, b):
        return abs(a-b) < 1e-5

    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render', 'proxy'])

    def bounds(path):
        return cache.ComputeWorldBound(stage.GetPrimAtPath(path)).ComputeAlignedRange()

    def contains(path, box, point):
        if not box.Contains(point):
            return False
        prim = stage.GetPrimAtPath(path)
        if not prim.IsA(UsdGeom.Mesh):
            return True
        # A sloped soffit's AABB includes open space. Test the actual closed mesh
        # by odd/even triangle intersections instead of reporting that box as solid.
        mesh = UsdGeom.Mesh(prim)
        transform = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
        vertices = [transform.Transform(Gf.Vec3d(*v)) for v in mesh.GetPointsAttr().Get()]
        indices = list(mesh.GetFaceVertexIndicesAttr().Get())
        direction = Gf.Vec3d(1, .00137, .00291)
        hits, offset = [], 0
        for count in mesh.GetFaceVertexCountsAttr().Get():
            face = indices[offset:offset+count]
            offset += count
            for i in range(1, count-1):
                a, b, c = (vertices[j] for j in [face[0], face[i], face[i+1]])
                edge1, edge2 = b-a, c-a
                cross = Gf.Cross(direction, edge2)
                det = Gf.Dot(edge1, cross)
                if abs(det) < 1e-10:
                    continue
                delta = point-a
                u = Gf.Dot(delta, cross)/det
                q = Gf.Cross(delta, edge1)
                v = Gf.Dot(direction, q)/det
                distance = Gf.Dot(edge2, q)/det
                if u >= 0 and v >= 0 and u+v <= 1 and distance > 1e-7:
                    if all(abs(distance-old)>1e-6 for old in hits):
                        hits.append(distance)
        return len(hits)%2 == 1

    check('Z-up, meter units, default World', UsdGeom.GetStageUpAxis(stage)=='Z' and UsdGeom.GetStageMetersPerUnit(stage)==1 and str(stage.GetDefaultPrim().GetPath())=='/World')
    floor = bounds('/World/Floor/Corridor/Slab')
    ceiling = bounds('/World/Ceilings/Corridor/Slab')
    check('Corridor width 2.10 m and floor at z=0', close(floor.GetSize()[1], 2.1) and close(floor.GetMax()[2], 0))
    check('Clear corridor height 2.50 m', close(ceiling.GetMin()[2]-floor.GetMax()[2], 2.5))
    m, e = config['measured'], config['estimated']
    for s in config['stairs']:
        for direction, sign in [('Up', 1), ('Down', -1)]:
            tops = []
            for i in range(1, e['stair_visible_risers']+1):
                p = f'/World/Stairs/{s["name"]}/{direction}/Tread_{i:02}'
                box = bounds(p)
                tops.append(box.GetMax()[2])
                check(p+' width/depth/top/collider', close(box.GetSize()[0], m['stair_flight_width']) and close(box.GetSize()[1], e['stair_tread']) and close(box.GetMax()[2], sign*i*m['stair_riser']) and stage.GetPrimAtPath(p).HasAPI(UsdPhysics.CollisionAPI))
            landing = bounds(f'/World/Stairs/{s["name"]}/{direction}/TerminalLanding')
            check(f'{s["name"]}/{direction} landing has no additional step', close(landing.GetMax()[2], tops[-1]))
    colliders = [p for p in stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)]
    invalid, no_material = [], []
    for prim in colliders:
        box = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        if box.IsEmpty() or any(not math.isfinite(v) for v in [*box.GetMin(), *box.GetMax()]):
            invalid.append(str(prim.GetPath()))
        if not UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()[0]:
            no_material.append(str(prim.GetPath()))
    check('Finite collider extents', not invalid, invalid)
    check('Bound materials on every collider', not no_material, no_material)
    # Swept sample of a central 1.30 m-wide, 1.85 m-high passage. AABBs are conservative.
    blockers = set()
    ranges = [(str(p.GetPath()), cache.ComputeWorldBound(p).ComputeAlignedRange()) for p in colliders]
    for ix in range(5, int(e['corridor_length']*10)-4):
        for y in [-.65, 0, .65]:
            for z in [.15, .65, 1.3, 2.0]:
                point = Gf.Vec3d(ix/10, y, z)
                for path, box in ranges:
                    if box.Contains(point):
                        blockers.add(path)
    check('Central 1.30 m corridor passage remains clear', not blockers, sorted(blockers))
    # Confirm stair centerlines have 2 m headroom without a low slab crossing them.
    headroom_blockers = set()
    xf = UsdGeom.XformCache()
    for s in config['stairs']:
        transform = xf.GetLocalToWorldTransform(stage.GetPrimAtPath('/World/Stairs/'+s['name']))
        for direction, sign, cx in [('Up', 1, -(m['stair_flight_width']+e['stair_center_gap'])/2), ('Down', -1, (m['stair_flight_width']+e['stair_center_gap'])/2)]:
            for i in range(1, e['stair_visible_risers']+1):
                y = e['stair_entry_landing']+(i-.5)*e['stair_tread']
                z = sign*i*m['stair_riser']
                for dz in [.25, 1, 2.0]:
                    point = transform.Transform(Gf.Vec3d(cx, y, z+dz))
                    for path, box in ranges:
                        if contains(path, box, point):
                            headroom_blockers.add(path)
    check('Stair centerlines have 2 m headroom', not headroom_blockers, sorted(headroom_blockers))
    layers, assets, unresolved = UsdUtils.ComputeAllDependencies(str(WORLD))
    check('No unresolved USD or texture dependencies', not unresolved, list(unresolved))
    check('All dependencies inside E10 repository', all(Path(str(p)).resolve().is_relative_to(ROOT) for p in assets))
    check('Exactly one physics scene', sum(p.IsA(UsdPhysics.Scene) for p in stage.Traverse())==1)
    check('Static environment has no accidental rigid bodies', not any(p.HasAPI(UsdPhysics.RigidBodyAPI) for p in stage.Traverse()))
    report = {'success': all(x['passed'] for x in checks), 'stage_sha256': hashlib.sha256(WORLD.read_bytes()).hexdigest(), 'check_count': len(checks), 'colliders': len(colliders), 'checks': checks}
    out = ROOT/'outputs/validation'
    out.mkdir(parents=True, exist_ok=True)
    (out/'static_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['success', 'check_count', 'colliders']}, indent=2))
    for check in checks:
        if not check['passed']:
            print('FAIL:', check)
    raise SystemExit(0 if report['success'] else 1)


if __name__ == '__main__':
    main()
