"""Final Cycles surface, scan and lens pass, called by refine.py."""
from pathlib import Path
import numpy as np

ASSETS = OUT / 'assets'


def texture_surface(material, file, scale):
    tree = material.node_tree
    uv = tree.nodes.new('ShaderNodeTexCoord')
    size = tree.nodes.new('ShaderNodeVectorMath')
    size.operation = 'SCALE'
    tree.links.new(uv.outputs['Object'], size.inputs[0])
    size.inputs['Scale'].default_value = scale
    tex = tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(file), check_existing=True)
    tex.image.colorspace_settings.name = 'Non-Color'
    tex.projection = 'BOX'
    tex.projection_blend = .28
    tree.links.new(size.outputs[0], tex.inputs[0])
    return tex.outputs['Color']


def surface_relief(mat, file, scale, distance, strength):
    tree = mat.node_tree
    bs = tree.nodes.get('Principled BSDF')
    normal = bs.inputs['Normal'].links[0].from_socket
    micro = node(tree, 'ShaderNodeBump', Normal=normal, Strength=strength,
                 Distance=distance, Height=texture_surface(mat, file, scale))
    tree.links.new(micro.outputs[0], bs.inputs['Normal'])
    tree.links.new(micro.outputs[0], bs.inputs['Coat Normal'])


def roughness(mat, file, scale, low, high):
    tree = mat.node_tree
    bs = tree.nodes.get('Principled BSDF')
    variation = node(tree, 'ShaderNodeMapRange', Value=texture_surface(mat, file, scale))
    variation.inputs['To Min'].default_value = low
    variation.inputs['To Max'].default_value = high
    tree.links.new(variation.outputs[0], bs.inputs['Roughness'])


def surgical_field():
    for ob in (flap, bank):
        # Carry the outer margin into the cheek beyond the field of view.
        # Keep the freely moving incision lip and both needle bites in place.
        for i in range(len(ob.data.vertices)):
            u, s = (i // 89) / 32, (i % 89) / 88
            outer = max(0, (u-.50)/.50)**2
            anterior = max(0, (.10-s)/.10)**2
            posterior = max(0, (s-.90)/.10)**2
            delta = V(((21 if ob == flap else -9)*outer,
                       7*posterior-8*anterior,
                       (2.7 if ob == flap else -2)*outer-.8*(posterior+anterior)))/1000
            for sk in ob.data.shape_keys.key_blocks:
                sk.data[i].co += delta
    bed_mat = O['Alveolar bed, cortical rim and contiguous vestibule'].data.materials[0]
    for m in (gum, raw, bed_mat):
        surface_relief(m, ASSETS/'leather_red_02_disp_1k.jpg', 61, .00019, .38)
        roughness(m, ASSETS/'leather_red_02_rough_1k.jpg', 61, .19, .48)
        bs = m.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Coat Weight'].default_value = .27
        bs.inputs['Coat Roughness'].default_value = .155
    for obj in (flap, bank):
        # Bind the vascular pigment to the rest cage so it travels with the flap.
        m = gum.copy()
        m.name = obj.name + ' • superficial vascular plexus'
        obj.data.materials[0] = m
        uv = obj.data.uv_layers.new(name='Vessels in resting epithelium')
        rest = obj.data.shape_keys.key_blocks[0]
        for i, loop in enumerate(obj.data.loops):
            p = rest.data[loop.vertex_index].co*1000
            uv.data[i].uv = ((p.x-12)/46, (p.y+59)/45)
        nt=m.node_tree
        bs=nt.nodes.get('Principled BSDF')
        tex=nt.nodes.new('ShaderNodeTexImage')
        tex.image=bpy.data.images.load(str(ASSETS/'subsurface_vessels.png'),check_existing=True)
        tex.image.colorspace_settings.name='Non-Color'
        base_color=bs.inputs['Base Color'].links[0].from_socket
        mask=node(nt,'ShaderNodeMixRGB',Fac=tex.outputs['Color'],Color1=base_color,
                  Color2=(.112,.013,.029,1))
        nt.links.new(mask.outputs[0],bs.inputs['Base Color'])
    for m,scale,dist in [(bone,53,.00023),(dentin,118,.000064),(liner,76,.00014)]:
        surface_relief(m, ASSETS/'coral_gravel_disp_1k.jpg', scale, dist, .45)
    for m,lo,hi in ((steel,.12,.28),(satin,.19,.40)):
        roughness(m,ASSETS/'Metal032_1K-JPG_Roughness.jpg',124,lo,hi)

    # A blood film breaks on the rough cementum where the roots release from
    # their periodontal attachments. Preserve the freshly cut dentin face.
    for name in ('Superior root segment','Inferior root segment'):
        obj=O[name]
        m=cement.copy();m.name='Moist cementum on '+name.lower()
        for i,slot in enumerate(obj.data.materials):
            if slot==cement: obj.data.materials[i]=m
        nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
        tex=nt.nodes.new('ShaderNodeTexCoord')
        coords=node(nt,'ShaderNodeVectorMath');coords.operation='MULTIPLY'
        nt.links.new(tex.outputs['Generated'],coords.inputs[0])
        coords.inputs[1].default_value=(2.6,.94,2.3)
        gr=node(nt,'ShaderNodeTexNoise',Vector=coords.outputs[0],Scale=3.6,Detail=4.0,Distortion=.47)
        cover=ramp(nt,gr.outputs[0],[(.40,(0,0,0)),(.57,(.10,.10,.10)),(.67,(.9,.9,.9))])
        basec=bs.inputs['Base Color'].links[0].from_socket
        mix=node(nt,'ShaderNodeMixRGB',Fac=cover,Color1=basec,Color2=(.15,.012,.019,1))
        nt.links.new(mix.outputs[0],bs.inputs['Base Color'])
        bs.inputs['Coat Weight'].default_value=.62


def scanned_tools():
    for name in ('Willinger','Langenbeck'):
        data=np.load(str(ASSETS/(name+'.npz')))
        if name=='Willinger':
            rig=O['Periosteal elevator']
            for child in list(rig.children): disable(child)
            ob=mesh('3D-COSI • Willinger periosteal elevator',data['vertices']*.84,
                    data['faces'].tolist(),satin,rig)
            visible(ob,[(9.85,13.10)])
            ob.rotation_euler.z=math.radians(77)
        else:
            # A separate assistant pass takes up the reflected outer lip.
            rig=link('Assistant • buccal retraction')
            ob=mesh('3D-COSI • small Langenbeck retractor',data['vertices']*.72,
                    data['faces'].tolist(),satin,rig)
            visible(ob,[(12.42,18.81)])
            # Local Y follows the handle, local Z follows the bent blade.
            from mathutils import Matrix
            y=V((.85,-.46,.24)).normalized()
            z0=V((-.18,-.12,.98));x=y.cross(z0).normalized();z=x.cross(y).normalized()
            rig.rotation_mode='QUATERNION'
            rig.rotation_quaternion=Matrix((x,y,z)).transposed().to_quaternion()
            for t,p in [(12.42,(52,-51,46)),(13.02,(44.1,-44.8,35.5)),(13.9,(40.7,-44.65,34.0)),
                        (17.75,(40.9,-44.60,33.8)),(18.25,(43.2,-46.0,36.8)),(18.80,(56,-53,51))]:
                key(rig,'location',t,world(p))
    # Narrow satin band between the turbine shell and its cap, as on dental handpieces.
    ring=lathe('Turbine head cap • satin edge',[(9.59,2.08),(9.69,2.07),(9.73,2.02)],satin,O['Surgical handpiece'])
    visible(ring,[(0,3),(13,23.08),(27,28.06)])


def clot_finish():
    with bpy.data.libraries.load(str(ASSETS/'clot_material.blend'),link=False) as (source,target):
        target.materials=['Fresh Wet Blood Clot']
    m=target.materials[0]
    group=next(n for n in m.node_tree.nodes if n.type=='GROUP')
    for name, value in {'Clot Color':(.080,.0018,.007,1),'Deep Color':(.023,.0006,.002,1),
                        'Blood Color':(.15,.003,.010,1),'Bright Color':(.24,.016,.024,1),
                        'Bump Distance':.00019,'Displacement Scale':0,
                        'Coat Weight':.36,'Wet Roughness':.18,'Dry Roughness':.35,
                        'Coagulate Scale':13,'Reflection Factor':.025}.items():
        group.inputs[name].default_value=value
    # The source uses object-space coordinates on a metre-scale sphere.
    # Use the clot's bounding box so its fibre and coagulation patterns resolve in millimetres.
    ng=group.node_tree
    coordinate=next(n for n in ng.nodes if n.type=='TEX_COORD')
    link=coordinate.outputs['Object'].links[0]
    ng.links.new(coordinate.outputs['Generated'],link.to_socket)
    group.inputs['Bump Strength'].default_value=.38
    group.inputs['Bump Distance'].default_value=.00032
    ob=O['Consolidating clot below posterior suture gap']
    remat(ob,m)
    # Final lens position isolates the clot and apposed margin beside the knot.
    cam=sorted(S.timeline_markers,key=lambda mk:mk.frame)[-1].camera
    for t,at,dist,lens in [(41.05,(29.6,-34.0,38.25),29.5,58),
                          (42.55,(30.0,-32.0,37.60),28.1,61),
                          (43.95,(30.05,-31.80,37.62),27.5,61)]:
        direction=V((.28,-.17,.95)).normalized()
        loc=world(at)+direction*dist/1000
        rot=(world(at)-loc).to_track_quat('-Z','Y') @ Quaternion((0,0,1),.048)
        key(cam,'location',t,loc);key(cam,'rotation_quaternion',t,rot)
        key(cam.data,'lens',t,lens);key(cam.data,'dof.focus_distance',t,dist/1000)
    for mk in S.timeline_markers:
        if mk.camera: mk.camera.data.dof.aperture_fstop=86


def finish_surfaces():
    surgical_field()
    scanned_tools()
    contact_details()
    clot_finish()
    clinical_colour()
    incision_profile()
    clot_surface_relief()
    continuous_bone_fulcra()
    keylight=O['Operatory lamp • reflected key'].data
    keylight.size=.0078
    keylight.size_y=.0125
    O['Broad diffuse fill'].data.energy*=.78
    O['Cavity fill'].data.energy*=.84
    S.cycles.samples=14
    bpy.ops.file.pack_all()


def contact_details():
    # Give saline a readable air interface and keep the jet outside the flute silhouette.
    fluid=water.copy();fluid.name='Aerated edge of the irrigation stream'
    bs=fluid.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Transmission Weight'].default_value=.54
    bs.inputs['Coat Weight'].default_value=.40
    drill=O['Surgical handpiece']
    for ob in S.objects:
        if ob.name.startswith(('Atomised saline','Free irrigant jet')):
            remat(ob,fluid)
    arc=[(2.14,.76,4.77),(1.97,.69,4.18),(1.79,.65,3.60),
         (1.58,.54,2.99),(1.36,.42,2.3),(1.11,.33,1.69),(.83,.23,1.13),(.41,.12,.61)]
    jet=tube('Continuous saline core',arc,.168,fluid,drill,radii=(.9,1,.85,.79,.74,.70,.49,.21))
    visible(jet,[(0,3),(13.60,17.96),(19.29,22.78),(27.22,27.88)])
    # Small drops close to the wet contact plane, with a directional specular streak.
    for i in range(15):
        a=2*pi*(i+.21)/15;span=rng.uniform(1.8,4.1);height=rng.uniform(.48,1.8)
        o=organic('Impact droplets in the irrigation fan',(.2,0,.52),(1,1,1),fluid,drill,i)
        intervals=[]
        for a0,a1 in ((0,2.97),(13.60,17.96),(19.29,22.78)):
            t=a0+(i%7)*.046
            while t<a1-.13:
                life=min(rng.uniform(.15,.24),a1-t);sz=rng.uniform(.10,.18)
                for f in (0,.5,1):
                    key(o,'location',t+life*f,V((cos(a)*(.61+span*f),sin(a)*(.61+span*f),.45+height*sin(pi*f)+.23*f))/1000,'LINEAR')
                    key(o,'scale',t+life*f,(sz*(1-.34*f),sz*.74,sz*(1.6-.45*f)),'LINEAR')
                intervals.append((t,t+life));t+=rng.uniform(.37,.61)
        visible(o,intervals)
    # A damp, fenestrated film spreads on the actual milled surface in the opening.
    # Keep it local to the cortical contact, separate from the exposed canal.
    lip=O['Cutaway lip at the opening bur contact']
    m=bone.copy();m.name='Milled cortex under a thin saline film'
    nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
    bs.inputs['Coat Weight'].default_value=.88
    bs.inputs['Coat Roughness'].default_value=.095
    remat(lip,m)
    for k in range(6):
        a=2*pi*k/6+.2; pts=[]
        for j in range(7):
            phase=a+j*.13; r=.70+.35*sin(j*.6+k)
            pts.append((r*cos(phase),r*sin(phase),.38+.08*sin(phase*3)))
        track=tube('Peripheral saline on the milled cortex',pts,.078,fluid,lip,radii=(.18,.59,.92,1,.72,.39,.10))
        visible(track,[(0,3)])
    # The retromolar pad joins the distal wound margin at a shallow angle.
    for o in S.objects:
        if o.name.startswith('Retromolar mucosal fold'):
            o.location.z-=.0014
            o.scale.x*=1.22
    # Vary the cut face independently from intact enamel. A small pulp
    # space appears only on the transverse dentin, in the core of the section.
    nt=dentin.node_tree;bs=nt.nodes.get('Principled BSDF')
    uv=nt.nodes.new('ShaderNodeTexCoord').outputs['Generated']
    xyz=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(uv,xyz.inputs[0])
    def distance_component(coord,center,stretch):
        sub=nt.nodes.new('ShaderNodeMath');sub.operation='SUBTRACT'
        nt.links.new(xyz.outputs[coord],sub.inputs[0]);sub.inputs[1].default_value=center
        sq=nt.nodes.new('ShaderNodeMath');sq.operation='MULTIPLY';nt.links.new(sub.outputs[0],sq.inputs[0]);nt.links.new(sub.outputs[0],sq.inputs[1])
        mul=nt.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';nt.links.new(sq.outputs[0],mul.inputs[0]);mul.inputs[1].default_value=stretch
        return mul.outputs[0]
    dx=distance_component('X',.52,1.1);dz=distance_component('Z',.53,.66)
    add=nt.nodes.new('ShaderNodeMath');add.operation='ADD';nt.links.new(dx,add.inputs[0]);nt.links.new(dz,add.inputs[1])
    center=ramp(nt,add.outputs[0],[(0,(1,1,1)),(.003,(.91,.91,.91)),(.008,(.09,.09,.09)),(.011,(0,0,0))])
    src=bs.inputs['Base Color'].links[0].from_socket
    tint=node(nt,'ShaderNodeMixRGB',Fac=center,Color1=src,Color2=(.146,.025,.022,1))
    nt.links.new(tint.outputs[0],bs.inputs['Base Color'])


def clinical_colour():
    deep=O['Posterior oral lining'].data.materials[0]
    mbed=O['Alveolar bed, cortical rim and contiguous vestibule'].data.materials[0]
    skin_materials=[(gum,'attached',.34),(flap.data.materials[0],'attached',.39),
                    (bank.data.materials[0],'attached',.39),(raw,'lining',.34),
                    (deep,'lining',.23),(mbed,'lining',.29)]
    for m,region,weight in skin_materials:
        nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
        path=ASSETS/f'clinical_{region}.png'
        tex=texture_surface(m,path,94 if region=='attached' else 74)
        tex.node.image.colorspace_settings.name='sRGB'
        orig=bs.inputs['Base Color'].links[0].from_socket
        # Preserve the radial bone/soft tissue transition in the socket.
        if m==mbed:
            tissue=next(n for n in nt.nodes if n.type=='ATTRIBUTE')
            mask=node(nt,'ShaderNodeMapRange',Value=tissue.outputs['Fac'])
            for k,v in [('From Min',.73),('From Max',.94),('To Min',0),('To Max',weight)]:
                mask.inputs[k].default_value=v
            amount=mask.outputs[0]
        else:
            amount=weight
        mix=node(nt,'ShaderNodeMixRGB',Fac=amount,Color1=orig,Color2=tex)
        # Modulate deep lining and raw periosteum with the photographed grain,
        # retaining their darker blood supply and the shadow inside the field.
        if region=='lining': mix.blend_type='SOFT_LIGHT'
        nt.links.new(mix.outputs[0],bs.inputs['Base Color'])
        value=node(nt,'ShaderNodeRGBToBW',Color=tex).outputs[0]
        relief=node(nt,'ShaderNodeBump',Normal=bs.inputs['Normal'].links[0].from_socket,
                    Height=value,Distance=.00011,Strength=.28)
        nt.links.new(relief.outputs[0],bs.inputs['Normal'])
        nt.links.new(relief.outputs[0],bs.inputs['Coat Normal'])
    # Focus the opening on the bur, the short crossing irrigation jet, and the canal beneath it.
    cam=sorted(S.timeline_markers,key=lambda mk:mk.frame)[0].camera
    key(cam.data,'lens',0,61);key(cam.data,'lens',2.95,65)
    # Concentrated wash is pale and translucent at the cannula end, then fresh
    # capillary blood advances over the same animated liquid surface.
    liquid=O['Continuous socket meniscus • refill and saline wash'].data.materials[0]
    nt=liquid.node_tree;bs=nt.nodes.get('Principled BSDF')
    mix=bs.inputs['Base Color'].links[0].from_node
    colored=mix.inputs[2].links[0].from_node
    for el,col in zip(colored.color_ramp.elements,[(.33,.056,.069),(.72,.26,.29),(.86,.51,.48)]):
        el.color=(*col,1)
    gloss=bs.inputs['Transmission Weight'].links[0].from_node
    gloss.inputs['To Max'].default_value=.31


def incision_profile():
    from mathutils import Matrix
    blade=O['No. 15 scalpel']
    blade.animation_data_clear()
    for t,y,clearance in [(7,-47,5.8),(7.36,-43.8,.24),(7.52,-42.8,-.16),
                          (8.35,-37.3,-.23),(9.0,-32.85,-.22),(9.6,-27.65,-.10),
                          (9.83,-26.6,1.05),(10.13,-25,8.2)]:
        p=margin(max(0,min(1,(y+44)/17)));p.y=y;p.z+=clearance
        z=V((-.47,-.64,.61+.06*sin(t*2))).normalized()
        camera_direction=V((.54,-.22,.8)).normalized()
        yaxis=(camera_direction-camera_direction.dot(z)*z).normalized()
        xaxis=yaxis.cross(z).normalized()
        rot=Matrix((xaxis,yaxis,z)).transposed().to_quaternion()
        key(blade,'location',t,world(p))
        key(blade,'rotation_quaternion',t,rot)
    # Use a shallow fluid cross-section. The free film is measured on each
    # deformed lip rather than connecting a static curve across the wound.
    for ob in list(S.objects):
        if ob.name.startswith(('Capillary welling in the incision','Wicking film at raw margin')):
            disable(ob)
    times=[7.32,7.52,7.82,8.08,8.35,8.64,8.92,9.24,9.58,9.87,
           10.17,10.50,10.83,11.14,11.46,11.80,12.14,12.49,12.82,36.62,37.06,37.5]
    rows=tuple(range(14,74))
    for surface,polarity in [(flap,1),(bank,-1)]:
        forms=[]
        keys=surface.data.shape_keys.key_blocks
        basis=keys[0]
        for t in times:
            S.frame_set(frame(t))
            pts=[]
            for j in rows:
                # Physical surface normal in current pose. The base table and
                # every shape key are in the same mm coordinate system.
                def point(i,j):
                    n=i*89+j
                    initial=basis.data[n].co.copy();p=initial.copy()
                    for k in list(keys)[1:]:
                        if k.value: p+=(k.data[n].co-initial)*k.value
                    return p*1000
                edge=point(0,j)
                inward=(point(1,j)-edge).normalized()
                tangent=(point(0,j+1)-point(0,j-1)).normalized()
                normal=inward.cross(tangent).normalized()*polarity
                origin_y=basis.data[j].co.y*1000
                progress=min(1,max(0,(-43.6+(t-7.37)*6.96-origin_y)/.64))
                width=(.26+.13*sin(j*.50+polarity)+.11*sin(j*.89))*(.75 if polarity<0 else .88)
                width*=progress
                # A few slightly wider patches are where capillaries empty onto the cut.
                width+=progress*.25*sum(exp(-((j-k)/1.65)**2) for k in (22,37,61))
                for u in (0,.23,.59,1):
                    h=progress*(.009+.042*sin(pi*u))-.065*(1-progress)
                    pts.append(edge+inward*(width*u+.015)+normal*h)
            forms.append(pts)
        faces=[(4*j+i,4*j+i+1,4*j+i+5,4*j+i+4) for j in range(len(rows)-1) for i in range(3)]
        film=mesh('Surface blood film on '+surface.name,forms[0],faces if polarity==1 else [f[::-1] for f in faces],blood)
        visible(film,[(7.36,37.48)])
        film.shape_key_add(name='Uncut epithelium')
        for j in range(1,len(times)):
            keys_at=[(times[j-1],0),(times[j],1)]
            if j>1:keys_at.insert(0,(times[0],0))
            if j+1<len(times):keys_at.append((times[j+1],0))
            deform(film,f'Film at {times[j]:.2f}s',forms[j],keys_at)
    S.frame_set(1)


def clot_surface_relief():
    # Use an irregular upper surface without a polar vertex at the centre of
    # the specular highlight. Broad lobes sit beneath finer fibrin ridges.
    clot=O['Consolidating clot below posterior suture gap']
    imported=clot.data.materials[0]
    def height(x,y):
        q=(x/2.97)**2+(y/5.4)**2
        broad=noise.noise(V((x*.91+1.9,y*.82,2.92)))
        ridge=noise.turbulence(V((x*2.15+.82,y*1.65-.37,1.93)),3,False)
        envelope=max(0,1-q)**.56
        return 1.17*envelope+envelope*(.30*broad+.16*ridge+.060*sin(x*4.2+y*1.15+3*broad))
    points=[];faces=[]
    n=72
    for j in range(n+1):
        a=-1+2*j/n
        for i in range(n+1):
            b=-1+2*i/n
            x=2.97*b*math.sqrt(1-.50*a*a)
            y=5.4*a*math.sqrt(1-.50*b*b)
            points.append((x,y,height(x,y)))
    for j in range(n):
        for i in range(n):
            q=j*(n+1)+i
            faces.append((q,q+1,q+n+2,q+n+1))
    cap=mesh('Clot upper surface • fibrin relief',points,faces,imported)
    clot.data=cap.data
    bpy.data.objects.remove(cap,do_unlink=True)
    solid=clot.modifiers.new('Dark lower clot body','SOLIDIFY')
    solid.thickness=.00116;solid.offset=-1
    # Retain the survey material's coagulation texture. Add a calibrated
    # blood BSDF for the larger wet surface and soften the operating lamp reflection.
    mat=shade('Clotted blood • irregular wet top',[(.037,.0010,.003),(.11,.0036,.009),(.19,.009,.018)],
              2.25,.33,.16,sss=.19,coat=.15,ior=1.35)
    nt=mat.node_tree;phys=nt.nodes.get('Principled BSDF')
    phys.inputs['Coat Roughness'].default_value=.25
    grp=nt.nodes.new('ShaderNodeGroup');src=next(n for n in imported.node_tree.nodes if n.type=='GROUP')
    grp.node_tree=src.node_tree
    for inp in src.inputs:
        if hasattr(inp,'default_value') and inp.name in grp.inputs:
            grp.inputs[inp.name].default_value=inp.default_value
    mixed=nt.nodes.new('ShaderNodeMixShader');mixed.inputs[0].default_value=.29
    nt.links.new(phys.outputs[0],mixed.inputs[1])
    shader=next(o for o in grp.outputs if o.type=='SHADER')
    nt.links.new(shader,mixed.inputs[2])
    nt.links.new(mixed.outputs[0],nt.nodes.get('Material Output').inputs['Surface'])
    remat(clot,mat)
    for o in list(S.objects):
        if o.name.startswith('Fine strands at clot meniscus'):
            sp=o.data.splines[0]
            for p in sp.bezier_points:
                x,y,_=p.co*1000
                p.co.z=(height(x,y)+.018)/1000
            o.data.bevel_depth=.000018
    # The adhesive film darkens valleys while discrete granules interrupt the lamp highlight.
    for i in range(24):
        x=rng.uniform(-1.7,1.65);y=rng.uniform(-1.9,3.8);z=height(x,y)
        r=rng.uniform(.085,.215)
        b=organic('Small aggregates in clot', (x,y,z-.026), (r,r*.81,r*.41),mat,clot,i)
        visible(b,[(41.00+i*.032,44.05)])


def continuous_bone_fulcra():
    # Raise the existing buccal wall beneath the two purchase points. Because
    # the same vertices carry the socket material, the ledge has no separate edge.
    from mathutils.bvhtree import BVHTree
    obj=O['Alveolar bed, cortical rim and contiguous vestibule']
    bed=obj.data
    tree=BVHTree.FromPolygons([v.co.copy() for v in bed.vertices],
                              [tuple(p.vertices) for p in bed.polygons])
    supports=[]
    for ob in S.objects:
        if ob.name.startswith('Rough buccal bone at elevator fulcrum'):
            p=(ob.location-base.ZERO)*1000
            hit,_,_,_=tree.ray_cast(V((p.x/1000,p.y/1000,.065)),V((0,0,-1)))
            supports.append((p,max(0,p.z-.10-hit.z*1000)))
            disable(ob)
    pts=[]
    for vert in bed.vertices:
        p=vert.co*1000
        rise=max((h*exp(-((p.x-q.x)/1.85)**2-((p.y-q.y)/1.54)**2) for q,h in supports),default=0)
        pts.append(p+V((0,0,rise)))
    deform(obj,'Continuous buccal wall under elevator purchase',pts,
           [(0,0),(18.66,0),(18.84,1),(32.95,1),(33,0)])
    S.frame_set(1)
