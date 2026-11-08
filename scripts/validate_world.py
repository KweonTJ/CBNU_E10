#!/usr/bin/env python3
"""Check the composed USD's dimensions, traversable volume and dependencies."""
import hashlib
import json
import math
from pathlib import Path
from pxr import Gf, Usd, UsdGeom, UsdLux, UsdPhysics, UsdShade, UsdUtils
from inspect_containment import inspect_fixtures

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT/'worlds/cbnu_e10/cbnu_e10.usda'


def main():
    stage = Usd.Stage.Open(str(WORLD))
    config = json.loads((WORLD.parent/'config/layout.json').read_text())
    manifest = json.loads((WORLD.parent/'build_manifest.json').read_text())
    floors = manifest['levels']['floors']
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
    for root, s in [(item['root'], s) for item in floors.values() for s in config['stairs']]:
        transform = xf.GetLocalToWorldTransform(stage.GetPrimAtPath(root+'/Stairs/'+s['name']))
        for direction, sign, cx in [('Up', 1, -(m['stair_flight_width']+e['stair_center_gap'])/2), ('Down', -1, (m['stair_flight_width']+e['stair_center_gap'])/2)]:
            if not stage.GetPrimAtPath(root+'/Stairs/'+s['name']+'/'+direction).IsActive():
                continue
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
    check('Deliverable world contains no cameras', not any(p.IsA(UsdGeom.Camera) for p in stage.Traverse()) and not stage.GetPrimAtPath('/World/Cameras'))
    overview = Usd.Stage.Open(str(WORLD.with_name('cbnu_e10_overview.usda')))
    check('Overview composition contains no cameras', not any(p.IsA(UsdGeom.Camera) for p in overview.Traverse()))
    containment = inspect_fixtures(stage, config)
    check('Every fixture stays inside corridor or alcove walls', containment['success'], containment)
    recessed_windows, blocked_apertures, door_top_gaps = [], [], []
    for door in [stage.GetPrimAtPath(item['root']+'/Doors/'+d['name']) for item in floors.values() for d in config['doors']]:
        header = stage.GetPrimAtPath(str(door.GetPath())+'/Header')
        header_bottom = cache.ComputeRelativeBound(header, door).ComputeAlignedRange().GetMin()[2]
        for index in [0, 1]:
            glass = stage.GetPrimAtPath(str(door.GetPath())+f'/Glass_{index}')
            glass_box = cache.ComputeRelativeBound(glass, door).ComputeAlignedRange()
            front = .035-.055/2
            depths = [glass_box.GetMin()[1]-front]
            for side in ['Left', 'Right', 'Top', 'Bottom']:
                frame = stage.GetPrimAtPath(str(door.GetPath())+f'/GlassFrame_{index}_{side}')
                depths.append(cache.ComputeRelativeBound(frame, door).ComputeAlignedRange().GetMin()[1]-front)
            cx, _, cz = glass_box.GetMidpoint()
            leaf = stage.GetPrimAtPath(str(door.GetPath())+f'/Leaf_{index}')
            leaf_top = cache.ComputeRelativeBound(leaf, door).ComputeAlignedRange().GetMax()[2]
            if abs(header_bottom-leaf_top)>1e-5:
                door_top_gaps.append(str(leaf.GetPath()))
            blockers = []
            for solid in leaf.GetChildren():
                local = cache.ComputeRelativeBound(solid, door).ComputeAlignedRange()
                if local.GetMin()[0] < cx < local.GetMax()[0] and local.GetMin()[2] < cz < local.GetMax()[2]:
                    blockers.append(str(solid.GetPath()))
            blocked_apertures.extend(blockers)
            if min(depths) >= .009 and glass_box.GetMax()[1] < .035+.055/2:
                recessed_windows.append(str(glass.GetPath()))
    check('All door windows and their frames are recessed into the leaf', len(recessed_windows)==2*len(config['doors'])*len(floors), {'window_count':len(recessed_windows), 'glass_recess_m':.0355, 'frame_recess_m':.0095})
    check('Door window apertures contain no solid door backing', not blocked_apertures, blocked_apertures)
    check('Every door leaf reaches the header with no top gap', not door_top_gaps, door_top_gaps)
    exterior_config = json.loads((WORLD.parent/'config/exterior.json').read_text())
    exterior_dims = exterior_config['estimated_geometry']
    check('Photo-referenced exterior has six levels', exterior_dims['levels']==6 and all(stage.GetPrimAtPath(f'/World/Exterior/Facades/MainFront/Level_{i}') for i in range(1,7)))
    envelope = bounds('/World/Exterior/RoomWings/GroundFloorSlab')
    check('Unified exterior foundation surrounds corridor and stair bays', envelope.GetSize()[1]>15 and envelope.GetMin()[0]<0 and envelope.GetMax()[0]>config['estimated']['corridor_length'])
    lighting = manifest['lighting']
    transforms = UsdGeom.XformCache()
    level_lights = {}
    hidden_lights, embedded_lights = [], []
    for prim in stage.Traverse():
        if not prim.HasAPI(UsdLux.LightAPI):
            continue
        if UsdGeom.Imageable(prim).ComputeVisibility()=='invisible' or UsdLux.LightAPI(prim).GetIntensityAttr().Get()<=0:
            hidden_lights.append(str(prim.GetPath()))
        path = str(prim.GetPath())
        if '/Lights/Rooms/' in path or '/Lights/StairSupplements/' in path:
            pos = transforms.GetLocalToWorldTransform(prim).Transform(Gf.Vec3d(0))
            if any(contains(path, box, pos) for path, box in ranges):
                embedded_lights.append(path)
        if '/Lights/Rooms/' in path:
            key = path.split('/')[3] if path.startswith('/World/Levels/') else 'Level_3'
            level_lights[key] = level_lights.get(key, 0)+1
    check('Every level has active local lights', len(level_lights)==exterior_dims['levels'] and all(n>0 for n in level_lights.values()) and not hidden_lights, level_lights)
    check('New lights are outside solid walls, floors and ceilings', not embedded_lights, embedded_lights)
    room_coverage = []
    for room in lighting['rooms']:
        left, right, front, rear = room['bounds_xy']
        points = [transforms.GetLocalToWorldTransform(stage.GetPrimAtPath(path)).Transform(Gf.Vec3d(0)) for path in room['lights']]
        room_coverage.append(bool(points) and all(left<p[0]<right and front<p[1]<rear and 2.0<p[2]-room['floor_z']<2.5 for p in points))
    check('Every enclosed room has its own ceiling lights', bool(room_coverage) and all(room_coverage), {'rooms':len(room_coverage)})
    for level, item in floors.items():
        root, z = item['root'], item['floor_z']
        slab = bounds(root+'/Floor/Corridor/Slab')
        roof = bounds(root+'/Ceilings/Corridor/Slab')
        doors = stage.GetPrimAtPath(root+'/Doors').GetChildren()
        check('Level '+level+' repeats the measured corridor and all doors',
              close(slab.GetMax()[2], z) and close(slab.GetSize()[1], 2.1) and close(roof.GetMin()[2]-z, 2.5) and len(doors)==len(config['doors']))
    blocked_connections = []
    for item in manifest['levels']['stair_connections']:
        low = item['lower_path']
        upper = item['upper_path']
        z = item['landing_z']
        bridge = bounds(low+'/HalfLandingBridge')
        heights = [bounds(low+'/Up/TerminalLanding').GetMax()[2], bridge.GetMax()[2], bounds(upper+'/Down/TerminalLanding').GetMax()[2]]
        check(f'Half landing {item["lower_level"]}-{item["upper_level"]} {item["stair"]} is continuous', all(close(height,z) for height in heights))
        transform = transforms.GetLocalToWorldTransform(stage.GetPrimAtPath(low))
        along = e['stair_entry_landing']+e['stair_visible_risers']*e['stair_tread']+e['stair_terminal_landing']/2
        for x in [-.84, -.08, 0, .08, .84]:
            for height in [.15, 1.0, 2.0]:
                point = transform.Transform(Gf.Vec3d(x, along, e['stair_visible_risers']*m['stair_riser']+height))
                for path, box in ranges:
                    if contains(path, box, point):
                        blocked_connections.append(path)
    check('All ten half-landings have clear crossing space and 2 m headroom', not blocked_connections, sorted(set(blocked_connections)))
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
