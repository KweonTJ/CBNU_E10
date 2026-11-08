"""Photo-referenced building envelope around the preserved E10 corridor stage."""
import json
from pathlib import Path
from pxr import Gf, UsdGeom, UsdLux

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'worlds/cbnu_e10/config/exterior.json'


class Envelope:
    def __init__(self, builder):
        self.b = builder
        self.source = json.loads(CONFIG.read_text())
        self.c = self.source['estimated_geometry']
        self.base = '/World/Exterior'
        builder.group(self.base)
        self.z0 = -(self.c['surveyed_level']-1)*self.c['floor_to_floor']
        self.top = self.z0+self.c['levels']*self.c['floor_to_floor']

    def panel(self, path, start, end, z0, z1, material='Brick', collision=True):
        """Wall segment with metric UVs, avoiding stretched brick textures."""
        b = self.b
        x0, y0 = start
        x1, y1 = end
        t = self.c['cladding_thickness']
        length = ((x1-x0)**2+(y1-y0)**2)**.5
        horizontal = abs(y1-y0)<1e-6
        # These axes-aligned segments form an enclosed perimeter; all cladding
        # stays clear of the surveyed corridor and the two stair footprints.
        size = (length, t, z1-z0) if horizontal else (t, length, z1-z0)
        b.box(path+'/Body', ((x0+x1)/2, (y0+y1)/2, (z0+z1)/2), size, 'BrickBase' if material=='Brick' else material, collision)
        if material=='Brick':
            for sign in [-1, 1]:
                dx, dy = (0, sign*(t/2+.0008)) if horizontal else (sign*(t/2+.0008), 0)
                pts = [(x0+dx,y0+dy,z0),(x1+dx,y1+dy,z0),(x1+dx,y1+dy,z1),(x0+dx,y0+dy,z1)]
                b.mesh(path+f'/BrickSurface_{sign+1}', pts, [[0,1,2,3]], 'Brick',
                       uv=[(0,z0/.6),(length/1.2,z0/.6),(length/1.2,z1/.6),(0,z1/.6)])

    def window(self, path, center, width, height, normal, door=False):
        """Framed, opaque reflective glazing closes a real facade opening."""
        b = self.b
        x, y, z = center
        horizontal = abs(normal[1])>0
        def box(name, u, depth, zz, su, sd, sz, mat, collision=True):
            pos = (x+u, y+normal[1]*depth, z+zz) if horizontal else (x+normal[0]*depth, y+u, z+zz)
            size = (su, sd, sz) if horizontal else (sd, su, sz)
            b.box(path+'/'+name, pos, size, mat, collision)
        box('Glass', 0, 0, 0, width, .055, height, 'FacadeGlass')
        for sign in [-1,1]:
            box(f'Jamb_{sign+1}', sign*(width/2-.026), .035, 0, .052, .10, height, 'Aluminum')
        for label, zz in [('Top', height/2-.025), ('Bottom', -height/2+.025)]:
            box(label, 0, .035, zz, width, .10, .05, 'Aluminum')
        box('VerticalMullion', 0, .039, 0, .045, .10, height, 'Aluminum')
        box('OpeningRail', 0, .04, -height*.19, width, .10, .045, 'Aluminum')
        if door:
            for sign in [-1,1]:
                box(f'Pull_{sign+1}', sign*.11, .11, -.1, .025, .045, .38, 'Metal', False)

    def elevation(self, name, start, end, normal, count, width, entrance=False):
        b, c = self.b, self.c
        x0,y0 = start
        x1,y1 = end
        length = ((x1-x0)**2+(y1-y0)**2)**.5
        ux,uy = (x1-x0)/length,(y1-y0)/length
        pitch = length/count
        points = lambda u: (x0+u*ux,y0+u*uy)
        for level in range(c['levels']):
            floor = self.z0+level*c['floor_to_floor']
            p = self.base+f'/Facades/{name}/Level_{level+1}'
            for i in range(count):
                center = (i+.5)*pitch
                low,high = center-width/2,center+width/2
                # Split at openings, leaving no opaque backing slab behind windows.
                if i==0:
                    self.panel(p+'/Pier_00',points(0),points(low),floor,floor+c['floor_to_floor'])
                else:
                    previous=(i-.5)*pitch+width/2
                    self.panel(p+f'/Pier_{i:02}',points(previous),points(low),floor,floor+c['floor_to_floor'])
                is_door = entrance and level==0 and i in [4,5]
                sill = .02 if is_door else c['window_sill']
                height = 2.65 if is_door else c['window_height']
                if sill>0:
                    self.panel(p+f'/Sill_{i:02}',points(low),points(high),floor,floor+sill)
                self.panel(p+f'/Spandrel_{i:02}',points(low),points(high),floor+sill+height,floor+c['floor_to_floor'])
                xx,yy=points(center)
                self.window(p+f'/Window_{i:02}',(xx,yy,floor+sill+height/2),width,height,normal,is_door)
            self.panel(p+'/LastPier',points((count-.5)*pitch+width/2),points(length),floor,floor+c['floor_to_floor'])

    def tower(self, name, x0, x1, y, normal=(0,-1), strips=1):
        b,c=self.b,self.c
        p=self.base+'/Facades/'+name
        width=x1-x0
        glass_width=1.30 if strips==1 else 1.05
        center=(x0+x1)/2
        self.panel(p+'/LeftBrick',(x0,y),(center-glass_width/2,y),self.z0,self.top)
        self.panel(p+'/RightBrick',(center+glass_width/2,y),(x1,y),self.z0,self.top)
        for level in range(c['levels']):
            f=self.z0+level*c['floor_to_floor']
            # Central blue glass runs through floor divisions, as in the official photo.
            self.window(p+f'/VerticalGlass_{level+1}',(center,y-.12,f+c['floor_to_floor']/2),glass_width,c['floor_to_floor'],normal)
            # Shallow belt courses bind the two brick piers into a single tower.
            for side,lo,hi in [('L',x0,center-glass_width/2),('R',center+glass_width/2,x1)]:
                b.box(p+f'/BrickBelt_{level}_{side}',((lo+hi)/2,y-.115,f+c['floor_to_floor']-.05),(hi-lo,.035,.10),'BrickAccent',False)
            if width>4:
                for side,xx in [('L',x0+.72),('R',x1-.72)]:
                    if level==c['levels']-1 and side=='L':
                        continue
                    # Small dark inserts on the brick pier are decorative recesses.
                    self.window(p+f'/SmallWindow_{level}_{side}',(xx,y-.117,f+1.75),.70,1.35,normal)
        b.poster(p+'/BuildingNumber',(x0+.95,y-.131,self.top-2.2),1.70,.90,'BuildingSign')

    def wings(self):
        """Fill in room-side structure without placing a slab across stair voids."""
        b,c=self.b,self.c
        p=self.base+'/RoomWings'
        b.group(p)
        w=b.w/2
        room_x0,room_x1=0,b.length
        stair_bay=2*b.m['stair_flight_width']+b.e['stair_center_gap']+2*b.e['wall_thickness']
        for side,outer in [(-1,c['main_front_y']+.13),(1,c['rear_y']-.13)]:
            inner=side*(w+b.e['wall_thickness'])
            ya,yb=sorted((inner,outer))
            holes=[]
            for stair in b.c['stairs']:
                if stair['side']==side:
                    holes.append((stair['x']-stair_bay/2,stair['x']+stair_bay/2))
            if side==-1:
                holes.append(tuple(b.e['alcove_x_range']))
            cursor=room_x0
            for i,(lo,hi) in enumerate(sorted(holes)+[(room_x1,room_x1)]):
                if lo>cursor:
                    b.box(p+f'/Floor_{side+1}_{i}',((lo+cursor)/2,(ya+yb)/2,-.08),(lo-cursor,yb-ya,.16),'Concrete')
                    b.box(p+f'/Ceiling_{side+1}_{i}',((lo+cursor)/2,(ya+yb)/2,b.h+.08),(lo-cursor,yb-ya,.16),'Ceiling')
                cursor=hi
            # Subdivisions belong to unobserved, inaccessible room space.
            for i,xx in enumerate([7.5,11.5,15.5,19.5,23.5,27.5]):
                b.box(p+f'/Partition_{side+1}_{i}',(xx,(ya+yb)/2,b.h/2),(.12,yb-ya,b.h),'Wall')
        # Continuous foundation at ground level unifies the entire building mass.
        b.box(p+'/GroundFloorSlab',((c['x_min']+c['x_max'])/2,(c['rear_y']+c['near_tower_front_y'])/2,self.z0-.10),
              (c['x_max']-c['x_min'],c['rear_y']-c['near_tower_front_y'],.20),'Concrete')

    def roofs(self):
        b,c=self.b,self.c
        p=self.base+'/Roofs'
        b.group(p)
        sections=[('NearTower',c['x_min'],c['near_tower_end_x'],c['near_tower_front_y'],c['rear_y'],self.top+.25),
                  ('MainWing',c['near_tower_end_x'],c['far_tower_start_x'],c['main_front_y'],c['rear_y'],self.top),
                  ('FarTower',c['far_tower_start_x'],c['x_max'],c['far_tower_front_y'],c['rear_y'],self.top+.15)]
        for name,x0,x1,y0,y1,z in sections:
            b.box(p+'/'+name+'/Deck',((x0+x1)/2,(y0+y1)/2,z+.09),(x1-x0,y1-y0,.18),'Roof')
            for edge,start,end in [('Front',(x0,y0),(x1,y0)),('Rear',(x0,y1),(x1,y1)),('Left',(x0,y0),(x0,y1)),('Right',(x1,y0),(x1,y1))]:
                if z>self.top:
                    self.panel(p+'/'+name+'/'+edge+'UpperBand',start,end,self.top,z)
                self.panel(p+'/'+name+'/'+edge,start,end,z,z+c['parapet_height'])
                horizontal=abs(start[1]-end[1])<1e-6
                size=(abs(end[0]-start[0])+.06,.28,.08) if horizontal else (.28,abs(end[1]-start[1])+.06,.08)
                b.box(p+'/'+name+'/'+edge+'Coping',((start[0]+end[0])/2,(start[1]+end[1])/2,z+c['parapet_height']+.04),size,'Limestone')

    def build(self):
        b,c=self.b,self.c
        near,far=c['near_tower_end_x'],c['far_tower_start_x']
        self.elevation('MainFront',(near,c['main_front_y']),(far,c['main_front_y']),(0,-1),c['main_window_count'],c['main_window_width'],True)
        self.elevation('Rear',(c['x_min'],c['rear_y']),(c['x_max'],c['rear_y']),(0,1),12,1.80)
        self.elevation('WestEnd',(c['x_min'],c['near_tower_front_y']),(c['x_min'],c['rear_y']),(-1,0),4,1.45)
        self.elevation('EastEnd',(c['x_max'],c['far_tower_front_y']),(c['x_max'],c['rear_y']),(1,0),4,1.45)
        self.tower('NearTower',c['x_min'],near,c['near_tower_front_y'])
        self.tower('FarTower',far,c['x_max'],c['far_tower_front_y'])
        self.panel(self.base+'/Facades/NearReturn',(near,c['near_tower_front_y']),(near,c['main_front_y']),self.z0,self.top)
        self.panel(self.base+'/Facades/FarReturn',(far,c['far_tower_front_y']),(far,c['main_front_y']),self.z0,self.top)
        for level in range(c['levels']):
            f=self.z0+level*c['floor_to_floor']
            b.box(self.base+f'/FacadeBands/Front_{level}',((near+far)/2,c['main_front_y']-.19,f+2.78),(far-near,.48,.18),'Limestone')
            b.box(self.base+f'/FacadeBands/Rear_{level}',((c['x_min']+c['x_max'])/2,c['rear_y']+.15,f+2.78),(c['x_max']-c['x_min'],.34,.16),'Limestone')
        self.wings()
        self.roofs()
        ground=self.base+'/Ground'
        b.group(ground)
        b.box(ground+'/Site', (19.2,-1.0,self.z0-.24), (62,39,.22), 'SitePaving')
        b.box(ground+'/FrontWalk', (19.2,-10.1,self.z0-.055), (43,3.0,.11), 'Concrete')
        for i in range(44):
            b.box(ground+f'/PaverJoint_{i:02}',(-2.3+i,-10.1,self.z0+.001),(.008,3,.002),'Grout',False)
        for yy in [-11.60,-10.85,-10.10,-9.35,-8.60]:
            b.box(ground+'/LongJoint_'+str(round(abs(yy)*100)),(19.2,yy,self.z0+.001),(43,.008,.002),'Grout',False)
        entrance_x=near+5*(far-near)/c['main_window_count']
        b.box(self.base+'/Entrance/Canopy',(entrance_x,c['main_front_y']-.82,self.z0+2.95),(6.0,1.75,.18),'Limestone')
        b.box(self.base+'/Entrance/Fascia',(entrance_x,c['main_front_y']-1.66,self.z0+2.87),(6.0,.08,.16),'Aluminum',False)
        sun=UsdLux.DistantLight.Define(b.stage,self.base+'/Lighting/Sun')
        sun.CreateIntensityAttr(1800)
        sun.CreateAngleAttr(.53)
        sun.CreateColorAttr(Gf.Vec3f(1,.94,.84))
        sun.AddRotateXYZOp().Set(Gf.Vec3f(35,-25,0))
        return {'source':self.source,'ground_z':self.z0,'roof_z':self.top,'surveyed_corridor_z':0,
                'traversable_interior_levels':[3],'exterior_levels':c['levels']}


def build_exterior(builder):
    return Envelope(builder).build()
