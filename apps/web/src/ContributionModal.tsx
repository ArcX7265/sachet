import { useEffect, useState } from 'react';
import { Check, Clock3, GitBranch } from 'lucide-react';
import { request } from './api';
import { Modal, Spinner } from './App';
import type { Case } from './types';

export function ContributionModal({data,token,busy,act,update,onClose,toast}:{data:Case;token:string;busy:boolean;act:(fn:()=>Promise<void>)=>Promise<void>;update:(data:Case)=>Promise<void>;onClose:()=>void;toast:(text:string)=>void}){
 const [preview,setPreview]=useState<{report:Record<string,unknown>;preview_digest:string}|null>(null);
 const [narrative,setNarrative]=useState('');
 const [previewNarrative,setPreviewNarrative]=useState('');
 const [refresh,setRefresh]=useState(0);
 const [error,setError]=useState('');
 const [consent,setConsent]=useState(false);
 useEffect(()=>{let mounted=true;setPreview(null);setConsent(false);setError('');const timer=setTimeout(()=>void request<Record<string,unknown>&{preview_digest:string}>(`/v1/cases/${data.id}/contributions/preview`,token,'POST',{narrative}).then(value=>{if(typeof value.preview_digest!=='string'||value.preview_digest.length!==64)throw new Error('The sharing preview could not be verified. Please retry.');if(mounted){const {preview_digest,...report}=value;setPreview({report,preview_digest});setPreviewNarrative(narrative)}}).catch(reason=>{if(mounted)setError((reason as Error).message)}),350);return()=>{mounted=false;clearTimeout(timer)}},[data.id,data.revision,token,narrative,refresh]);
 const current=preview!==null&&previewNarrative===narrative;
 return <Modal title="Share a report for review" onClose={onClose} wide><p className="modal-description">Preview exactly what an analyst will receive. The report includes detected action categories. You can also describe the sequence in your own words to help reviewers investigate an unfamiliar request.</p>
  <label>What happened, in your own words? <span className="field-help">Optional. Remove names, contact details, payment addresses, account details, and secrets. Your description will be shared with analysts after you consent.</span><textarea rows={4} maxLength={2000} value={narrative} onChange={e=>{setNarrative(e.target.value);setConsent(false)}} placeholder="For example: A supposed recruiter moved the conversation to another app, then asked for a release-code deposit before paying me."/><span className="field-help">{narrative.length}/2000 characters. Inspect the preview yourself; automatic checks cannot guarantee that all sensitive details are removed.</span></label>
  {error?<div><p className="form-error" role="alert">{error}</p><button className="text-button" onClick={()=>setRefresh(value=>value+1)}>Retry preview</button></div>:!current?<div className="inline-progress"><Spinner/>Preparing the sharing preview…</div>:<pre className="json-preview review-data" aria-label="Exact contribution preview">{JSON.stringify(preview?.report,null,2)}</pre>}
  <ul className="consent-list"><li><Check size={16}/>Sharing is separate from assessment.</li><li><Check size={16}/>Original case messages and title are excluded; your optional description is included.</li><li><Check size={16}/>Analysts must review and evaluate a proposed update before release.</li><li><Check size={16}/>Withdraw at any time from this case.</li></ul>
  <div className="info-note"><Clock3 size={17}/><p>Contributions expire after 30 days and are withdrawn if the source case is deleted or expires. Deleting the case removes dependent detection proposals and restores a valid baseline where required.</p></div>
  <label className="consent-checkbox"><input type="checkbox" checked={consent} disabled={!current||!!error} onChange={e=>setConsent(e.target.checked)}/><span>I have inspected the preview, removed sensitive details from my description, and agree to share this exact report for analyst review.</span></label>
  <div className="modal-actions"><button className="button secondary" onClick={onClose}>Keep private</button><button className="button primary" disabled={busy||!current||!consent||!!error} onClick={()=>void act(async()=>{await request(`/v1/cases/${data.id}/contributions`,token,'POST',{consent:true,narrative,preview_digest:preview?.preview_digest});await update(await request<Case>(`/v1/cases/${data.id}`,token));onClose();toast('Your previewed report was contributed for analyst review.');})}>{busy?<Spinner/>:<GitBranch size={16}/>}Consent & share</button></div>
 </Modal>;
}
