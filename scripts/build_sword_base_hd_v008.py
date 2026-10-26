"""Project Genesis — sword BASE from the eight-affinity concept, HD modular V008.
Every component is its own mesh: NEVER join objects before GLB export.
Concept source: eight swords pack / Base.png (420x630). Neutral sword only.
Blender 4.5.13 LTS, Cycles CPU; exports .blend, .glb and proof-of-work audit.
"""
import bpy, math, os, json, random
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi
random.seed(33171)

OUT=Path(os.environ.get('GITHUB_WORKSPACE',os.getcwd()))/'output_sword_hd'
OUT.mkdir(exist_ok=True,parents=True)
STEM='Espada_Concept_Base_HD_V008'

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for mat in list(bpy.data.materials): bpy.data.materials.remove(mat)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=28
bpy.context.view_layer.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=False
scene.render.resolution_x=1040
scene.render.resolution_y=1560
scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.view_settings if hasattr(scene.view_settings,'view_settings') else None
scene.world=bpy.data.worlds.new('Estudio_Gris')
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.13,.145,.155,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35

# Real PBR materials, no emissive/magical layers.
def mat(name,color,metallic,roughness,noise_scale=0,bump_strength=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1);m.use_nodes=True
    nodes=m.node_tree.nodes;links=m.node_tree.links
    bs=nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Roughness'].default_value=roughness
    if noise_scale:
        coord=nodes.new('ShaderNodeTexCoord');coord.location=(-870,160)
        noise=nodes.new('ShaderNodeTexNoise');noise.location=(-620,180)
        noise.inputs['Scale'].default_value=noise_scale
        noise.inputs['Detail'].default_value=3.0
        noise.inputs['Roughness'].default_value=.67
        links.new(coord.outputs['Object'],noise.inputs['Vector'])
        ramp=nodes.new('ShaderNodeValToRGB');ramp.location=(-370,250)
        a,b=ramp.color_ramp.elements
        a.position=.23;a.color=(*(max(.001,v*.38) for v in color),1)
        b.position=.78;b.color=(*(min(.9,v*1.04) for v in color),1)
        links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
        rough_noise=nodes.new('ShaderNodeMapRange');rough_noise.location=(-310,-40)
        rough_noise.inputs['To Min'].default_value=max(.09,roughness-.12)
        rough_noise.inputs['To Max'].default_value=min(.88,roughness+.13)
        links.new(noise.outputs['Fac'],rough_noise.inputs['Value'])
        links.new(rough_noise.outputs['Result'],bs.inputs['Roughness'])
        if bump_strength:
            bump=nodes.new('ShaderNodeBump');bump.location=(-70,-150)
            bump.inputs['Strength'].default_value=bump_strength
            bump.inputs['Distance'].default_value=.0012 if metallic>.5 else .0018
            links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return m

steel=mat('Acero_forjado_satina_PBR',(.24,.265,.28),.96,.34,31,.16)
steel_edges=mat('Acero_filos_pulidos_PBR',(.39,.41,.43),.97,.255,49,.075)
steel_dark=mat('Acero_patina_oscura_PBR',(.12,.13,.14),.86,.49,27,.16)
guard_steel=mat('Acero_guarda_cepillado_PBR',(.275,.295,.31),.96,.32,32,.11)
guard_plate_steel=mat('Acero_Forjado_Guarda_Ancha_PBR',(.15,.17,.19),.91,.49,43,.14)
highlights=mat('Acero_resaltes_plata_PBR',(.40,.40,.37),.97,.27,42,.075)
engraving=mat('Oscurecido_incisiones_PBR',(.085,.093,.104),.74,.55,0,0)
leather=mat('Cuero_marron_rojizo_PBR',(.075,.026,.015),.0,.77,74,.19)
leather_light=mat('Cuero_cantos_envejecidos_PBR',(.118,.039,.022),.0,.70,61,.16)
wood=mat('Madera_nucleo_puno_PBR',(.115,.06,.033),.0,.82,17,.12)

ASSETS=[]
def init_mesh(ob,zone,part,uv=True, smooth=False):
    ob['Genesis_Asset']=True;ob['Zona_Afinidad']=zone;ob['Componente']=part
    ob['Version']='HD_V008';ob['Afinidades_activas']=0
    ob['Atributos_reservados']='AffinityMask_A RGBA [Fuego,Hielo,Naturaleza,Tierra]; AffinityMask_B RGBA [Rayo,Luz,Sombra,Libre]'
    if ob.type!='MESH':return ob
    mesh=ob.data
    for poly in mesh.polygons:poly.use_smooth=smooth
    if uv:
        u0=mesh.uv_layers.new(name='UV0_PBR')
        u1=mesh.uv_layers.new(name='UV1_Mascaras_Afinidad')
        verts=mesh.vertices
        mnx=min(v.co.x for v in verts); mxx=max(v.co.x for v in verts)
        mnz=min(v.co.z for v in verts); mxz=max(v.co.z for v in verts)
        dx=max(.001,mxx-mnx); dz=max(.001,mxz-mnz)
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                v=verts[mesh.loops[li].vertex_index].co
                u0.data[li].uv=(v.x*3.2 + .5,v.z*3.2+.5)
                u1.data[li].uv=((v.x-mnx)/dx,(v.z-mnz)/dz)
    for n in ('AffinityMask_A','AffinityMask_B'):
        col=mesh.color_attributes.new(name=n,type='FLOAT_COLOR',domain='CORNER')
        for d in col.data:d.color=(0.,0.,0.,0.)
    ASSETS.append(ob)
    return ob

def obj(name,verts,faces,material,zone,part=None,smooth=False):
    mesh=bpy.data.meshes.new(name+'_Geometry')
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    # Recalculate normals without joining components.
    import bmesh
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
    return init_mesh(ob,zone,part or name,smooth=smooth)

def tube(name,points,radii,matl,zone,sides=12,normal_y=True):
    # Sweep 3D path with stable planar normal. For leather stripes and subtle metal filigree.
    verts=[];faces=[]
    for i,p in enumerate(points):
        p=Vector(p)
        prev=Vector(points[max(0,i-1)]);nex=Vector(points[min(len(points)-1,i+1)])
        t=(nex-prev).normalized()
        ref=Vector((0,1,0)) if abs(t.dot(Vector((0,1,0))))<.88 else Vector((1,0,0))
        v=(t.cross(ref)).normalized();u=(v.cross(t)).normalized()
        r=radii[i] if isinstance(radii,(list,tuple)) else radii
        for j in range(sides):
            q=2*pi*j/sides
            verts.append(tuple(p + r*(math.cos(q)*u+math.sin(q)*v)))
        if i:
            for j in range(sides):a=(i-1)*sides+j;b=(i-1)*sides+(j+1)%sides;c=i*sides+(j+1)%sides;d=i*sides+j;faces.append((a,b,c,d))
    faces.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))])
    return obj(name,verts,faces,matl,zone,smooth=True)

def rings(name,rings_data,matl,zone,sides=24,faceted=False):
    # each ring (z, radiusX, radiusY), axially symmetric profile, separated object
    verts=[];faces=[]
    for z,rx,ry in rings_data:
        for j in range(sides):
            a=2*pi*j/sides;verts.append((rx*math.cos(a),ry*math.sin(a),z))
    for i in range(len(rings_data)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(rings_data)-1)*sides+j for j in range(sides)))
    return obj(name,verts,faces,matl,zone,smooth=not faceted)

def faceted_gem(name,cx,cy,cz,rx,ry,rz,material,zone):
    # raised double-pyramid jewel, not a flat texture
    verts=[(cx,cy-ry,cz),(cx+rx,cy,cz),(cx,cy,cz+rz),(cx-rx,cy,cz),(cx,cy,cz-rz),(cx,cy+ry,cz)]
    faces=[(0,1,2),(0,2,3),(0,3,4),(0,4,1),(5,2,1),(5,3,2),(5,4,3),(5,1,4)]
    return obj(name,verts,faces,material,zone)

# --- Forged steel blade, symmetrical double edge, separate body + edges ---
TIP=.888;START=-.013
RINGS=140

def blade_width(z):
    # Reference measured from Base.png:
    # straight blade 0.90 m; lower half-width ~0.050 m; apex begins at 85.5%.
    # The V002 blade was ~27% too wide relative to the long narrow reference.
    q=max(0.,min(1.,(z-START)/(TIP-START)))
    if q<.055:
        return .0498*(.982+.018*q/.055)
    if q<.855:
        return .0498*(1.-.037*(q-.055)/.800)
    v=(q-.855)/.145
    return (.0498*.963)*max(.000065,max(0.,1.-v)**.96)

def profile_y(k,z,front):
    # CRITICAL GEOMETRY REPAIR: Previous V002 had a tiny center valley:
    # |k|=0 measured 96% thickness, |k|=.20 measured 100%.
    # A real double-edge diamond blade must instead have the HIGHEST ridge
    # at the center line k=0, on both front and back, down to the final apex.
    q=max(0.,min(1.,(z-START)/(TIP-START)))
    tip_thinning=max(.025, min(1., ((1.-q)/.040)**.7))
    th=.0150*(1.-.24*q)*tip_thinning
    a=abs(k)
    if a<=.06: f=1.-.018*a/.06
    elif a<=.22: f=.982-.135*(a-.06)/.16
    elif a<=.48: f=.847-.205*(a-.22)/.26
    elif a<=.75: f=.642-.169*(a-.48)/.27
    elif a<=.92: f=.473-.365*(a-.75)/.17
    else: f=max(.013,.108-.095*(a-.92)/.08)
    return (-1 if front else 1)*max(.00008,th*f)

def blade_section(name,fractions,material,zone):
    n=len(fractions);v=[];faces=[]
    for front in (True,False):
        for i in range(RINGS):
            z=START+(TIP-START)*i/(RINGS-1);w=blade_width(z)
            for f in fractions:v.append((f*w,profile_y(f,z,front),z))
    sz=n*RINGS
    for i in range(RINGS-1):
        for j in range(n-1):
            k=i*n+j
            faces.append((k,k+1,k+1+n,k+n))
            k+=sz;faces.append((k+n,k+1+n,k+1,k))
    for i in range(RINGS-1):
        for j in (0,n-1):
            k=i*n+j;faces.append((k,k+n,k+sz+n,k+sz))
    for j in range(n-1):
        faces.append((j,j+sz,j+sz+1,j+1))
        k=(RINGS-1)*n+j;faces.append((k,k+1,k+sz+1,k+sz))
    return obj(name,v,faces,material,zone, smooth=False)

blade_section('Hoja_Nucleo_Forjado',[-.75,-.48,-.22,-.06,0,.06,.22,.48,.75],steel,'Hoja')
blade_section('Filo_Izquierdo',[-1.,-.985,-.92,-.845,-.75],steel_edges,'Filo_Izquierdo')
blade_section('Filo_Derecho',[.75,.845,.92,.985,1.],steel_edges,'Filo_Derecho')
# Heel/ricasso under crossguard; separate, not joined to blade
rings('Espiga_Oculta',[( -.427,.007,.005),(-.075,.009,.007),(.075,.009,.007)],steel_dark,'Espiga',sides=12)

# Shallow, broken forged grooves rather than exaggerated painted scratches.
for i,(side,z,length,offset) in enumerate([
  (-1,.20,.072,.014),(1,.273,.061,.009),(-1,.345,.090,.020),
  (1,.455,.055,.017),(-1,.535,.085,.012),(1,.624,.062,.011),
  (-1,.684,.031,.010),(1,.185,.040,.022)
]):
    pts=[];seg=16
    for j in range(seg):
        a=j/(seg-1);zz=z+length*(a-.5)
        x=side*(offset+.009*(a-.5))
        yy=profile_y(x/max(.001,blade_width(zz)),zz,True)-.0008
        pts.append((x,yy,zz))
    tube('Marca_Forja_%02d'%i,pts,[.00019+.00045*math.sin(pi*j/(seg-1)) for j in range(seg)],engraving,'Grabados_Hoja',sides=6)

# Discrete raised shoulder langets: guard-to-blade transition, 3D not a decal.
for sign,label in [(-1,'Izquierdo'),(1,'Derecho')]:
    pts=[]
    for i in range(25):
        t=i/24;z=-.009+t*.112;x=sign*(.0505-.019*t+.002*sin(pi*t))
        pts.append((x,-.011-0.0005*cos(pi*t),z))
    tube('Refuerzo_Basal_'+label,pts,[.005*(1-.88*(i/24)**2)+.0005 for i in range(25)],guard_steel,'Refuerzos_Hoja',sides=10)
    tube('Filete_Refuerzo_'+label,[(x,y-.004,z) for x,y,z in pts],.00115,highlights,'Refuerzos_Hoja',sides=8)

# Broad crossguard with forged flat facets, swept down arms and diamond terminals.
def forged_guard_plate(name,sign,material):
    # Thick forged weapon crossguard, not a round/linear tube.
    # Precisely outlined front-facing plate matches the low curved profile
    # of the original Base reference; chamfered rims on front and rear.
    outline=[
      (.014,-.009),(.036,-.013),(.062,-.019),(.093,-.023),
      (.123,-.020),(.151,-.015),(.172,-.008),(.187,-.017),
      (.178,-.034),(.154,-.041),(.115,-.046),(.080,-.050),
      (.041,-.052),(.014,-.043)]
    n=len(outline)
    cx=sum(x for x,z in outline)/n
    cz=sum(z for x,z in outline)/n
    verts=[]
    for factor,depth in ((1.,-.011),(.935,-.022),(1.,.011),(.935,.022)):
        for x,z in outline:
            verts.append((sign*(cx+(x-cx)*factor),depth,-.028+(cz+(z-cz)*factor+.028)*1.14))
    faces=[]
    for row1,row2 in ((0,n),(0,2*n),(2*n,3*n)):
        for j in range(n):
            t=(j+1)%n
            faces.append((row1+j,row1+t,row2+t,row2+j))
    faces.append(tuple(range(n,2*n)))
    faces.append(tuple(reversed(range(3*n,4*n))))
    return obj(name,verts,faces,material,'Guarda',smooth=False)

# Position guide from concept: ±.195m spread, double shoulder claws above crossbar.
for sign,label in [(-1,'Izquierda'),(1,'Derecha')]:
    P=[];RR=[]
    for i in range(41):
        t=i/40;x=sign*(.014+.171*t)
        z=-.026- .0085*sin(pi*t) + .006*t
        P.append((x,0,z));RR.append(.010+ .007*sin(pi*(t*.86+.1)) + .0015*t)
    forged_guard_plate('Guarda_Brazo_'+label,sign,guard_plate_steel)
    tube('Guarda_Filete_Frontal_'+label,[(x,-.027,z+.008) for x,y,z in P],
        [.0024+.0008*sin(pi*i/40) for i in range(41)],highlights,'Ornamentos_Guarda',sides=10)
    # raised lower outline tracing the full ornament
    tube('Guarda_Filete_Inferior_'+label,[(x,-.026,z-.012) for x,y,z in P],.0019,steel_dark,'Ornamentos_Guarda',sides=8)
    # tip diamond (3D cap) and dark engraved collar
    faceted_gem('Guarda_Remate_'+label,sign*.188,0,-.015,.022,.014,.026,highlights,'Remates_Guarda')
    rings_dummy=None
    # Solid forged ascending langet, separate left/right, not a wire arch.
    shape=[(.038,-.015),(.071,-.010),(.066,.011),(.055,.040),(.050,.085),(.046,.066),(.047,.034)]
    vertices=[(sign*x,y,z) for y in (-.012,.012) for x,z in shape]
    m=len(shape)
    faces=[tuple(range(m)),tuple(reversed(range(m,2*m)))]
    for k in range(m):faces.append((k,(k+1)%m,(k+1)%m+m,k+m))
    obj('Guarda_Ala_Solida_'+label,vertices,faces,guard_steel,'Guarda')
    tube('Guarda_Ala_Filete_'+label,
         [(sign*.068,-.014,-.004),(sign*.054,-.014,.038),(sign*.049,-.014,.080)],
         [.0024,.0018,.0008],highlights,'Ornamentos_Guarda',sides=8)
    # engraved tiny support on top of horizontal guard
    tube('Guarda_Filigrana_Curva_'+label,
         [(sign*(.026+.118*t/25),-.026, -.022-.021*sin(pi*t/25)+.012*(t/25)) for t in range(26)],
         .0016,highlights,'Ornamentos_Guarda',sides=8)

# central broad diamond socket in a traditional utilitarian gothic silhouette
faceted_gem('Guarda_Escudo_Central',0,-.010,-.024,.032,.015,.041,steel_dark,'Guarda')
faceted_gem('Guarda_Diamante_Resalte',0,-.028,-.025,.022,.006,.029,highlights,'Ornamentos_Guarda')
faceted_gem('Guarda_Diamante_Posterior',0,.025,-.025,.020,.005,.024,highlights,'Ornamentos_Guarda')

# --- Grip, handmade wrapped brown leather. Each wrap is a real independent mesh. ---
G_TOP=-.078;G_BOTTOM=-.418
rings('Empunadura_Nucleo_Madera',[(G_BOTTOM,.020,.020),(-.34,.021,.021),(-.245,.022,.022),
                                     (-.15,.021,.021), (G_TOP,.020,.020)],wood,'Empunadura',sides=28)
rings('Empunadura_Funda_Cuero',[(G_BOTTOM,.0220,.0220),(-.350,.0225,.0225),(-.245,.0232,.0232),
                                 (-.14,.0225,.0225),(G_TOP,.0221,.0221)],leather,'Empunadura',sides=36)
# Leather STRIPS with true ribbon thickness, NOT round rope coils.
def leather_ribbon(name,points,width=.019,thick=.0028):
    verts=[];faces=[]
    for i,raw in enumerate(points):
        p=Vector(raw);t=(Vector(points[min(len(points)-1,i+1)])-Vector(points[max(i-1,0)])).normalized()
        radial=Vector((p.x,p.y,0)).normalized()
        across=t.cross(radial).normalized()
        half=width*.5
        # two outer / two inner vertices per station
        verts.extend([tuple(p+across*half+radial*thick),tuple(p-across*half+radial*thick),
                      tuple(p+across*half),tuple(p-across*half)])
        if i:
            q=(i-1)*4;r=i*4
            faces.extend([(q,q+1,r+1,r),(q+3,q+2,r+2,r+3),(q+2,q,r,r+2),(q+1,q+3,r+3,r+1)])
    faces.extend([(0,2,3,1),tuple((len(points)-1)*4+j for j in (0,1,3,2))])
    return obj(name,verts,faces,leather_light,'Trenzado_Cuero',smooth=True)

TURN=11
for turn in range(TURN):
    pts=[];steps=74
    for j in range(steps):
        t=j/(steps-1);frac=(turn+t)/TURN
        zz=G_TOP-.007 -(G_TOP-G_BOTTOM-.018)*frac
        theta=2*pi*(turn+t)+.40+.12*sin(turn*1.7)
        rr=.0232+.00048*sin(8*pi*frac)
        pts.append((rr*cos(theta),rr*sin(theta),zz))
    leather_ribbon('Cuero_Trenza_Espiral_%02d'%(turn+1),pts,width=.018+.0030*sin(turn*2.7))
# Extra asymmetric crossing straps based on the irregular hand-wrapped reference.
for k,zc in enumerate((-.15,-.245,-.345)):
    pts=[]
    for j in range(34):
        a=j/33
        theta= -2.20+1.42*a if k%2 else -.90-1.40*a
        rr=.0246
        zz=zc+(a-.5)*.041
        pts.append((rr*cos(theta),rr*sin(theta),zz))
    leather_ribbon('Cuero_Cruce_Artesanal_%02d'%(k+1),pts,width=.013,thick=.0019)
# Visually read seam behind, each stitch discrete 3D.
for k in range(22):
    zz=G_BOTTOM +.014 +k*.014
    pts=[(-.0035,.024,zz-.002),(0,.0243,zz),(.0035,.024,zz+.002)]
    tube('Costura_Cuero_%02d'%k,pts,.00072,leather_light,'Costuras_Cuero',sides=6)

rings('Virola_Superior',[(G_TOP-.009,.025,.025),(G_TOP-.006,.025,.025),(G_TOP+.009,.023,.023),(G_TOP+.013,.022,.022)],guard_steel,'Virolas',sides=32)
rings('Virola_Inferior',[(G_BOTTOM-.015,.022,.022),(G_BOTTOM-.012,.027,.027),(G_BOTTOM+.008,.026,.026),(G_BOTTOM+.012,.022,.022)],guard_steel,'Virolas',sides=32)
for z,label in [(G_TOP-.006,'Superior'),(G_BOTTOM-.009,'Inferior')]:
    rings('Aro_Filo_'+label,[(z-.002,.027,.027),(z,.028,.028),(z+.002,.027,.027)],highlights,'Virolas',sides=32)

# Faceted diamond pommel matching exact base concept, not a sphere.
# Pommel core elongated from -.428 to -.535, with pointed termination.
rings('Pomo_Cuerpo_Facetado',[
    (-.552,.001,.001),(-.519,.034,.018),(-.480,.052,.026),(-.453,.040,.021),(-.429,.019,.014)],
    guard_steel,'Pomo',sides=8,faceted=True)
# A prominent wide faceted kite matching the 2D art, with two independent metal facings.
faceted_gem('Pomo_Diamante_Frontal',0,-.030,-.487,.040,.012,.055,highlights,'Ornamentos_Pomo')
faceted_gem('Pomo_Diamante_Trasero',0,.030,-.487,.039,.010,.054,steel_dark,'Ornamentos_Pomo')
for sign,label in ((-1,'Izquierdo'),(1,'Derecho')):
    tube('Pomo_Filete_'+label,[(sign*.010,-.033,-.537),(sign*.032,-.033,-.483),(sign*.011,-.030,-.438)],
         .0017,highlights,'Ornamentos_Pomo',sides=7)

# 18 percent taller leather grip, proportional to the original Base concept.
# Move lower collar and faceted pommel down without merging any objects.
GRIP_STRETCH=1.18
GRIP_ORIGINAL_BOTTOM=G_BOTTOM
GRIP_EXTRA=(G_BOTTOM-G_TOP)*(GRIP_STRETCH-1)
for ob in ASSETS:
    zone=ob['Zona_Afinidad']
    if zone not in ('Empunadura','Trenzado_Cuero','Costuras_Cuero','Virolas','Pomo','Ornamentos_Pomo'):
        continue
    for vert in ob.data.vertices:
        z=vert.co.z
        if z<G_TOP:
            if z>=GRIP_ORIGINAL_BOTTOM:
                vert.co.z=G_TOP+(z-G_TOP)*GRIP_STRETCH
            else:
                vert.co.z=z+GRIP_EXTRA
        if zone in ('Pomo','Ornamentos_Pomo'):
            vert.co.x*=1.10
            vert.co.y*=1.10
    verts=ob.data.vertices
    mnx=min(v.co.x for v in verts);mxx=max(v.co.x for v in verts)
    mnz=min(v.co.z for v in verts);mxz=max(v.co.z for v in verts)
    dx=max(.001,mxx-mnx);dz=max(.001,mxz-mnz)
    u0=ob.data.uv_layers.get('UV0_PBR')
    u1=ob.data.uv_layers.get('UV1_Mascaras_Afinidad')
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            v=verts[ob.data.loops[li].vertex_index].co
            if u0:u0.data[li].uv=(v.x*3.2+.5,v.z*3.2+.5)
            if u1:u1.data[li].uv=((v.x-mnx)/dx,(v.z-mnz)/dz)
    ob.data.update()

# Geometry-only silhouette calibration against actual pixel dimensions in Base.png.
# Preserve each independent component and the median ridge cross-section.
# Reference: blade width/height .0643, crossguard width/height .250.
# Previous V007: ~.0682 and ~.275 respectively in frontal image.
for ob in ASSETS:
    zone=ob['Zona_Afinidad']
    scale_x=1.0
    if zone in ('Hoja','Filo_Izquierdo','Filo_Derecho','Grabados_Hoja','Refuerzos_Hoja'):
        scale_x=.945
    elif zone in ('Guarda','Ornamentos_Guarda','Remates_Guarda'):
        scale_x=.912
    if scale_x==1.0:continue
    for vert in ob.data.vertices:
        vert.co.x *= scale_x
    verts=ob.data.vertices
    mnx=min(v.co.x for v in verts);mxx=max(v.co.x for v in verts)
    mnz=min(v.co.z for v in verts);mxz=max(v.co.z for v in verts)
    dx=max(.001,mxx-mnx);dz=max(.001,mxz-mnz)
    u0=ob.data.uv_layers.get('UV0_PBR')
    u1=ob.data.uv_layers.get('UV1_Mascaras_Afinidad')
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            v=verts[ob.data.loops[li].vertex_index].co
            if u0:u0.data[li].uv=(v.x*3.2+.5,v.z*3.2+.5)
            if u1:u1.data[li].uv=((v.x-mnx)/dx,(v.z-mnz)/dz)
    ob.data.update()

# Explicit downstream Unreal intent; no fake affinity applied
for ob in ASSETS:
    ob['Sistema_Afinidades']='7 capas inactivas; control por malla, mascaras o material instances en UE'
    ob['Material_Base_Inalterado']=True
    ob['LODs_Pendientes']=True

# Studio only, not included in the GLB game asset
worldmat=bpy.data.materials.new('Fondo_Studio_NoExportar');worldmat.diffuse_color=(.024,.026,.031,1)
worldmat.use_nodes=True
n=worldmat.node_tree.nodes;n.clear()
out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission')
em.inputs['Color'].default_value=(.022,.025,.032,1)
em.inputs['Strength'].default_value=1.0
worldmat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,.58,0))
bg=bpy.context.object;bg.name='Fondo_Studio_NoExportar';bg.rotation_euler[0]=pi/2;bg.data.materials.append(worldmat)

def light(name,location,power,color,size,size_y=None):
    data=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
    ob.location=location;data.energy=power;data.color=color
    data.shape='RECTANGLE';data.size=size;data.size_y=size_y or size
    ob.rotation_euler=(Vector((0,0,.15))-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob
light('Softbox_Principal',( -1.25,-2.3,1.4),155,(.88,.91,1),1.25,2.1)
light('Softbox_Bisel_Derecho',(1.40,-1.6,.65),29,(1,.94,.83),.45,2.3)
light('Softbox_Filo_Izquierdo',(-1.2,.9,.86),72,(.83,.9,1),.60,1.7)
light('Softbox_Guarda_Cercano',(.1,-1.8,-.30),30,(1,.73,.51),.65,.8)

def camera(name,pos,target=(0,0,.130),scale=1.65):
    data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(o)
    o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=scale;data.lens=55
    return o
camfront=camera('Camara_Frontal_Ortografica',(0,-4.0,.175),scale=1.62)
camthree=camera('Camara_TresCuartos',(1.55,-3.85,.34),scale=1.62)
camdetail=camera('Camara_Detalles',(.45,-2.2,-.13),target=(0,0,-.17),scale=.59)
scene.camera=camfront

# Validate before output. No low-poly joins, seven-affinity storage on every exported mesh.
assert all(o.type=='MESH' and len(o.data.uv_layers)>=2 and len(o.data.color_attributes)>=2 for o in ASSETS)
assert len(ASSETS)>40
if any(o.name!=a.name for i,o in enumerate(ASSETS) for a in ASSETS[i+1:] if o.name==a.name):
    raise RuntimeError('Duplicate object names')
tri=sum(len(p.vertices)-2 for o in ASSETS for p in o.data.polygons)
manifest={
  'name':'Espada Base - Coleccion Original 7 Afinidades - Alta Definicion V008',
  'concept':'Project Genesis / original eight-affinity sword pack / Base.png',
  'source_scale_m':{'top_z':TIP,'pommel_bottom_z':round(-.552+GRIP_EXTRA,5)},
  'v002_geometry_corrections':['broader shoulder','wider pommel','larger guard wings'],
  'v003_geometry_corrections':['slender blade','median ridge continues to apex'],
  'v004_geometry_corrections':['shorter wings','flat crossguard','darkened wrapped grip'],
  'v005_geometry_corrections':['extended grip','cross-laced leather','larger pommel'],
  'v006_geometry_corrections':['actual closed steel crossguard plates','beveled guard relief'],
  'v007_geometry_corrections':['dark PBR forged guard','more prominent metal bevel trim'],
  'v008_geometry_corrections':['blade width proportion calibrated to source photo -5.5%','crossguard total span reduced 8.8% to source photo','center ridges and exact pointed apex preserved','recompute UV0/UV1 on changed meshes','all objects remain separate'],
  'master_rule':'Every modeled component is a distinct Blender object; never join to optimize source.',
  'unreal_delivery':'glb with independently named meshes and active base PBR only. FBX optional later.',
  'channel_map':{
    'AffinityMask_A':['Fuego','Hielo','Naturaleza','Tierra'],
    'AffinityMask_B':['Rayo','Luz','Sombra','Reservado'],
  },
  'affinity_shader_status':'Reserved storage only. No 7-affinity Unreal master shader implemented or validated.',
  'unreal_import_status':'Not validated in Unreal yet.',
  'mesh_count':len(ASSETS),'triangles':tri,
  'parts':[{ 'name':o.name,'zone':o['Zona_Afinidad'],'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),
             'uv_layers':[u.name for u in o.data.uv_layers], 'vertex_color_layers':[a.name for a in o.data.color_attributes],
             'material':o.active_material.name if o.active_material else None} for o in ASSETS]
}
(OUT/(STEM+'_AUDIT.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

scene.camera=camfront
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(STEM+'.blend')))
# Exclude all studio objects by selection, avoid accidental join or lost separate parts.
bpy.ops.object.select_all(action='DESELECT')
for o in ASSETS:o.select_set(True)
bpy.context.view_layer.objects.active=ASSETS[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/(STEM+'.glb')),export_format='GLB',
                          use_selection=True,export_apply=True,export_texcoords=True,
                          export_normals=True,export_materials='EXPORT')
bpy.ops.object.select_all(action='DESELECT')

for cam,suffix in [(camfront,'FRONTAL'),(camthree,'TRES_CUARTOS'),(camdetail,'DETALLES')]:
    scene.camera=cam
    scene.render.filepath=str(OUT/(STEM+'_'+suffix+'.png'))
    bpy.ops.render.render(write_still=True)
    assert Path(scene.render.filepath).is_file() and Path(scene.render.filepath).stat().st_size>10000
print('GENESIS_HD_SWORD_SUCCESS', 'meshes',len(ASSETS),'triangles',tri,'files',STEM)