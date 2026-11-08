"""Repeat the third-floor interior and join its dogleg stairs between levels."""
from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdShade


def build_levels(builder):
    b = builder
    geometry = b.exterior_manifest['source']['estimated_geometry']
    n, rise = b.e['stair_visible_risers'], b.m['stair_riser']
    if abs(geometry['floor_to_floor']-2*n*rise)>1e-6:
        raise ValueError('Floor spacing must equal the two connected stair flights')
    b.group('/World/Levels')
    parts = ['Floor', 'Walls', 'Ceilings', 'Doors', 'Fixtures', 'Stairs', 'Lights', 'SpawnPoints']
    levels = {}
    template_rooms = b.lighting_manifest['rooms']
    all_rooms = []
    for level in range(1, geometry['levels']+1):
        z = b.exterior_manifest['ground_z']+(level-1)*geometry['floor_to_floor']
        original = level==geometry['surveyed_level']
        root = '/World' if original else f'/World/Levels/Level_{level}'
        if not original:
            floor = b.group(root, (0, 0, z))
            floor.CreateAttribute('e10:level', Sdf.ValueTypeNames.Int).Set(level)
            for name in parts:
                prim = UsdGeom.Xform.Define(b.stage, root+'/'+name).GetPrim()
                prim.GetReferences().AddInternalReference('/World/'+name)
            rooms = UsdGeom.Xform.Define(b.stage, root+'/RoomWings').GetPrim()
            rooms.GetReferences().AddInternalReference('/World/Exterior/RoomWings')
            b.stage.OverridePrim(root+'/RoomWings/GroundFloorSlab').SetActive(False)
            b.stage.OverridePrim(root+'/Lights/Ambient').SetActive(False)
            material = '/World/Looks/Directory'+str(level)
            Sdf.CopySpec(b.stage.GetRootLayer(), '/World/Looks/Directory', b.stage.GetRootLayer(), material)
            UsdShade.Shader(b.stage.GetPrimAtPath(material+'/Texture')).GetInput('file').Set(Sdf.AssetPath(f'../../assets/textures/directory_{level}.png'))
            UsdShade.MaterialBindingAPI.Apply(b.stage.GetPrimAtPath(root+'/Fixtures/Directory/Face')).Bind(UsdShade.Material(b.stage.GetPrimAtPath(material)))
            marker_material = '/World/Looks/FloorMarker'+str(level)
            Sdf.CopySpec(b.stage.GetRootLayer(), '/World/Looks/FloorMarker', b.stage.GetRootLayer(), marker_material)
            UsdShade.Shader(b.stage.GetPrimAtPath(marker_material+'/Texture')).GetInput('file').Set(Sdf.AssetPath(f'../../assets/textures/floor_marker_{level}.png'))
            marker = b.stage.GetPrimAtPath(root+'/Fixtures/Elevator/FloorMarker')
            marker.GetAttribute('e10:floorNumber').Set(level)
            marker.GetAttribute('e10:label').Set(f'{level}F / {level}층')
            UsdShade.MaterialBindingAPI.Apply(b.stage.GetPrimAtPath(str(marker.GetPath())+'/Graphic/Face')).Bind(UsdShade.Material(b.stage.GetPrimAtPath(marker_material)))
        room_root = '/World/Exterior/RoomWings' if original else root+'/RoomWings'
        levels[str(level)] = {'root': root, 'floor_z': z, 'room_root': room_root,
                              'door_assemblies': len(b.c['doors'])}
        for room in template_rooms:
            item = dict(room, level=level, floor_z=z)
            item['lights'] = [path.replace('/World/', root+'/', 1) for path in room['lights']]
            all_rooms.append(item)

    width, gap = b.m['stair_flight_width'], b.e['stair_center_gap']
    entry = b.e['stair_entry_landing']
    end = entry+n*b.e['stair_tread']
    land = b.e['stair_terminal_landing']
    bay = 2*width+gap
    for level, direction, sign in [(1, 'Down', 1), (geometry['levels'], 'Up', -1)]:
        root = levels[str(level)]['root']
        for stair in b.c['stairs']:
            p = root+'/Stairs/'+stair['name']
            b.stage.OverridePrim(p+'/'+direction).SetActive(False)
            for name in ['Middle', 'Landing']:
                b.stage.OverridePrim(root+'/Lights/StairSupplements/'+stair['name']+'/'+direction+name).SetActive(False)
            if direction=='Up':
                b.stage.OverridePrim(p+'/HalfLandingBridge').SetActive(False)
            # The building terminates with a landing, rather than a flight into
            # the ground slab or through the roof.
            if direction=='Down':
                b.box(p+'/EndFloorClosure', (sign*(width+gap)/2, (entry+end+land)/2, -.08),
                      (width, end+land-entry, .16), 'Stone')
            else:
                # Leave the shaft open above the fifth-floor arriving flight;
                # a slab here would reduce its headroom to 1.92 m.
                cx = -(width+gap)/2
                for height in [.45, .90]:
                    b.rod(p+'/TopGuard_'+str(int(height*100)), (cx-width/2, entry-.06, height),
                          (cx+width/2, entry-.06, height), .025)
                for side in [-1, 1]:
                    b.rod(p+f'/TopGuardPost_{side+1}', (cx+side*(width/2-.03), entry-.06, 0),
                          (cx+side*(width/2-.03), entry-.06, .90), .018)
            low, high = (0, n*rise) if level==1 else (-n*rise, b.h)
            for name in ['SideWall_0', 'SideWall_2', 'BackWall', 'Divider']:
                prim = b.stage.GetPrimAtPath(p+'/'+name)
                pos = prim.GetAttribute('xformOp:translate').Get()
                scale = prim.GetAttribute('xformOp:scale').Get()
                prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(pos[0], pos[1], (low+high)/2))
                prim.GetAttribute('xformOp:scale').Set(Gf.Vec3d(scale[0], scale[1], high-low))
            if level==geometry['levels']:
                roof = root+'/Ceilings/Stair_'+stair['name']
                b.group(roof, (stair['x'], stair['side']*b.w/2, 0), stair['yaw'])
                b.box(roof+'/Roof', (0, (end+land)/2, b.h+.08),
                      (bay+2*b.e['wall_thickness'], end+land, .16), 'Ceiling')

    connections = []
    for level in range(1, geometry['levels']):
        for stair in b.c['stairs']:
            lower, upper = levels[str(level)], levels[str(level+1)]
            connections.append({'lower_level': level, 'upper_level': level+1, 'stair': stair['name'],
                                'lower_path': lower['root']+'/Stairs/'+stair['name'],
                                'upper_path': upper['root']+'/Stairs/'+stair['name'],
                                'landing_z': lower['floor_z']+n*rise})
    b.lighting_manifest['rooms'] = all_rooms
    b.lighting_manifest['floor_panels'] = {str(i): b.lighting_manifest['floor_panels'][str(geometry['surveyed_level'])] for i in range(1, geometry['levels']+1)}
    b.lighting_manifest['light_prims'] = sum(p.HasAPI(UsdLux.LightAPI) for p in b.stage.Traverse())
    b.lighting_manifest['stair_supplement_lights'] = 6*len(b.c['stairs'])*geometry['levels']-4*len(b.c['stairs'])
    b.exterior_manifest['traversable_interior_levels'] = list(range(1, geometry['levels']+1))
    return {'floors': levels, 'stair_connections': connections,
            'source': 'User-requested repetition of the video-based third-floor layout.'}
