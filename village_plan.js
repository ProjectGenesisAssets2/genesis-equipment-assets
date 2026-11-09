/* v0.11.005 · 63 m square, preserving the two existing tutorial door anchors. */
(() => {
  const workshopScale=.75;
  const bounds={minX:-24.5,maxX:38.5,minZ:-14.5,maxZ:48.5};
  const workshops=[
    {profession:'Herrero',label:'HERRERÍA',x:0,z:0,yaw:0,cx:0,cz:-3.9375,w:9,d:7.875,existing:true},
    {profession:'Curtidor',label:'CURTIDURÍA',x:14,z:0,yaw:0,cx:14,cz:-3.9375,w:9,d:7.875,existing:true},
    {profession:'Carpintero',label:'CARPINTERÍA',x:-11.5625,z:16,yaw:90,cx:-15.5,cz:16,w:7.875,d:9},
    {profession:'Arcanista',label:'ARCANISTA',x:25.5625,z:16,yaw:-90,cx:29.5,cz:16,w:7.875,d:9},
    {profession:'Joyero',label:'JOYERÍA',x:-11,z:32.0625,yaw:180,cx:-11,cz:36,w:9,d:7.875}
  ];
  const plaza={x:7,z:16,w:13,d:13};
  const market={x:26,z:36,w:12,d:10,reference:true};
  const roads=[
    {name:'Sendero principal',x:7,z:24.2,w:3.5,d:48.6},
    {name:'Acceso Herrero',x:0,z:2.1,w:2.6,d:4.6},
    {name:'Acceso Curtidor',x:14,z:2.1,w:2.6,d:4.6},
    {name:'Unión talleres norte',x:7,z:3.6,w:16.6,d:2.6},
    {name:'Acceso Carpintero',x:-5.2,z:16,w:13.7,d:2.6},
    {name:'Acceso Arcanista',x:19.2,z:16,w:13.7,d:2.6},
    {name:'Acceso Joyero',x:-2,z:28.5,w:21,d:2.6},
    {name:'Umbral Joyero',x:-11,z:30,w:2.6,d:5.5},
    {name:'Acceso Mercado',x:17,z:36,w:21,d:2.6}
  ];
  function blocked(x,z,r=.33){return workshops.some(p=>!p.existing&&Math.abs(x-p.cx)<p.w/2+r&&Math.abs(z-p.cz)<p.d/2+r)}
  function toWorld(point,center=0){return{x:center+(point.x-center)*workshopScale,y:point.y||0,z:point.z*workshopScale}}
  function toLocal(x,z,center=0){return{x:(x-center)/workshopScale,z:z/workshopScale}}
  function movementSpeed(keys){return keys.has('ShiftLeft')||keys.has('ShiftRight')?5:2.75}
  const plan=Object.freeze({bounds,workshops,plaza,market,roads,blocked,workshopScale,toWorld,toLocal,movementSpeed});
  globalThis.GenesisVillagePlan=plan;
  if(typeof module!=='undefined')module.exports=plan;
})();
