import {useState} from 'react';
import type {FormEvent} from 'react';
import {ShieldCheck, LoaderCircle} from 'lucide-react';
import {request, saveAccountSession} from './api';
import type {AccountSession} from './api';

export function SignIn({onSignIn,notice}:{onSignIn:(account:AccountSession)=>Promise<void>;notice:string}){
 const [username,setUsername]=useState('evaluator');const [password,setPassword]=useState('evaluator123456');
 const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 async function submit(event:FormEvent){event.preventDefault();setBusy(true);setError('');try{
  const account=await request<AccountSession>('/v1/auth/login',undefined,'POST',{username,password});
  saveAccountSession(account);setPassword('');await onSignIn(account);
 }catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <main className="signin-shell"><section className="signin-card" aria-labelledby="signin-title">
  <div className="brand"><span className="brand-mark"><ShieldCheck size={24}/></span><span>sachet<span className="brand-dot">.</span></span></div>
  <h1 id="signin-title">Open your workspace.</h1><p>Explore Sachet with the evaluator account below.</p>
  {(error||notice)&&<p className="form-error" role="alert">{error||notice}</p>}
  <form onSubmit={submit}><label>Username<input autoComplete="username" autoCapitalize="none" spellCheck={false} required maxLength={120} value={username} onChange={e=>setUsername(e.target.value)}/></label>
   <label>Password<input type="password" autoComplete="current-password" required maxLength={256} value={password} onChange={e=>setPassword(e.target.value)}/></label>
   <button className="button primary" disabled={busy} type="submit">{busy?<LoaderCircle size={17} className="spin"/>:null}{busy?'Signing in…':'Sign in'}</button>
  </form><dl className="signin-demo-credentials" aria-label="Evaluator demo credentials"><div><dt>Demo username</dt><dd>evaluator</dd></div><div><dt>Demo password</dt><dd>evaluator123456</dd></div></dl>
 </section></main>
}
