// Project Genesis - Hielo V21, experimental surface-bound effect.
// Independent shader; NO approved fire or rayo source file modifications.
// Visual design: cristales azulados que crecen en facetas superiores de la hoja.
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
 vec2 cell=vec2(x*2.8+seed*.47,v*7.0);
 float facets=abs(fract(cell.x*.72+cell.y*.33)-.5);
 float brittle=abs(fract(cell.x*.42-cell.y*.61)-.5);
 float crystal=1.-smoothstep(.20,.37,facets*.57+brittle*.43);
 float edge=1.-smoothstep(.50,.97,abs(x));
 float growing=.37+.63*smoothstep(.19,.82,genesisFbm(vec2(cell.x+t*.08,cell.y-t*.38)));
 float flicker=.87+.13*sin(t*3.2+seed*1.9+v*16.);
 float alpha=clamp(power*(.20+.46*power)*edge*crystal*growing,0.,.72);
 if(alpha<.008)discard;
 vec3 ice=vec3(.24,.62,1.25);
 vec3 frost=vec3(.76,.94,1.68);
 vec3 rgb=mix(ice,frost,crystal*.72+smoothstep(.81,.96,genesisNoise(cell*2.5-t*.1))*.18);
 gl_FragColor=vec4(rgb*(.55+.65*power)*flicker,alpha);
}
`;
export const HIELO_V21_SPEC=Object.freeze({
  id:'Genesis_Hielo_V21_Cristalizacion',affinity:'hielo',approved:false,
  scope:'only original V03 sword test',intensity:[0,100],
  source:'V21 affinity zone contract, concept implementation not user approved',
  manifest:'vfx/experimental/Genesis_AffinitySlots_V01.mjs',
  semanticSlot:'blade_upper_facet',
  visual:'cristales azulados que crecen en facetas superiores de la hoja',
  preservesGLB:true,preservesPBRV175:true,
  independent:true,composabilityTested:false,otherObjectFamiliesImplemented:false
});
const patches=[
 {
  "y": 0.761523,
  "height": 0.02747,
  "x": -0.02,
  "halfWidth": 0.014926,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.086
 },
 {
  "y": 0.771614,
  "height": 0.027565,
  "x": 0,
  "halfWidth": 0.012333,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.08793265306171306
 },
 {
  "y": 0.781705,
  "height": 0.026029,
  "x": 0.02,
  "halfWidth": 0.014518,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.08895634918996537
 },
 {
  "y": 0.791795,
  "height": 0.028904,
  "x": -0.009,
  "halfWidth": 0.015768,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.08858962809994661
 },
 {
  "y": 0.801886,
  "height": 0.02488,
  "x": 0.011,
  "halfWidth": 0.012814,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.08700496445046771
 },
 {
  "y": 0.811977,
  "height": 0.029785,
  "x": -0.02,
  "halfWidth": 0.01338,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.08494765031693113
 },
 {
  "y": 0.822068,
  "height": 0.024325,
  "x": 0,
  "halfWidth": 0.015985,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.08338527268275923
 },
 {
  "y": 0.832159,
  "height": 0.029978,
  "x": 0.02,
  "halfWidth": 0.013818,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.08305264216212699
 },
 {
  "y": 0.84225,
  "height": 0.024508,
  "x": -0.009,
  "halfWidth": 0.012544,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.08410620008638303
 },
 {
  "y": 0.852341,
  "height": 0.029432,
  "x": 0.011,
  "halfWidth": 0.015495,
  "curve": 0.002,
  "shape": "crystal",
  "z": 0.08605044170145304
 }
];
export function createHieloV21(pc,app,bladeAabb){
 return createV21SurfaceChannel(pc,app,bladeAabb,{
  id:'hielo',fragmentGLSL,patches,lightColor:[0.52,0.76,1],
  lightIntensity:0.18,
 });
}
