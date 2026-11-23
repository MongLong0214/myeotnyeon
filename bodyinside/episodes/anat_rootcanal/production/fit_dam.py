"""Fit the isolation assembly to the saved DBCLS set, retaining the animation outside isolation."""
from pathlib import Path
import math
import json
import sys
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

EP = Path(__file__).resolve().parent.parent
sc = bpy.context.scene
sc.frame_set(156)
objects = sc.objects
hero = objects['M1 • enamel mantle']
body = objects['M1 • patent canal section']
surround = [objects[k] for k in ['P2 • registered neighbor','M2 • registered neighbor','FJ1253 • attached gingiva','FJ3289 • mandibular section']]
def hit(obj, start, direction):
    ok, v, _, _ = obj.ray_cast(Vector(start), Vector(direction))
    return np.array(v) if ok else None

def lingual(x,z):
    hits = [p[1] for o in [body,hero] if (p:=hit(o,(x,20,z),(0,-1,0))) is not None]
    return max(hits)

def vertices(obj, points):
    obj.data.vertices.foreach_set('co',np.asarray(points,dtype='f').ravel())
    obj.data.update()

def tube(obj,p,radius,sides):
    p=np.array(p)
    t=np.gradient(p,axis=0); t/=np.linalg.norm(t,axis=1)[:,None]
    ref=np.tile([0.,1.,0.],(len(p),1));ref[np.abs(t[:,1])>.94]=[1.,0,0]
    n=np.cross(t,ref);n/=np.linalg.norm(n,axis=1)[:,None]
    b=np.cross(t,n)
    theta=2*math.pi*np.arange(sides)/sides
    pts=p[:,None,:]+np.broadcast_to(radius,(len(p),))[:,None,None]*(n[:,None,:]*np.cos(theta)[None,:,None]+b[:,None,:]*np.sin(theta)[None,:,None])
    vertices(obj,pts)
wingpositions=[]
for side,sign in [('',-1),('.001',1)]:
    # Two posterior contact pads seat on the curved lingual cervical surface.
    zz=4.85
    xs=sign*np.linspace(2.70,4.28,26)
    curve=[]
    for j,x in enumerate(xs):
        u=j/(len(xs)-1);z=zz+.70*u
        y=lingual(x,z)
        curve.append((x, y+.155+1.62*u, z))
    tube(objects['Clamp jaw'+side],curve,np.linspace(.17,.29,26),18)
    x,y,z=curve[-1]
    w=(x,y+.31,z+.18)
    wingpositions.append(w)
    objects['Perforated clamp wing'+side].location=w
    objects['Perforated clamp wing'+side].scale=(.70,.57,.175)
    objects['Clamp forceps perforation'+side].location=(x+.20*sign,y+.30,z+.345)
a,b=map(np.array,wingpositions)
bow=[]
for u in np.linspace(0,1,54):
    pos=(1-u)*a+u*b
    pos[1]+=3.55*math.sin(math.pi*u)
    pos[2]+=.47+1.01*math.sin(math.pi*u)
    bow.append(pos)
tube(objects['Spring clamp bow'],bow,.22,12)
probe=objects['Clamp check forceps beak'];probe.animation_data_clear()
for f,h in [(150,.64),(152,.035),(155,.05),(164,6.4)]:
    probe.location=(a[0]+.02,a[1]-.08,a[2]+.14+h)
    probe.keyframe_insert('location',frame=f)
for f,on in [(0,False),(150,True),(165,False)]:
    for k in ('hide_render','hide_viewport'):
        setattr(probe,k,not on);probe.keyframe_insert(k,frame=f)
# Drape the sheet over the occlusal contours of the two neighboring teeth.
# The inner edge follows the curved shell. The cutaway exposes the working lumen.
verts=[];na=109;nr=18
for j in range(nr):
    u=j/(nr-1)
    for i in range(na):
        angle=-.18+(math.pi+.36)*i/(na-1);c,s=math.cos(angle),math.sin(angle)
        base=[p for o in (body,hero) if (p:=hit(o,(12*c,12*s,3.85),(-c,-s,0))) is not None]
        r=max((p[0]*c+p[1]*s for p in base),default=5.55)
        radius=r+(15.5-r)*u
        x,y=radius*c,radius*s
        # The stretched rubber rests on high points and tents across narrow gaps.
        roof=max([3.70]+[p[2]+.28 for o in surround for dx,dy in ((0,0),(.18,0),(-.18,0),(0,.18),(0,-.18)) if (p:=hit(o,(x+dx,y+dy,17),(0,0,-1))) is not None])
        lift=1-math.exp(-u*18)
        slope=3.89+5.12*(1-math.exp(-u*4.2))+1.34*u
        z=max(roof*lift+3.89*(1-lift),slope)+(.18*math.sin(7*angle+5*u)+.15*math.cos(13*angle-6*u))*math.sin(math.pi*u)
        verts.append((x,y,z))
vertices(objects['Fenestrated green rubber dam • section'],verts)
tube(objects['Rolled dam margin'],verts[:na],.14,12)
tube(objects['Dental dam wire frame'],verts[-na:],.19,12)
sc.frame_set(0)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
