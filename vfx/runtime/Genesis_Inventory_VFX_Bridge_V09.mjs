// Project Genesis V09 bridge for inventories, results screens and mercenary equipment.
// This file does not modify gameplay save data, equipped GLB, material or the UI.
import {createSevenChannelRig,ELEMENTAL_CHANNELS} from './Genesis_Universal_7Canales_V09.mjs';

export const BASE_CHANNEL='Base';
export const CHANNEL_SET=new Set(ELEMENTAL_CHANNELS);
export const validateChannelLevels=(levels)=>{
 if(!levels||typeof levels!=='object')return {};
 const out={};
 for(const [key,value] of Object.entries(levels)){
   if(key===BASE_CHANNEL)continue; // Base is physical damage/protection, no FX.
   if(key==='Veneno')continue; // Poison is learned Nature technique, not default affinity.
   if(!CHANNEL_SET.has(key))throw Error('UNSUPPORTED_ELEMENTAL_CHANNEL: '+key);
   if(!Number.isFinite(Number(value)))throw Error('INVALID_ELEMENTAL_INTENSITY: '+key);
   const v=Math.max(0,Math.min(100,Number(value)));
   if(v>0)out[key]=v; // Missing channel stays missing: no zero-bars or placeholders.
 }
 return out;
};
export function connectGenesisElementalVFX(pc,app,assetRoot,{
 kind,bladeAabb=null,initialChannels={},getTime=()=>0
}={}){
 if(!assetRoot||!assetRoot.enabled)throw Error('GENESIS_VFX_ASSET_ROOT_REQUIRED');
 const rig=createSevenChannelRig(pc,app,assetRoot,{kind,bladeAabb});
 let current=validateChannelLevels(initialChannels),alive=true;
 function setChannels(values){
   if(!alive)throw Error('VFX_BRIDGE_DISPOSED');
   current=validateChannelLevels(values);
   rig.apply(getTime(),current);
   return {...current};
 }
 function tick(time=getTime()){
   if(!alive)return;
   rig.apply(time,current);
 }
 setChannels(current);
 return {
   kind,
   rig,
   setChannels,
   tick,
   channels:()=>({...current}),
   destroy(){
     if(!alive)return;
     alive=false;
     rig.destroy();
   }
 };
}
