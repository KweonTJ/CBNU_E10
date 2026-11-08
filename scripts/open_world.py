"""Isaac Sim GUI entrypoint; camera/exposure edits stay in the session layer."""
import asyncio
from pathlib import Path
import carb.settings
import omni.kit.app
import omni.usd


async def open_world():
    app = omni.kit.app.get_app()
    for _ in range(10):
        await app.next_update_async()
    root = Path(__file__).resolve().parents[1]
    ok, error = await omni.usd.get_context().open_stage_async(str(root/'worlds/cbnu_e10/cbnu_e10.usda'))
    if not ok:
        raise RuntimeError(str(error))
    from omni.kit.viewport.utility import get_active_viewport
    viewport = get_active_viewport()
    if viewport:
        viewport.camera_path = '/World/Cameras/Corridor'
    settings = carb.settings.get_settings()
    for key, value in {'op': 6, 'filmIso': 100, 'fNumber': 4.0, 'exposureTime': .016667, 'cm2Factor': 1.0}.items():
        settings.set('/rtx/post/tonemap/'+key, value)
    settings.set('/app/viewport/grid/enabled', False)


asyncio.ensure_future(open_world())
