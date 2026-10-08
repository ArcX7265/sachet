import type { Role } from './types';
const API_BASE=(import.meta.env.VITE_API_BASE_URL||'/api').replace(/\/$/,'');
const STORAGE='sachet-demo-sessions-v1';
const ACCOUNT_STORAGE='sachet-account-session-v1';
export type AccountSession={token:string;role:Role;expires_at:string};
export function accountToken(){return sessionStorage.getItem(ACCOUNT_STORAGE)||''}
export function saveAccountSession(value:AccountSession){sessionStorage.setItem(ACCOUNT_STORAGE,value.token)}
export function clearAccountSession(){sessionStorage.removeItem(ACCOUNT_STORAGE)}
export function savedTokens():Partial<Record<Role,string>> {try{return JSON.parse(sessionStorage.getItem(STORAGE)||'{}')}catch{return {}}}
export async function session(role:Role){const tokens=savedTokens();if(tokens[role])return tokens[role]!;const data=await request<{token:string}>('/v1/sessions',undefined,'POST',{role});tokens[role]=data.token;sessionStorage.setItem(STORAGE,JSON.stringify(tokens));return data.token;}
export async function request<T>(path:string,token?:string,method='GET',body?:unknown):Promise<T>{
  let response:Response;
  try {response=await fetch(`${API_BASE}${path}`,{method,headers:{...(body!==undefined?{'Content-Type':'application/json'}:{}),...(token?{Authorization:`Bearer ${token}`}:{})},body:body!==undefined?JSON.stringify(body):undefined});}catch {throw new Error('Sachet could not reach the service. Check your connection, then retry.');}
  const data=await response.json().catch(()=>null);
  if(!response.ok){if(response.status===401&&token&&accountToken()===token){clearAccountSession();window.dispatchEvent(new Event('sachet-session-expired'))}const detail=data?.detail;throw new Error(typeof detail==='string'?detail:Array.isArray(detail)?detail.map((d:{msg:string})=>d.msg).join('; '):detail?.message||data?.message||`Request could not be completed (${response.status}).`)}
  return data as T;
}
export const unique=()=>crypto.randomUUID();
export async function extractImage(file:File,onProgress:(message:string)=>void,qrOnly=false):Promise<{text:string;qr:string|null}>{
  if(!['image/png','image/jpeg','image/webp'].includes(file.type))throw new Error('Choose a PNG, JPEG, or WebP image.');
  if(file.size>8*1024*1024)throw new Error('Choose an image smaller than 8 MB.');
  onProgress('Reading image on this device…');
  const bitmap=await createImageBitmap(file);
  if(bitmap.width*bitmap.height>25000000){bitmap.close();throw new Error('This image is too large. Choose one below 25 megapixels.');}
  const canvas=document.createElement('canvas');canvas.width=bitmap.width;canvas.height=bitmap.height;
  const context=canvas.getContext('2d',{willReadFrequently:true});if(!context)throw new Error('This browser cannot read the selected image.');
  context.drawImage(bitmap,0,0);bitmap.close();
  const {default:jsQR}=await import('jsqr');const pixels=context.getImageData(0,0,canvas.width,canvas.height);const qr=jsQR(pixels.data,pixels.width,pixels.height)?.data??null;
  if(qrOnly){if(!qr)throw new Error('No readable QR code found. Try a sharper image or paste the payment link.');return{text:'',qr};}
  onProgress('Loading local English text recognition…');
  const {createWorker}=await import('tesseract.js');const worker=await createWorker('eng',1,{logger:m=>{if(m.status==='recognizing text')onProgress(`Reading text locally · ${Math.round(m.progress*100)}%`);}});
  try{const result=await worker.recognize(canvas);return{text:result.data.text,qr};}finally{await worker.terminate();}
}
