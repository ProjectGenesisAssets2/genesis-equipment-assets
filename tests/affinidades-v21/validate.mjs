import assert from 'node:assert/strict';
import {verifyNewChannelBands,V21_ZONE_BANDS,V21_NEW_CHANNELS} from '../../vfx/experimental/Genesis_AffinitySurfaceCore_V21.mjs';
import {inspectProfile,CHANNELS,CHANNEL_POLICY} from '../../vfx/experimental/Genesis_AffinitySlots_V01.mjs';
import {HIELO_V21_SPEC} from '../../vfx/experimental/Genesis_Hielo_V21_Cristalizacion.mjs';
import {LUZ_V21_SPEC} from '../../vfx/experimental/Genesis_Luz_V21_Destellos.mjs';
import {SOMBRA_V21_SPEC} from '../../vfx/experimental/Genesis_Sombra_V21_Brumas.mjs';
import {NATURALEZA_V21_SPEC} from '../../vfx/experimental/Genesis_Naturaleza_V21_Filamentos.mjs';
import {TIERRA_V21_SPEC} from '../../vfx/experimental/Genesis_Tierra_V21_Mineral.mjs';
const expected=['hielo','luz','sombra','naturaleza','tierra'];
assert.deepEqual(V21_NEW_CHANNELS,expected);
assert.deepEqual(verifyNewChannelBands().map(x=>x.id).sort(),expected.slice().sort());
const defs=[HIELO_V21_SPEC,LUZ_V21_SPEC,SOMBRA_V21_SPEC,NATURALEZA_V21_SPEC,TIERRA_V21_SPEC];
for(const x of defs){
 assert.equal(x.approved,false);
 assert.equal(x.preservesGLB,true);
 assert.equal(x.preservesPBRV175,true);
 assert.equal(x.independent,true);
 assert.equal(x.composabilityTested,false);
 assert.equal(x.otherObjectFamiliesImplemented,false);
 assert.deepEqual(x.intensity,[0,100]);
 const band=V21_ZONE_BANDS[x.affinity];assert.ok(band);
}
for(const name of ['sword','shield','armor','jewel']) {
 const p=inspectProfile(name);
 assert.equal(p.masksUnique,true);
 assert.equal(p.physicalOverlapVerified,false);
}
assert.equal(CHANNELS.length,7);
assert.equal(CHANNEL_POLICY.runtimeFullyImplemented,false);
assert.equal(new Set(defs.map(x=>x.affinity)).size,5);
console.log('GENESIS_V21_FIVE_INDEPENDENT_AFFINITIES_STATIC_VALIDATED',JSON.stringify({
 channels:expected,zones:V21_ZONE_BANDS,notYetApproved:true,
 physicalExclusivityWithinFive:'5 y bands mathematically disjoint',
 againstFireAndRayo:'not yet verified',otherFamilies:'not yet implemented'
}));
