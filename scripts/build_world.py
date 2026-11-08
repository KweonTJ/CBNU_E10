#!/usr/bin/env python3
"""Build a self-contained E10 USD using the locally installed OpenUSD runtime."""
import hashlib
import json
import math
import random
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdPhysics, UsdShade
from build_exterior import build_exterior
from build_lighting import build_lighting
from build_levels import build_levels

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'worlds' / 'cbnu_e10'
CONFIG = OUT / 'config' / 'layout.json'
PALETTE = {
    'Wall': ((.79, .80, .76), .78, 0),
    'Ceiling': ((.82, .83, .79), .85, 0),
    'Stone': ((.57, .57, .53), .42, 0),
    'FloorCream': ((.60, .59, .55), .32, 0),
    'FloorGreen': ((.37, .43, .38), .38, 0),
    'Grout': ((.30, .32, .30), .85, 0),
    'Skirting': ((.045, .053, .05), .55, 0),
    'Teal': ((.065, .28, .32), .42, .15),
    'DoorWhite': ((.76, .78, .75), .5, .05),
    'Metal': ((.52, .57, .59), .22, .85),
    'DarkGlass': ((.09, .16, .15), .17, .40),
    'WindowGlass': ((.17, .23, .24), .12, .50),
    'StairGreen': ((.44, .53, .43), .86, 0),
    'Red': ((.62, .016, .023), .3, .25),
    'White': ((.89, .89, .85), .6, 0),
    'Blue': ((.025, .09, .22), .6, .1),
    'Exit': ((.025, .24, .09), .6, 0),
    'Wood': ((.55, .37, .20), .58, 0),
    'WoodLight': ((.64, .51, .35), .6, 0),
    'Yellow': ((.93, .62, .025), .7, 0),
    'Leaf': ((.035, .16, .055), .65, 0),
    'LeafLight': ((.11, .26, .07), .6, 0),
    'Soil': ((.045, .026, .014), 1, 0),
    'Pot': ((.13, .095, .06), .6, 0),
    'WarmGlow': ((1, .65, .28), .4, 0),
    'CoolGlow': ((.95, .97, 1), .4, 0),
    'Brick': ((.38, .16, .10), .88, 0),
    'BrickBase': ((.36, .16, .11), .88, 0),
    'BrickAccent': ((.46, .21, .12), .75, 0),
    'Limestone': ((.78, .78, .71), .68, 0),
    'Concrete': ((.48, .49, .47), .78, 0),
    'Roof': ((.20, .24, .22), .85, 0),
    'FacadeGlass': ((.055, .22, .29), .18, .55),
    'Aluminum': ((.64, .68, .68), .28, .72),
    'SitePaving': ((.29, .31, .31), .9, 0),
    'BuildingSign': ((.9, .9, .85), .5, 0),
}


class Builder:
    def __init__(self, config, filename):
        self.c = config
        self.m, self.e = config['measured'], config['estimated']
        self.lighting = json.loads((OUT/'config/lighting.json').read_text())
        self.w, self.h = self.m['corridor_clear_width'], self.m['corridor_clear_height']
        self.length = self.e['corridor_length']
        self.stage = Usd.Stage.CreateNew(str(filename))
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(self.stage, 1)
        self.stage.SetTimeCodesPerSecond(60)
        world = UsdGeom.Xform.Define(self.stage, '/World').GetPrim()
        self.stage.SetDefaultPrim(world)
        world.CreateAttribute('e10:surveyedFloor', Sdf.ValueTypeNames.Int).Set(3)
        world.CreateAttribute('e10:sourceVideo', Sdf.ValueTypeNames.String).Set(config['source_video'])
        for key, value in self.m.items():
            world.CreateAttribute('e10:' + key, Sdf.ValueTypeNames.Double).Set(value)
        for name in ['Looks', 'Floor', 'Walls', 'Ceilings', 'Doors', 'Fixtures', 'Stairs', 'Lights', 'SpawnPoints']:
            UsdGeom.Xform.Define(self.stage, '/World/' + name)
        self.materials = {}
        self.containment_adjustments = []
        self.make_materials()
        physics = UsdPhysics.Scene.Define(self.stage, '/World/PhysicsScene')
        physics.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
        physics.CreateGravityMagnitudeAttr(9.81)
        physics.GetPrim().AddAppliedSchema('PhysxSceneAPI')
        physics.GetPrim().CreateAttribute('physxScene:timeStepsPerSecond', Sdf.ValueTypeNames.UInt).Set(120)
        physics.GetPrim().CreateAttribute('physxScene:enableGPUDynamics', Sdf.ValueTypeNames.Bool).Set(False)
        self.stage.GetRootLayer().customLayerData = {
            'generator': 'scripts/build_world.py',
            'config_sha256': hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        }

    def make_materials(self):
        textures = {'FloorCream': 'terrazzo_cream', 'FloorGreen': 'terrazzo_green', 'Ceiling': 'ceiling',
                    'Directory': 'directory', 'QuietSign': 'quiet', 'Brick': 'brick', 'BuildingSign': 'building_sign',
                    'FloorMarker': 'floor_marker_3'}
        for name in [*PALETTE, 'Directory', 'QuietSign', 'FloorMarker']:
            color, rough, metallic = PALETTE.get(name, ((.8, .8, .8), .7, 0))
            path = '/World/Looks/' + name
            mat = UsdShade.Material.Define(self.stage, path)
            shader = UsdShade.Shader.Define(self.stage, path + '/Surface')
            shader.CreateIdAttr('UsdPreviewSurface')
            shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
            shader.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(rough)
            shader.CreateInput('metallic', Sdf.ValueTypeNames.Float).Set(metallic)
            if name == 'WarmGlow':
                shader.CreateInput('emissiveColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(2, 1, .4))
            if name == 'CoolGlow':
                shader.CreateInput('emissiveColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(8, 8, 8))
            shader.CreateOutput('surface', Sdf.ValueTypeNames.Token)
            mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), 'surface')
            if name in textures:
                reader = UsdShade.Shader.Define(self.stage, path + '/UV')
                reader.CreateIdAttr('UsdPrimvarReader_float2')
                reader.CreateInput('varname', Sdf.ValueTypeNames.Token).Set('st')
                reader.CreateOutput('result', Sdf.ValueTypeNames.Float2)
                tex = UsdShade.Shader.Define(self.stage, path + '/Texture')
                tex.CreateIdAttr('UsdUVTexture')
                tex.CreateInput('file', Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath('../../assets/textures/' + textures[name] + '.png'))
                tex.CreateInput('sourceColorSpace', Sdf.ValueTypeNames.Token).Set('sRGB')
                for wrap in ['wrapS', 'wrapT']:
                    tex.CreateInput(wrap, Sdf.ValueTypeNames.Token).Set('repeat')
                tex.CreateInput('st', Sdf.ValueTypeNames.Float2).ConnectToSource(reader.ConnectableAPI(), 'result')
                tex.CreateOutput('rgb', Sdf.ValueTypeNames.Float3)
                shader.GetInput('diffuseColor').ConnectToSource(tex.ConnectableAPI(), 'rgb')
                if name == 'BuildingSign':
                    tex.CreateOutput('a', Sdf.ValueTypeNames.Float)
                    shader.CreateInput('opacity', Sdf.ValueTypeNames.Float).ConnectToSource(tex.ConnectableAPI(), 'a')
                    shader.CreateInput('opacityThreshold', Sdf.ValueTypeNames.Float).Set(.5)
            material_physics = UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
            material_physics.CreateStaticFrictionAttr(.8)
            material_physics.CreateDynamicFrictionAttr(.65)
            material_physics.CreateRestitutionAttr(0)
            self.materials[name] = mat

    def finish(self, shape, material, collision):
        prim = shape.GetPrim()
        binding = UsdShade.MaterialBindingAPI.Apply(prim)
        binding.Bind(self.materials[material])
        if collision:
            UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
            binding.Bind(self.materials[material], materialPurpose='physics')
        if isinstance(shape, UsdGeom.Gprim):
            shape.CreateDisplayColorAttr([Gf.Vec3f(*PALETTE.get(material, ((.8, .8, .8), 0, 0))[0])])
        return prim

    def group(self, path, pos=(0, 0, 0), yaw=0):
        xform = UsdGeom.Xform.Define(self.stage, path)
        xform.AddTranslateOp().Set(Gf.Vec3d(*pos))
        if yaw:
            xform.AddRotateZOp().Set(yaw)
        return xform.GetPrim()

    def box(self, path, pos, size, mat, collision=True, rotate=None):
        if min(size) <= 0:
            raise ValueError(f'Nonpositive size: {path}: {size}')
        shape = UsdGeom.Cube.Define(self.stage, path)
        shape.CreateSizeAttr(1)
        shape.AddTranslateOp().Set(Gf.Vec3d(*pos))
        if rotate:
            shape.AddRotateXYZOp().Set(Gf.Vec3f(*rotate))
        shape.AddScaleOp().Set(Gf.Vec3d(*size))
        return self.finish(shape, mat, collision)

    def cylinder(self, path, pos, radius, height, mat, collision=True):
        shape = UsdGeom.Cylinder.Define(self.stage, path)
        shape.CreateRadiusAttr(radius)
        shape.CreateHeightAttr(height)
        shape.CreateAxisAttr('Z')
        shape.AddTranslateOp().Set(Gf.Vec3d(*pos))
        return self.finish(shape, mat, collision)

    def rod(self, path, a, b, radius=.018, mat='Metal', collision=True):
        delta = Gf.Vec3d(*b) - Gf.Vec3d(*a)
        shape = UsdGeom.Cylinder.Define(self.stage, path)
        shape.CreateRadiusAttr(radius)
        shape.CreateHeightAttr(delta.GetLength())
        shape.CreateAxisAttr('Z')
        shape.AddTranslateOp().Set((Gf.Vec3d(*a) + Gf.Vec3d(*b)) / 2)
        q = Gf.Rotation(Gf.Vec3d(0, 0, 1), delta.GetNormalized()).GetQuat()
        shape.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(q)
        return self.finish(shape, mat, collision)

    def mesh(self, path, points, faces, mat, collision=False, uv=None):
        shape = UsdGeom.Mesh.Define(self.stage, path)
        shape.CreatePointsAttr(points)
        shape.CreateFaceVertexCountsAttr([len(f) for f in faces])
        shape.CreateFaceVertexIndicesAttr([i for f in faces for i in f])
        shape.CreateSubdivisionSchemeAttr('none')
        shape.CreateDoubleSidedAttr(True)
        if uv:
            UsdGeom.PrimvarsAPI(shape).CreatePrimvar('st', Sdf.ValueTypeNames.TexCoord2fArray, 'faceVarying').Set(uv)
        return self.finish(shape, mat, collision)

    def plane(self, path, x0, x1, y0, y1, z, mat, pitch=.3, down=False):
        pts = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
        indices = [3, 2, 1, 0] if down else [0, 1, 2, 3]
        self.mesh(path, pts, [indices], mat, uv=[(pts[i][0]/pitch, pts[i][1]/pitch) for i in indices])

    def poster(self, path, center, width, height, mat, yaw=0):
        self.group(path, center, yaw)
        self.mesh(path + '/Face', [(-width/2, 0, -height/2), (width/2, 0, -height/2),
                  (width/2, 0, height/2), (-width/2, 0, height/2)], [[0, 1, 2, 3]], mat,
                  uv=[(0, 0), (1, 0), (1, 1), (0, 1)])

    def floor(self, name, x0, x1, y0, y1, z=0, border=False):
        base = '/World/Floor/' + name
        self.group(base)
        t = self.e['slab_thickness']
        self.box(base + '/Slab', ((x0+x1)/2, (y0+y1)/2, z-t/2), (x1-x0, y1-y0, t), 'Stone')
        b = self.e['floor_border_width'] if border else 0
        self.plane(base + '/Terrazzo', x0, x1, y0+b, y1-b, z+.0005, 'FloorCream')
        if border:
            self.plane(base + '/GreenLeft', x0, x1, y1-b, y1, z+.0005, 'FloorGreen')
            self.plane(base + '/GreenRight', x0, x1, y0, y0+b, z+.0005, 'FloorGreen')
        pitch = self.e['floor_tile']
        for i in range(1, round((x1-x0)/pitch)):
            self.box(base+f'/JointX_{i:03}', (x0+i*pitch, (y0+y1)/2, z+.0008), (.0015, y1-y0, .0004), 'Grout', False)
        for i in range(1, round((y1-y0)/pitch)):
            self.box(base+f'/JointY_{i:02}', ((x0+x1)/2, y0+i*pitch, z+.0008), (x1-x0, .0015, .0004), 'Grout', False)

    def ceiling(self, name, x0, x1, y0, y1, z):
        base = '/World/Ceilings/' + name
        self.group(base)
        self.box(base+'/Slab', ((x0+x1)/2, (y0+y1)/2, z+.08), (x1-x0, y1-y0, .16), 'Ceiling')
        self.plane(base+'/Panels', x0, x1, y0, y1, z-.0005, 'Ceiling', .6, True)
        for i in range(1, math.ceil((x1-x0)/.6)):
            self.box(base+f'/GridX_{i:03}', (x0+i*.6, (y0+y1)/2, z-.002), (.008, y1-y0, .004), 'DoorWhite', False)
        for i in range(1, math.ceil((y1-y0)/.3)):
            self.box(base+f'/GridY_{i:02}', ((x0+x1)/2, y0+i*.3, z-.002), (x1-x0, .008, .004), 'DoorWhite', False)

    def walls(self):
        t = self.e['wall_thickness']
        bay = 2*self.m['stair_flight_width'] + self.e['stair_center_gap']
        for side in [-1, 1]:
            holes = [(s['x']-bay/2, s['x']+bay/2, 2.3) for s in self.c['stairs'] if s['side']==side]
            if side == -1:
                holes.append((*self.e['alcove_x_range'], self.h))
            holes += [(d['x']-d['width']/2-.045, d['x']+d['width']/2+.045, 2.3) for d in self.c['doors'] if d['side']==side]
            cursor = 0
            for i, (lo, hi, height) in enumerate(sorted(holes) + [(self.length, self.length, self.h)]):
                if lo < cursor - 1e-7:
                    raise ValueError('Overlapping wall openings')
                base = f'/World/Walls/{"North" if side==1 else "South"}_{i:02}'
                if lo > cursor:
                    self.box(base, ((cursor+lo)/2, side*(self.w/2+t/2), self.h/2), (lo-cursor, t, self.h), 'Wall')
                    self.box(base+'_Skirting', ((cursor+lo)/2, side*(self.w/2-.008), .055), (lo-cursor, .016, .11), 'Skirting')
                if height < self.h:
                    self.box(base+'_Header', ((lo+hi)/2, side*(self.w/2+t/2), (height+self.h)/2), (hi-lo, t, self.h-height), 'Wall')
                cursor = hi

    def door(self, d):
        x, side, width, style = (d[k] for k in ['x', 'side', 'width', 'style'])
        p = '/World/Doors/' + d['name']
        self.group(p, (x, side*self.w/2, 0), 0 if side == 1 else 180)
        color = 'DoorWhite' if style=='white' else 'Teal'
        height = self.e['door_height']
        for s in [-1, 1]:
            self.box(p+f'/Jamb_{s+1}', (s*(width/2+.0225), .04, 1.15), (.045, .13, 2.3), 'DoorWhite')
        self.box(p+'/Header', (0, .04, 2.28), (width+.09, .13, .04), 'DoorWhite')
        for i, sign in enumerate([-1, 1]):
            cx, lw = sign*width/4, width/2-.006
            glass_width = lw*.38 if style!='glazed' else lw*.78
            opening_w = glass_width+.04
            opening_h = .96 if style!='glazed' else 1.70
            opening_z = 1.46 if style!='glazed' else 1.15
            bottom, top = opening_z-opening_h/2, opening_z+opening_h/2
            leaf = p+f'/Leaf_{i}'
            self.group(leaf)
            # Four solid parts make an actual aperture. The front is local y=.0075.
            for label, sign_x in [('Left', -1), ('Right', 1)]:
                side_width = (lw-opening_w)/2
                self.box(leaf+'/'+label, (cx+sign_x*(opening_w/2+side_width/2), .035, height/2), (side_width,.055,height), color)
            self.box(leaf+'/BelowWindow', (cx,.035,bottom/2), (opening_w,.055,bottom), color)
            self.box(leaf+'/AboveWindow', (cx,.035,(top+height)/2), (opening_w,.055,height-top), color)
            # Rebate and pane both lie behind the door front; no overlay glass plate.
            for label, sign_x in [('Left', -1), ('Right', 1)]:
                self.box(p+f'/GlassFrame_{i}_{label}', (cx+sign_x*(opening_w/2-.012),.029,opening_z), (.024,.024,opening_h), 'Metal', False)
            for label, zz in [('Bottom', bottom+.012), ('Top', top-.012)]:
                self.box(p+f'/GlassFrame_{i}_{label}', (cx,.029,zz), (opening_w,.024,.024), 'Metal', False)
            self.box(p+f'/Glass_{i}', (cx,.047,opening_z), (opening_w-.048,.008,opening_h-.048), 'DarkGlass')
            if style == 'glazed':
                for h in [.55, .95, 1.35, 1.75]:
                    self.box(p+f'/Mullion_{i}_{int(h*100)}', (cx, .029, h), (opening_w-.048, .024, .027), 'Teal', False)
            self.cylinder(p+f'/Lock_{i}', (sign*.075, -.035, .95), .032, .035, 'Metal', False)
            self.box(p+f'/Handle_{i}', (sign*.12, -.055, .95), (.11, .03, .022), 'Metal', False)
        self.box(p+'/RoomPlate', (-width/2-.14, -.008, 1.6), (.16, .02, .10), 'Blue', False)
        self.box(p+'/CardReader', (-width/2-.12, -.016, 1.1), (.07, .035, .13), 'Skirting', False)
        self.box(p+'/Beacon', (-width/2-.05, -.04, 2.34), (.045, .045, .11), 'Blue', False)

    def downlight(self, name, x, y=0, z=None, intensity=None):
        z = self.h if z is None else z
        p = '/World/Lights/' + name
        self.cylinder(p+'_Trim', (x, y, z-.015), .105, .025, 'DoorWhite', False)
        self.cylinder(p+'_Lens', (x, y, z-.029), .086, .002, 'CoolGlow', False)
        disk = UsdLux.DiskLight.Define(self.stage, p)
        disk.CreateRadiusAttr(.085)
        disk.CreateIntensityAttr(self.lighting['corridor_intensity'] if intensity is None else intensity)
        disk.CreateNormalizeAttr(True)
        disk.CreateColorAttr(Gf.Vec3f(.94, .97, 1))
        disk.AddTranslateOp().Set(Gf.Vec3d(x, y, z-.036))

    def extinguisher(self, name, x, side):
        p = '/World/Fixtures/' + name
        self.group(p, (x, side*(self.w/2-.115), 0))
        self.box(p+'/Stand', (0, 0, .025), (.22, .22, .05), 'Red')
        self.cylinder(p+'/Bottle', (0, 0, .24), .075, .38, 'Red')
        self.cylinder(p+'/Neck', (0, 0, .46), .025, .055, 'Metal', False)
        self.box(p+'/Lever', (0, 0, .49), (.12, .026, .025), 'Skirting', False)
        self.box(p+'/Label', (0, -side*.073, .30), (.085, .006, .13), 'White', False)
        self.rod(p+'/Hose', (.075, 0, .46), (.10, 0, .20), .012, 'Skirting', False)

    def stairs(self, stair):
        fw, rise = self.m['stair_flight_width'], self.m['stair_riser']
        n, tread, gap = self.e['stair_visible_risers'], self.e['stair_tread'], self.e['stair_center_gap']
        bay = 2*fw+gap
        entry, land = self.e['stair_entry_landing'], self.e['stair_terminal_landing']
        end = entry+n*tread
        p = '/World/Stairs/' + stair['name']
        prim = self.group(p, (stair['x'], stair['side']*self.w/2, 0), stair['yaw'])
        prim.CreateAttribute('e10:geometryEvidence', Sdf.ValueTypeNames.String).Set('Video-based flights repeated on six levels, connected through inferred half-level landings.')
        self.box(p+'/EntryLanding', (0, entry/2, -.08), (bay, entry, .16), 'Stone')
        for name, sign, cx in [('Up', 1, -(fw+gap)/2), ('Down', -1, (fw+gap)/2)]:
            q = p+'/'+name
            self.group(q)
            for i in range(1, n+1):
                y, z = entry+(i-.5)*tread, sign*i*rise
                self.box(q+f'/Tread_{i:02}', (cx, y, z-.06), (fw, tread, .12), 'Stone')
                # The riser bridges the previous level and this level exactly.
                self.box(q+f'/Riser_{i:02}', (cx, entry+(i-1)*tread+.012, sign*(i-.5)*rise), (fw, .024, rise), 'Stone')
                self.box(q+f'/Nosing_{i:02}', (cx, y-tread/2+.015, z+.0005), (fw, .008, .001), 'Grout', False)
            self.box(q+'/TerminalLanding', (cx, end+land/2, sign*n*rise-.08), (fw, land, .16), 'Stone')
            # Sloped structural soffit lies below both the treads and risers.
            z0, z1 = (-.14, n*rise-.14) if sign==1 else (-rise-.14, -n*rise-rise-.14)
            profile = [(entry, z0), (end, z1), (end, z1-.16), (entry, z0-.16)]
            points = [(xx, yy, zz) for xx in [cx-fw/2, cx+fw/2] for yy, zz in profile]
            self.mesh(q+'/Soffit', points, [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], 'Stone', True)
            rail_x = cx + (fw/2-.028 if sign==1 else -fw/2+.028)
            rh = self.e['stair_rail_height']
            for i in range(0, n, 2):
                yy, zz = entry+(i+.5)*tread, sign*(i+1)*rise
                self.rod(q+f'/Post_{i:02}', (rail_x, yy, zz), (rail_x, yy, zz+rh), .016)
            a = (rail_x, entry+tread/2, sign*rise+rh)
            b = (rail_x, end-tread/2, sign*n*rise+rh)
            self.rod(q+'/Handrail', a, b, .025)
            self.rod(q+'/Midrail', (a[0], a[1], a[2]-.45), (b[0], b[1], b[2]-.45), .011)
            self.rod(q+'/EndPost', (rail_x, end-tread/2, sign*n*rise), b, .018)
        # One wall segment per level joins its neighbours without overlapping.
        low, high = -n*rise, n*rise
        t = self.e['wall_thickness']
        for sign in [-1, 1]:
            self.box(p+f'/SideWall_{sign+1}', (sign*(bay/2+t/2), (end+land)/2, (low+high)/2), (t, end+land, high-low), 'StairGreen')
        self.box(p+'/BackWall', (0, end+land+t/2, (low+high)/2), (bay+2*t, t, high-low), 'StairGreen')
        # Stop the divider before the landing so the next floor's return flight
        # is reachable. The bridge closes the 18 cm gap between the flights.
        self.box(p+'/Divider', (0, (entry+end)/2, (low+high)/2), (gap*.55, end-entry, high-low), 'StairGreen')
        self.box(p+'/HalfLandingBridge', (0, end+land/2, n*rise-.08), (gap, land, .16), 'Stone')
        self.box(p+'/ExitSign', (0, -.018, 2.405), (.30, .035, .13), 'Exit', False)
        self.box(p+'/ExitArrow', (0, -.038, 2.405), (.19, .008, .02), 'White', False)

    def end_window(self, name, x):
        p = '/World/Fixtures/' + name
        self.group(p, (x, 0, 0), 90 if x==self.length else -90)
        self.box(p+'/Back', (0, .06, 1.25), (self.w, .10, 2.5), 'WindowGlass')
        for side in [-1, 1]:
            self.box(p+f'/Jamb_{side+1}', (side*(self.w/2-.04), .055, 1.25), (.08, .10, 2.5), 'DoorWhite')
        for z in [.08, .88, 2.4]:
            self.box(p+f'/Cross_{int(z*100)}', (0, .055, z), (self.w, .10, .06), 'DoorWhite')
        self.box(p+'/Mullion', (0, .055, 1.65), (.055, .10, 1.5), 'DoorWhite')
        inward = .23
        for z in [.25, .50, .78, 1.0]:
            self.rod(p+f'/Guard_{int(z*100)}', (-self.w/2+.06, inward, z), (self.w/2-.06, inward, z), .022)
        for side in [-1, 1]:
            self.rod(p+f'/GuardPost_{side+1}', (side*.72, inward, .05), (side*.72, inward, 1.02), .025)

    def plant(self, name, x, y, height, seed):
        rng = random.Random(seed)
        p = '/World/Fixtures/Plants/' + name
        self.group(p, (x, y, 0))
        ph = min(.48, height*.35)
        self.cylinder(p+'/Pot', (0, 0, ph/2), .17, ph, 'Pot')
        self.cylinder(p+'/Soil', (0, 0, ph+.003), .155, .01, 'Soil', False)
        self.rod(p+'/Trunk', (0, 0, ph), (0, 0, height*.90), .018, 'Wood')
        for i in range(18):
            angle = rng.uniform(0, math.tau)
            z = rng.uniform(ph+.12, height*.93)
            length = rng.uniform(.20, .48)
            start = (0, 0, z)
            mid = (math.cos(angle)*length*.62, math.sin(angle)*length*.62, z+.15)
            tip = (math.cos(angle)*length, math.sin(angle)*length, z-.05)
            width = rng.uniform(.035, .09)
            tangent = (-math.sin(angle)*width, math.cos(angle)*width, 0)
            pts = [start, tuple(mid[k]+tangent[k] for k in range(3)), tip, tuple(mid[k]-tangent[k] for k in range(3)), mid]
            self.mesh(p+f'/Leaf_{i:02}', pts, [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]], 'Leaf' if i%3 else 'LeafLight')
        a, b = self.e['alcove_x_range']
        self.contain_group(p, (a, b, -self.w/2-self.e['alcove_depth'], -self.w/2), .08)

    def contain_group(self, path, rectangle, clearance):
        """Move an entire fixture, including its visible leaves and colliders."""
        prim = self.stage.GetPrimAtPath(path)
        bounds = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default']).ComputeWorldBound(prim).ComputeAlignedRange()
        lo, hi = bounds.GetMin(), bounds.GetMax()
        x0, x1, y0, y1 = rectangle
        shifts = []
        for axis, low, high in [(0, x0, x1), (1, y0, y1)]:
            if hi[axis]-lo[axis] > high-low-2*clearance:
                raise ValueError(f'Fixture cannot fit inside room: {path}')
            shift = max(0.0, low+clearance-lo[axis])
            shift = min(shift, high-clearance-hi[axis])
            shifts.append(shift)
        if any(abs(v)>1e-7 for v in shifts):
            attr = prim.GetAttribute('xformOp:translate')
            attr.Set(attr.Get()+Gf.Vec3d(shifts[0], shifts[1], 0))
            self.containment_adjustments.append({'prim': path, 'translation_xy_m': shifts, 'wall_clearance_m': clearance})

    def lobby(self):
        a, b = self.e['alcove_x_range']
        y0, y1 = -self.w/2-self.e['alcove_depth'], -self.w/2
        self.floor('PlantAlcove', a, b, y0, y1)
        self.ceiling('PlantAlcove', a, b, y0, y1, self.h)
        t = self.e['wall_thickness']
        for x in [a-t/2, b+t/2]:
            self.box('/World/Walls/Alcove_'+str(round(x*100)), (x, (y0+y1)/2, self.h/2), (t, y1-y0, self.h), 'Wall')
        self.box('/World/Walls/AlcoveRearLower', ((a+b)/2, y0-t/2, .46), (b-a, t, .92), 'Wall')
        self.box('/World/Walls/AlcoveRearGlass', ((a+b)/2, y0-t/2, 1.68), (b-a, .08, 1.52), 'WindowGlass')
        for x in [a+.05, a+1, a+2, b-.05]:
            self.box('/World/Fixtures/AlcoveFrame_'+str(round(x*100)), (x, y0+.05, 1.7), (.05, .08, 1.6), 'Metal')
        for z in [.9, 2.45]:
            self.box('/World/Fixtures/AlcoveFrameZ_'+str(int(z*100)), ((a+b)/2, y0+.05, z), (b-a, .08, .06), 'Metal')
        self.downlight('Alcove', (a+b)/2, (y0+y1)/2, intensity=self.lighting['alcove_intensity'])
        for i, (x, y, h) in enumerate([(a+.4,y0+.45,1.7),(a+1,y0+.55,1.45),(a+1.65,y0+.5,1.85),(b-.4,y0+1.0,1.4),(a+.9,y0+1.2,.65),(a+.3,y1-.5,.65)]):
            self.plant(f'Plant_{i:02}', x, y, h, 100+i)
        p = '/World/Fixtures/WaterDispenser'
        self.group(p, (b-.33, y0+1.5, 0))
        self.box(p+'/Body', (0, 0, .56), (.40, .42, 1.12), 'DoorWhite')
        self.box(p+'/TapPanel', (.206, 0, .85), (.016, .29, .24), 'Skirting', False)
        # Directory is readable at building/floor level; room-list rows stay anonymous.
        self.poster('/World/Fixtures/Directory', (b+.09, y1+.025, 1.55), .32, .56, 'Directory')
        elevator_x = (b+self.length)/2
        p = '/World/Fixtures/Elevator'
        self.group(p, (elevator_x, -self.w/2, 0), 180)
        self.box(p+'/WoodSurround', (0, -.035, 1.25), (self.length-b-.12, .06, 2.5), 'WoodLight', False)
        self.box(p+'/Frame', (0, -.09, 1.12), (1.55, .06, 2.24), 'Wood', False)
        for sign in [-1, 1]:
            self.box(p+f'/Door_{sign+1}', (sign*.326, -.13, 1.05), (.646, .03, 2.1), 'Metal', False)
        self.box(p+'/CallPanel', (.91, -.09, 1.12), (.08, .025, .23), 'Metal', False)
        self.box(p+'/Display', (0, -.13, 2.19), (.26, .02, .09), 'Skirting', False)
        self.box(p+'/DisplayLight', (0, -.145, 2.19), (.018, .01, .05), 'Red', False)
        for i, xx in enumerate([-.9, .9]):
            self.box(p+f'/Sconce_{i}', (xx, -.18, 1.9), (.13, .12, .32), 'WarmGlow', False)
        # Use the free wall beside the elevator, clear of its sconces and buttons.
        marker = p+'/FloorMarker'
        prim = self.group(marker, (1.26, -.076, 1.62))
        prim.CreateAttribute('e10:floorNumber', Sdf.ValueTypeNames.Int).Set(3)
        prim.CreateAttribute('e10:label', Sdf.ValueTypeNames.String).Set('3F / 3층')
        self.box(marker+'/Backing', (0, 0, 0), (.50, .022, .70), 'Aluminum', False)
        self.poster(marker+'/Graphic', (0, -.012, 0), .46, .66, 'FloorMarker')
        glow = UsdLux.RectLight.Define(self.stage, p+'/CoveLight')
        glow.CreateWidthAttr(2.4)
        glow.CreateHeightAttr(.06)
        glow.CreateIntensityAttr(1300)
        glow.CreateNormalizeAttr(True)
        glow.CreateColorAttr(Gf.Vec3f(1, .65, .30))
        glow.AddTranslateOp().Set(Gf.Vec3d(0, -.28, 2.40))
        for i, x in enumerate([elevator_x-.6, elevator_x+.6]):
            self.box(f'/World/Fixtures/Tactile_{i}', (x, -.70, .003), (.30, .30, .006), 'Yellow')
            for row in range(5):
                for col in range(5):
                    self.cylinder(f'/World/Fixtures/TactileDot_{i}_{row}_{col}', (x+(row-2)*.052, -.7+(col-2)*.052, .007), .011, .004, 'Yellow', False)

    def review_views(self):
        # Review poses are plain JSON. The deliverable stage contains no cameras.
        views = {
            'Corridor': ((4.4, 0, 1.58), (18, 0, 1.43), 18),
            'StartStairs': ((2.4, .45, 1.55), (2.65, -4.1, 1.05), 17),
            'FarLobby': ((32.3, .08, 1.58), (38.2, -.08, 1.40), 18),
            'PlantAlcove': ((32.65, .45, 1.55), (33.3, -3.6, 1.1), 17),
            'Return': ((30.8, 0, 1.58), (3, 0, 1.43), 18),
            'Overview': ((25, -38, 48), (19.2, 0, .1), 23),
            'ExteriorFront': ((-14, -44, 12), (17, -.7, 3.5), 30),
            'ExteriorRear': ((53, 38, 25), (20, 0, 4), 30),
            'DoorRecess': ((6.1, -.45, 1.60), (5.4, 1.05, 1.36), 28),
            'RoomFront': ((9.0, -1.8, 1.55), (10.4, -6.8, 1.4), 18),
            'RoomRear': ((9.0, 1.8, 1.55), (10.4, 6.8, 1.4), 18),
            'AllFloors': ((52, -48, 25), (19, 0, 4.2), 26),
        }
        exterior = self.exterior_manifest
        geometry = exterior['source']['estimated_geometry']
        for level in range(1, geometry['levels']+1):
            z = exterior['ground_z']+(level-1)*geometry['floor_to_floor']
            views[f'LightingLevel{level}'] = ((13.4, -2.0, z+1.5), (14.0, -7.65, z+1.35), 24)
            views[f'CorridorLevel{level}'] = ((4.4, 0, z+1.58), (18, 0, z+1.43), 18)
            elevator_x = (self.e['alcove_x_range'][1]+self.length)/2
            views[f'ElevatorLevel{level}'] = ((elevator_x, .90, z+1.62), (elevator_x, -1.05, z+1.50), 20)
        transforms = UsdGeom.XformCache()
        for stair in self.c['stairs']:
            transform = transforms.GetLocalToWorldTransform(self.stage.GetPrimAtPath('/World/Stairs/'+stair['name']))
            eye = transform.Transform(Gf.Vec3d((self.m['stair_flight_width']+self.e['stair_center_gap'])/2, .55, 1.55))
            target = transform.Transform(Gf.Vec3d((self.m['stair_flight_width']+self.e['stair_center_gap'])/2, 5.1, -1.45))
            views['StairDown'+stair['name']] = (tuple(eye), tuple(target), 18)
        for name, item in self.c['spawn_points'].items():
            prim = self.group('/World/SpawnPoints/'+name, item['position'], item['yaw_deg'])
            prim.CreateAttribute('e10:robotBaseHeight', Sdf.ValueTypeNames.Double).Set(.55)
        return views

    def build(self):
        self.floor('Corridor', 0, self.length, -self.w/2, self.w/2, border=True)
        self.ceiling('Corridor', 0, self.length, -self.w/2, self.w/2, self.h)
        self.walls()
        for d in self.c['doors']:
            self.door(d)
        for s in self.c['stairs']:
            self.stairs(s)
        self.end_window('StartWindow', 0)
        self.end_window('EndWindow', self.length)
        for i, (x, side) in enumerate(self.c['extinguishers']):
            self.extinguisher(f'Extinguisher_{i:02}', x, side)
        self.lobby()
        dome = UsdLux.DomeLight.Define(self.stage, '/World/Lights/Ambient')
        dome.CreateIntensityAttr(180)
        dome.CreateColorAttr(Gf.Vec3f(.80, .86, 1))
        for i in range(13):
            self.downlight(f'Ceiling_{i:02}', 1.2+i*3)
        for i in range(6):
            x = 5.0+i*5.4
            self.cylinder(f'/World/Fixtures/SmokeDetector_{i}', (x, .35, self.h-.035), .045, .035, 'White', False)
            self.box(f'/World/Fixtures/WallConduit_{i}', (x, self.w/2-.008, 2.35), (4.5, .016, .014), 'DoorWhite', False)
        self.poster('/World/Fixtures/Quiet', (4.5, .86, .35), .25, .50, 'QuietSign', 90)
        self.box('/World/Fixtures/QuietStand', (4.5, .89, .30), (.045, .27, .60), 'DoorWhite')
        self.box('/World/Fixtures/FireCabinet', (8.4, self.w/2-.025, .92), (.45, .035, 1.16), 'Metal', False)
        self.rod('/World/Fixtures/FireAlarm', (8.4, self.w/2-.04, 1.37), (8.4, self.w/2-.08, 1.37), .055, 'Red', False)
        self.exterior_manifest = build_exterior(self)
        self.lighting_manifest = build_lighting(self)
        views = self.review_views()
        self.levels_manifest = build_levels(self)
        self.stage.GetRootLayer().Save()
        return views


def main():
    config = json.loads(CONFIG.read_text())
    filename = OUT/'cbnu_e10.usda'
    if filename.exists():
        filename.unlink()
    builder = Builder(config, filename)
    views = builder.build()
    overview_path = OUT/'cbnu_e10_overview.usda'
    if overview_path.exists():
        overview_path.unlink()
    stage = Usd.Stage.CreateNew(str(overview_path))
    stage.GetRootLayer().subLayerPaths = ['cbnu_e10.usda']
    UsdGeom.Imageable(stage.OverridePrim('/World/Ceilings')).CreateVisibilityAttr('invisible')
    UsdGeom.Imageable(stage.OverridePrim('/World/Exterior')).CreateVisibilityAttr('invisible')
    UsdGeom.Imageable(stage.OverridePrim('/World/Levels')).CreateVisibilityAttr('invisible')
    stage.GetRootLayer().customLayerData = {'purpose': 'Inspection only; ceiling collision remains active. Use cbnu_e10.usda for simulation.'}
    stage.GetRootLayer().Save()
    manifest = {
        'world': str(filename.relative_to(ROOT)),
        'config_sha256': hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        'stage_sha256': hashlib.sha256(filename.read_bytes()).hexdigest(),
        'prims': sum(1 for _ in builder.stage.Traverse()),
        'collision_prims': sum(1 for p in builder.stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)),
        'views': {name: {'eye': eye, 'target': target, 'focal_length': focal} for name, (eye, target, focal) in views.items()},
        'camera_prims': sum(p.IsA(UsdGeom.Camera) for p in builder.stage.Traverse()),
        'containment_adjustments': builder.containment_adjustments,
        'exterior': builder.exterior_manifest,
        'lighting': builder.lighting_manifest,
        'levels': builder.levels_manifest,
        'limitations': config['limitations'],
    }
    (OUT/'build_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k: manifest[k] for k in ['world', 'prims', 'collision_prims']}, indent=2))


if __name__ == '__main__':
    main()
