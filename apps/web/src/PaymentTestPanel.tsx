import { useEffect, useRef, useState } from 'react';
import { ExternalLink, FlaskConical, RefreshCw } from 'lucide-react';
import { request, unique } from './api';
import type { Health, Payment } from './types';
import { Badge, Spinner } from './App';

type TestOrder={id:string;key_id:string;amount:number;currency:string;status:string;verified:boolean;mode:'test';limitations:string[]};
type CheckoutInstance={open:()=>void;on:(name:string,callback:()=>void)=>void};
declare global{interface Window{Razorpay?:new(options:Record<string,unknown>)=>CheckoutInstance}}
let checkoutLoading:Promise<void>|null=null;
async function checkoutScript(){
 if(window.Razorpay)return;
 if(!checkoutLoading)checkoutLoading=new Promise<void>((resolve,reject)=>{
  const script=document.createElement('script');script.src='https://checkout.razorpay.com/v1/checkout.js';script.async=true;
  script.onload=()=>window.Razorpay?resolve():reject(new Error('The test checkout did not initialize.'));
  script.onerror=()=>{script.remove();checkoutLoading=null;reject(new Error('The Razorpay test checkout could not be loaded.'))};document.head.appendChild(script);
 });
 await checkoutLoading;
}

export function PaymentTestPanel({payment,token}:{payment:Payment;token:string}){
 const [health,setHealth]=useState<Health|null>(null);
 const [order,setOrder]=useState<TestOrder|null>(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const [message,setMessage]=useState('');
 const idem=useRef(unique());
 useEffect(()=>{let mounted=true;void request<Health>('/health').then(h=>{if(mounted)setHealth(h)}).catch(e=>{if(mounted)setError((e as Error).message)});return()=>{mounted=false}},[]);
 const run=async(operation:()=>Promise<void>)=>{setBusy(true);setError('');try{await operation()}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 const create=async()=>{const next=await request<TestOrder>('/v1/payments/test-orders',token,'POST',{payment_request_id:payment.id,digest:payment.digest,idempotency_key:idem.current});setOrder(next);return next};
 const refresh=async()=>{if(order)setOrder(await request<TestOrder>(`/v1/payments/test-orders/${order.id}`,token))};
 const open=async()=>{
  const next=await create(); // Validate current case binding again before reopening checkout.
  if(!next.key_id.startsWith('rzp_test_')||next.mode!=='test')throw new Error('Only a configured test-mode checkout may open.');
  if(next.status==='captured'){setMessage('The server has already confirmed this test order as captured.');return;}
  await checkoutScript();
  const Checkout=window.Razorpay;if(!Checkout)throw new Error('Test checkout is unavailable.');
  const checkout=new Checkout({key:next.key_id,order_id:next.id,amount:next.amount,currency:next.currency,name:'Sachet test merchant',description:'Test gateway flow — preview recipient is not paid',handler:()=>{setMessage('Checkout returned. Refresh the server status; this browser response does not confirm capture.');},modal:{ondismiss:()=>setMessage('Checkout closed. Refresh the server status if you attempted a test payment.')},theme:{color:'#206c55'}});
  checkout.on('payment.failed',()=>setMessage('Checkout reported a failed attempt. Refresh the server status for its verified record.'));
  checkout.open();
 };
 return <section className="panel payment-test-panel"><div className="section-heading"><h3><FlaskConical size={17}/>Test gateway</h3><Badge>{health?.capabilities.payment_test.configured?'Configured':'Unavailable'}</Badge></div><p className="field-help">A separate test order is payable to the configured test merchant. It does not pay the UPI recipient in the preview. No live payments are enabled.</p>
 {!health?.capabilities.payment_test.configured?<p className="field-help">Server test keys and a signed-webhook secret are required. This installation has no connected test gateway.</p>:<>
 {order?<><dl className="test-order-details"><div><dt>Order</dt><dd>{order.id}</dd></div><div><dt>Server status</dt><dd>{order.status} {order.verified?'· signed event verified':'· capture unconfirmed'}</dd></div><div><dt>Test amount</dt><dd>{order.currency} {(order.amount/100).toLocaleString('en-IN')}</dd></div></dl>{order.status==='captured'&&order.verified?<div className="info-note"><p>Test capture confirmed by a matching signed gateway event. This does not represent a payment to the preview recipient.</p></div>:<button className="button secondary small" disabled={busy} onClick={()=>void run(open)}><ExternalLink size={14}/>Open test checkout</button>}<button className="text-button" disabled={busy} onClick={()=>void run(refresh)}><RefreshCw size={14}/>Refresh server status</button></>:<button className="button secondary small" disabled={busy||!payment.amount} onClick={()=>void run(async()=>{await create();setMessage('Test order created. Open checkout to attempt a test payment.');})}>{busy?<Spinner/>:<FlaskConical size={14}/>}Create test order</button>}
 {!payment.amount&&<p className="field-help">An explicit amount is needed for a test order.</p>}
 </>}
 {message&&<p className="field-help" role="status">{message}</p>}{error&&<p className="form-error" role="alert">{error}</p>}
 </section>;
}
