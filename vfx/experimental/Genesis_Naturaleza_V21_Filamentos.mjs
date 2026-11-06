// Project Genesis - Naturaleza V21, experimental surface-bound effect.
// Independent shader; NO approved fire or rayo source file modifications.
// Visual design: brotes de energía verde con ramificaciones orgánicas y hojas pequeñas.
import {createV21SurfaceChannel,v21NoiseGLSL} from './Genesis_AffinitySurfaceCore_V21.mjs';
const fragmentGLSL=`
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform float uIntensity;
${v21NoiseGLSL}
void main(void){
 float power=clamp(uIntensity*.01,0.,1.);
 if(power<=.0001)discard;
 float seed=floor(vUv.x),v=fract(vUv.x),x=vUv.y*2.-1.,t=uTime;
 float leaf=1.-smoothstep(.10,.90,abs(x));
 float central=exp(-abs(x)*19.);
 float vein1=exp(-abs(x-sin(v*7.5+seed*.81)*.43)*17.);
 float vein2=exp(-abs(x+sin(v*7.5+seed*.33)*.41)*19.);
 float structure=central*.34+leaf*.33+(vein1+vein2)*.18;
 float age=smoothstep(-.4,.6,sin(v*9.-t*1.7+seed*.83));
 float pulse=.72+.28*sin(t*2.4+seed*.4+v*11.);
 float alpha=clamp(power*(.23+.48*power)*structure*(.48+.52*age),0.,.71);
 if(alpha<.008)discard;
 vec3 moss=vec3(.09,.35,.065),sap=vec3(.45,1.07,.22),light=vec3(.69,1.55,.49);
 vec3 rgb=mix(moss,sap,age*.74+central*.26);
 rgb=mix(rgb,light,central*.35);
 gl_FragColor=vec4(rgb*(.52+.65*power)*pulse,alpha);
}
`;
export const NATURALEZA_V21_SPEC=Object.freeze({
  id:'Genesis_Naturaleza_V21_Filamentos',affinity:'naturaleza',approved:false,
  scope:'only original V03 sword test',intensity:[0,100],
  source:'V21 affinity zone contract, concept implementation not user approved',
  manifest:'vfx/experimental/Genesis_AffinitySlots_V01.mjs',
  semanticSlot:'blade_minor_filaments',
  visual:'brotes de energía verde con ramificaciones orgánicas y hojas pequeñas',
  preservesGLB:true,preservesPBRV175:true,
  independent:true,composabilityTested:false,otherObjectFamiliesImplemented:false
});
const patches=[
 {
  "y": 0.319812,
  "height": 0.044867,
  "x": -0.02,
  "halfWidth": 0.014926,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.086
 },
 {
  "y": 0.327063,
  "height": 0.045022,
  "x": 0,
  "halfWidth": 0.012333,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08793265306171306
 },
 {
  "y": 0.334313,
  "height": 0.042513,
  "x": 0.02,
  "halfWidth": 0.014518,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08895634918996537
 },
 {
  "y": 0.341562,
  "height": 0.047209,
  "x": -0.009,
  "halfWidth": 0.015768,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08858962809994661
 },
 {
  "y": 0.348813,
  "height": 0.040638,
  "x": 0.011,
  "halfWidth": 0.012814,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08700496445046771
 },
 {
  "y": 0.356063,
  "height": 0.048648,
  "x": -0.02,
  "halfWidth": 0.01338,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08494765031693113
 },
 {
  "y": 0.363313,
  "height": 0.039731,
  "x": 0,
  "halfWidth": 0.015985,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08338527268275923
 },
 {
  "y": 0.370563,
  "height": 0.048963,
  "x": 0.02,
  "halfWidth": 0.013818,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08305264216212699
 },
 {
  "y": 0.377812,
  "height": 0.040029,
  "x": -0.009,
  "halfWidth": 0.012544,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08410620008638303
 },
 {
  "y": 0.385063,
  "height": 0.048072,
  "x": 0.011,
  "halfWidth": 0.015495,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08605044170145304
 },
 {
  "y": 0.392313,
  "height": 0.041455,
  "x": -0.02,
  "halfWidth": 0.014955,
  "curve": 0.003,
  "shape": "leaf",
  "z": 0.08797095979615636
 }
];
export function createNaturalezaV21(pc,app,bladeAabb){
 return createV21SurfaceChannel(pc,app,bladeAabb,{
  id:'naturaleza',fragmentGLSL,patches,lightColor:[0.22,0.83,0.3],
  lightIntensity:0.17,
 });
}
