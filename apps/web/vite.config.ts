import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig(({command})=>{
  if(command==='build'&&process.env.VERCEL==='1'){
    const api=process.env.VITE_API_BASE_URL;
    if(!api||!/^https:\/\/[^/]+\/?$/.test(api))throw new Error('Set VITE_API_BASE_URL to the HTTPS origin of the Sachet API project.');
  }
  return {plugins:[react()],server:{host:'127.0.0.1',port:5173,strictPort:true,proxy:{'/api':{target:process.env.API_PROXY_TARGET||'http://127.0.0.1:8000',changeOrigin:true,rewrite:path=>path.replace(/^\/api/,'')}}}};
});
