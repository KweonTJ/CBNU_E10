"""Template lights for rooms and stairs, repeated on all floors by build_levels."""
import math
from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux


def panel(builder, path, position, intensity, rotation=None, width=None):
    b, c = builder, builder.lighting
    prim = b.group(path, position)
    if rotation is not None:
        UsdGeom.Xformable(prim).AddRotateXYZOp().Set(Gf.Vec3f(*rotation))
    width, height = c['panel_width'] if width is None else width, c['panel_height']
    b.box(path+'/Housing', (0, 0, .022), (width+.04, height+.04, .04), 'DoorWhite', False)
    b.box(path+'/Diffuser', (0, 0, .001), (width, height, .002), 'CoolGlow', False)
    light = UsdLux.RectLight.Define(b.stage, path+'/Light')
    light.CreateWidthAttr(width)
    light.CreateHeightAttr(height)
    light.CreateNormalizeAttr(True)
    light.CreateIntensityAttr(intensity)
    light.CreateColorAttr(Gf.Vec3f(*c['color']))
    light.AddTranslateOp().Set(Gf.Vec3d(0, 0, -.006))


def build_lighting(builder):
    b, c = builder, builder.lighting
    exterior = b.exterior_manifest
    geometry = exterior['source']['estimated_geometry']
    root = '/World/Lights/Rooms'
    b.group(root)
    counts, rooms = {}, []
    for level in [geometry['surveyed_level']]:
        floor_z = exterior['ground_z']+(level-1)*geometry['floor_to_floor']
        group = root+f'/Level_{level}'
        prim = b.group(group)
        prim.CreateAttribute('e10:level', Sdf.ValueTypeNames.Int).Set(level)
        prim.CreateAttribute('e10:floorZ', Sdf.ValueTypeNames.Double).Set(floor_z)
        if level == geometry['surveyed_level']:
            # Derive each enclosed room from the actual slabs and partitions.
            # A light in the corridor cannot illuminate through the closed doors.
            wings = b.stage.GetPrimAtPath('/World/Exterior/RoomWings')
            cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render'])
            bounds = lambda p: cache.ComputeWorldBound(p).ComputeAlignedRange()
            partitions = [bounds(p) for p in wings.GetChildren() if p.GetName().startswith('Partition_')]
            for slab in wings.GetChildren():
                if not slab.GetName().startswith('Floor_'):
                    continue
                box = bounds(slab)
                lo, hi = box.GetMin(), box.GetMax()
                y = (lo[1]+hi[1])/2
                cuts = [lo[0]]+sorted(p.GetMidpoint()[0] for p in partitions
                                     if p.GetMin()[1]<y<p.GetMax()[1] and lo[0]<p.GetMidpoint()[0]<hi[0])+[hi[0]]
                for index, (left, right) in enumerate(zip(cuts, cuts[1:])):
                    name = slab.GetName()+f'_Room_{index}'
                    b.group(group+'/'+name)
                    paths = []
                    number = max(1, math.ceil((right-left)/3.9))
                    for n in range(number):
                        path = group+'/'+name+f'/Panel_{n}'
                        x = left+(right-left)*(n+.5)/number
                        panel(b, path, (x, y, b.h-.05), c['floor_panel_intensity'],
                              width=min(c['panel_width'], right-left-.16))
                        paths.append(path+'/Light')
                    rooms.append({'name': name, 'bounds_xy': [left, right, lo[1], hi[1]], 'lights': paths})
        counts[str(level)] = sum(p.IsA(UsdLux.RectLight) for p in Usd.PrimRange(prim))

    # Mount supplementary fixtures on the real stair walls. Their emission faces
    # inward, and their height follows each flight instead of the high roof.
    stair_root = '/World/Lights/StairSupplements'
    b.group(stair_root)
    width, gap = b.m['stair_flight_width'], b.e['stair_center_gap']
    entry, tread = b.e['stair_entry_landing'], b.e['stair_tread']
    count, rise = b.e['stair_visible_risers'], b.m['stair_riser']
    half_bay = width+gap/2
    for stair in b.c['stairs']:
        group = stair_root+'/'+stair['name']
        b.group(group, (stair['x'], stair['side']*b.w/2, 0), stair['yaw'])
        for side in [-1, 1]:
            panel(b, group+f'/Entry_{side+1}', (side*(half_bay-.055), entry/2, 2.05),
                  c['stair_entry_intensity'], (0, side*90, 0))
        for direction, sign in [('Up', 1), ('Down', -1)]:
            wall_side = -sign
            for name, along, elevation in [
                    ('Middle', entry+(7-.5)*tread, sign*7*rise),
                    ('Landing', entry+count*tread+b.e['stair_terminal_landing']/2, sign*count*rise)]:
                panel(b, group+'/'+direction+name, (wall_side*(half_bay-.055), along, elevation+1.85),
                      c['stair_wall_intensity'], (0, wall_side*90, 0))
    return {'floor_panels': counts, 'rooms': rooms, 'stair_supplement_lights': 6*len(b.c['stairs']),
            'configuration': 'config/lighting.json',
            'light_prims': sum(p.HasAPI(UsdLux.LightAPI) for p in b.stage.Traverse())}
