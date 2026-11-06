// Project Genesis - Luz V21, experimental surface-bound effect.
// Independent shader; NO approved fire or rayo source file modifications.
// Visual design: destellos puntuales blanco-dorados cerca de la guarda.
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
 float dx=x,dy=(v-.5)*2.;
 float radius=length(vec2(dx,dy));
 float rayH=exp(-abs(dy)*22.)*(1.-smoothstep(.21,.94,abs(dx)));
 float rayV=exp(-abs(dx)*23.)*(1.-smoothstep(.18,.93,abs(dy)));
 float core=1.-smoothstep(.025,.27,radius);
 float halo=1.-smoothstep(.09,.85,radius);
 float pulse=.57+.43*pow(.5+.5*sin(t*3.8+seed*2.5),2.);
 float spark=clamp(core+rayH*.38+rayV*.47+halo*.23,0.,1.);
 float alpha=clamp(power*(.22+.49*power)*spark*pulse,0.,.80);
 if(alpha<.008)discard;
 vec3 gold=vec3(1.34,.83,.29),white=vec3(1.65,1.62,1.11);
 gl_FragColor=vec4(mix(gold,white,core*.82+rayH*.18)*(1.1+.45*power),alpha);
}
`;
export const LUZ_V21_SPEC=Object.freeze({
  id:'Genesis_Luz_V21_Destellos',affinity:'luz',approved:false,
  scope:'only original V03 sword test',intensity:[0,100],
  source:'V21 affinity zone contract, concept implementation not user approved',
  manifest:'vfx/experimental/Genesis_AffinitySlots_V01.mjs',
  semanticSlot:'pommel_highlights',
  visual:'destellos puntuales blanco-dorados cerca de la guarda',
  preservesGLB:true,preservesPBRV175:true,
  independent:true,composabilityTested:false,otherObjectFamiliesImplemented:false
});
const patches=[
 {
  "y": 0.019156,
  "height": 0.024723,
  "x": -0.02,
  "halfWidth": 0.017724,
  "curve": 0.001,
  "shape": "glint",
  "z": 0.086
 },
 {
  "y": 0.023781,
  "height": 0.024808,
  "x": 0,
  "halfWidth": 0.014645,
  "curve": 0.001,
  "shape": "glint",
  "z": 0.08793265306171306
 },
 {
  "y": 0.028406,
  "height": 0.023426,
  "x": 0.02,
  "halfWidth": 0.01724,
  "curve": 0.001,
  "shape": "glint",
  "z": 0.08895634918996537
 },
 {
  "y": 0.033031,
  "height": 0.026013,
  "x": -0.009,
  "halfWidth": 0.018724,
  "curve": 0.001,
  "shape": "glint",
  "z": 0.08858962809994661
 },
 {
  "y": 0.037656,
  "height": 0.022392,
  "x": 0.011,
  "halfWidth": 0.015217,
  "curve": 0.001,
  "shape": "glint",
  "z": 0.08700496445046771
 },
 {
  "y": 0.042281,
  "height": 0.026806,
  "x": -0.02,
  "halfWidth": 0.015888,
  "curve": 0.001,
  "shape": "glint",
  "z": 0.08494765031693113
 },
 {
  "y": 0.046906,
  "height": 0.021893,
  "x": 0,
  "halfWidth": 0.018983,
  "curve": 0.001,
  "shape": "glint",
  "z": 0.08338527268275923
 }
];
export function createLuzV21(pc,app,bladeAabb){
 return createV21SurfaceChannel(pc,app,bladeAabb,{
  id:'luz',fragmentGLSL,patches,lightColor:[1,0.83,0.47],
  lightIntensity:0.18,
 });
}
