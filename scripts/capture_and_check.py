"""Isaac Sim --exec entrypoint: render the real USD, then run PhysX smoke checks."""
import asyncio
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import carb.settings
import omni.kit.app
import omni.usd

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT/'worlds/cbnu_e10/cbnu_e10.usda'
OUT = ROOT/'outputs/preview'


async def main():
    app = omni.kit.app.get_app()
    OUT.mkdir(parents=True, exist_ok=True)
    selected_views = [name for name in os.environ.get('E10_CAPTURE_VIEWS', '').split(',') if name]
    report = {'success': False, 'state': 'running', 'pid': os.getpid(), 'started_utc': datetime.now(timezone.utc).isoformat(),
              'stage_sha256': hashlib.sha256(WORLD.read_bytes()).hexdigest(), 'renders': [], 'physics_checks': []}
    report['mode'] = 'render_only' if selected_views else 'render_and_physics'
    status = OUT/('render_refresh.json' if selected_views else 'capture_status.json')
    status.write_text(json.dumps(report, indent=2))
    try:
        for _ in range(10):
            await app.next_update_async()
        context = omni.usd.get_context()
        ok, error = await context.open_stage_async(str(WORLD))
        if not ok:
            raise RuntimeError(str(error))
        from pxr import Gf, Usd, UsdGeom, UsdPhysics
        from omni.kit.viewport.utility import get_active_viewport, capture_viewport_to_file
        settings = carb.settings.get_settings()
        settings.set('/app/viewport/grid/enabled', False)
        settings.set('/rtx/post/tonemap/op', 6)
        settings.set('/rtx/post/tonemap/filmIso', 100)
        settings.set('/rtx/post/tonemap/fNumber', 4.0)
        settings.set('/rtx/post/tonemap/exposureTime', .016667)
        settings.set('/rtx/post/tonemap/cm2Factor', 1.0)
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        UsdGeom.Xform.Define(stage, '/ReviewCameras').CreateVisibilityAttr('invisible')
        manifest = json.loads((WORLD.parent/'build_manifest.json').read_text())
        review_views = manifest['views']
        for name, view in review_views.items():
            camera = UsdGeom.Camera.Define(stage, '/ReviewCameras/'+name)
            camera.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(*view['eye']), Gf.Vec3d(*view['target']), Gf.Vec3d(0, 0, 1)).GetInverse())
            camera.CreateFocalLengthAttr(view['focal_length'])
            wide = name.startswith(('Exterior', 'Lighting', 'Elevator')) or name=='AllFloors'
            camera.CreateHorizontalApertureAttr(36 if wide else 24)
            camera.CreateVerticalApertureAttr(22.5 if wide else 32)
            camera.CreateClippingRangeAttr(Gf.Vec2f(.03, 200))
        viewport = get_active_viewport()
        if viewport is None:
            raise RuntimeError('No rendering viewport available')
        names = ['ExteriorFront', 'ExteriorRear']+[name for name in review_views if not name.startswith('Exterior')]+['Corridor', 'ExteriorFront']
        if selected_views:
            if any(name not in review_views for name in selected_views):
                raise ValueError('Unknown review view in E10_CAPTURE_VIEWS')
            names = selected_views
        for name in names:
            overview = name=='Overview'
            viewport.set_texture_resolution((1600, 1000) if name.startswith(('Exterior', 'Lighting', 'Elevator')) or name=='AllFloors' else ((1600, 900) if overview else (900, 1200)))
            viewport.camera_path = '/ReviewCameras/'+name
            ceiling = UsdGeom.Imageable(stage.GetPrimAtPath('/World/Ceilings'))
            ceiling.CreateVisibilityAttr().Set('invisible' if overview else 'inherited')
            exterior = UsdGeom.Imageable(stage.GetPrimAtPath('/World/Exterior'))
            exterior.CreateVisibilityAttr().Set('invisible' if overview else 'inherited')
            UsdGeom.Imageable(stage.GetPrimAtPath('/World/Levels')).CreateVisibilityAttr().Set('invisible' if overview else 'inherited')
            for part in ['Facades', 'FacadeBands', 'Roofs']:
                # Some organizing parents are typeless USD prims, so author
                # activation rather than relying on Imageable inheritance.
                stage.OverridePrim('/World/Exterior/'+part).SetActive(name!='AllFloors')
            for _ in range(75):
                await app.next_update_async()
            job = capture_viewport_to_file(viewport, str(OUT/(name+'.png')))
            await job.wait_for_result(completion_frames=15)
            if name not in report['renders']:
                report['renders'].append(name)
            status.write_text(json.dumps(report, indent=2))
            print('E10_RENDER '+name, flush=True)
        if selected_views:
            report['state'] = 'complete'
            report['success'] = set(report['renders'])==set(selected_views)
            return
        # Session-layer probes leave the deliverable USD untouched.
        from omni import timeline as timeline_module
        from omni import physx as physx_module
        query = physx_module.get_physx_scene_query_interface()
        config = json.loads((WORLD.parent/'config/layout.json').read_text())
        m, e = config['measured'], config['estimated']
        drops = [('Corridor', (15, 0, 0)), ('Alcove', (33, -1.65, 0))]
        for level, item in manifest['levels']['floors'].items():
            z = item['floor_z']
            drops.extend([(f'Level{level}_Corridor', (17, 0, z)), (f'Level{level}_RoomFront', (9.5, -4.3, z)),
                          (f'Level{level}_RoomRear', (9.5, 4.3, z))])
        for item in manifest['levels']['stair_connections']:
            bridge = stage.GetPrimAtPath(item['lower_path']+'/HalfLandingBridge')
            pos = UsdGeom.XformCache().GetLocalToWorldTransform(bridge).Transform(Gf.Vec3d(0))
            drops.append((f'Bridge_{item["lower_level"]}_{item["stair"]}', (pos[0], pos[1], item['landing_z'])))
        xforms = UsdGeom.XformCache()
        for stair in config['stairs']:
            transform = xforms.GetLocalToWorldTransform(stage.GetPrimAtPath('/World/Stairs/'+stair['name']))
            for direction, sign, cx in [('Up', 1, -(m['stair_flight_width']+e['stair_center_gap'])/2), ('Down', -1, (m['stair_flight_width']+e['stair_center_gap'])/2)]:
                for i in [1, 7, e['stair_visible_risers']]:
                    pos = transform.Transform(Gf.Vec3d(cx, e['stair_entry_landing']+(i-.5)*e['stair_tread'], sign*i*m['stair_riser']))
                    drops.append((stair['name']+'_'+direction+f'_{i:02}', tuple(pos)))
        for name, (x, y, z) in drops:
            sphere = UsdGeom.Sphere.Define(stage, '/World/ValidationProbes/'+name)
            sphere.CreateRadiusAttr(.055)
            sphere.AddTranslateOp().Set(Gf.Vec3d(x, y, z+.32))
            UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
            UsdPhysics.RigidBodyAPI.Apply(sphere.GetPrim())
            UsdPhysics.MassAPI.Apply(sphere.GetPrim()).CreateMassAttr(.1)
        settings.set('/physics/updateToUsd', True)
        timeline = timeline_module.get_timeline_interface()
        timeline.play()
        for _ in range(200):
            await app.next_update_async()
        physx = physx_module.get_physx_interface()
        for name, (x, y, z) in drops:
            pose = physx.get_rigidbody_transformation('/World/ValidationProbes/'+name)
            actual = pose['position'][2]
            error = abs(actual-(z+.055))
            check = {'name': 'drop_'+name, 'expected_center_z': z+.055, 'actual_center_z': actual,
                     'error_m': error, 'passed': error < .025}
            report['physics_checks'].append(check)
        # Raycasts are offset from probes to inspect supporting geometry directly.
        for name, (x, y, z) in drops:
            # The bridge is only 18 cm wide: offset along its landing instead.
            offset = (0, .10) if name.startswith('Bridge_') else (.10, 0)
            hit = query.raycast_closest((x+offset[0], y+offset[1], z+.10), (0, 0, -1), .4)
            actual = hit['position'][2] if hit.get('hit') else None
            report['physics_checks'].append({'name': 'ray_'+name, 'expected_z': z, 'actual_z': actual,
                'collider': str(hit.get('collision', '')), 'passed': actual is not None and abs(actual-z)<.005})
        timeline.stop()
        report['state'] = 'complete'
        report['success'] = len(report['renders'])==len(review_views) and all(c['passed'] for c in report['physics_checks'])
        print('E10_RUNTIME_RESULT '+json.dumps({'success': report['success'], 'physics_checks': len(report['physics_checks'])}), flush=True)
    except Exception as exc:
        import traceback
        report['state'] = 'failed'
        report['error'] = str(exc)
        print('E10_RUNTIME_FAILED '+traceback.format_exc(), flush=True)
    finally:
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        status.write_text(json.dumps(report, indent=2)+'\n')
        app.post_quit()


asyncio.ensure_future(main())
