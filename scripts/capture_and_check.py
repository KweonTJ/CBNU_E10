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
    report = {'success': False, 'state': 'running', 'pid': os.getpid(), 'started_utc': datetime.now(timezone.utc).isoformat(),
              'stage_sha256': hashlib.sha256(WORLD.read_bytes()).hexdigest(), 'renders': [], 'physics_checks': []}
    status = OUT/'capture_status.json'
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
        viewport = get_active_viewport()
        if viewport is None:
            raise RuntimeError('No rendering viewport available')
        names = ['Corridor', 'StartStairs', 'FarLobby', 'PlantAlcove', 'Return', 'Overview', 'Corridor']
        for name in names:
            overview = name=='Overview'
            viewport.set_texture_resolution((1600, 900) if overview else (900, 1200))
            viewport.camera_path = '/World/Cameras/'+name
            ceiling = UsdGeom.Imageable(stage.GetPrimAtPath('/World/Ceilings'))
            ceiling.CreateVisibilityAttr().Set('invisible' if overview else 'inherited')
            for _ in range(75):
                await app.next_update_async()
            job = capture_viewport_to_file(viewport, str(OUT/(name+'.png')))
            await job.wait_for_result(completion_frames=15)
            if name not in report['renders']:
                report['renders'].append(name)
            status.write_text(json.dumps(report, indent=2))
            print('E10_RENDER '+name, flush=True)
        # Session-layer probes leave the deliverable USD untouched.
        from omni import timeline as timeline_module
        from omni import physx as physx_module
        query = physx_module.get_physx_scene_query_interface()
        config = json.loads((WORLD.parent/'config/layout.json').read_text())
        m, e = config['measured'], config['estimated']
        drops = [('Corridor', (15, 0, 0)), ('Alcove', (33, -1.65, 0))]
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
            hit = query.raycast_closest((x+.10, y, z+.10), (0, 0, -1), .4)
            actual = hit['position'][2] if hit.get('hit') else None
            report['physics_checks'].append({'name': 'ray_'+name, 'expected_z': z, 'actual_z': actual,
                'collider': str(hit.get('collision', '')), 'passed': actual is not None and abs(actual-z)<.005})
        timeline.stop()
        report['state'] = 'complete'
        report['success'] = len(report['renders'])==6 and all(c['passed'] for c in report['physics_checks'])
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
