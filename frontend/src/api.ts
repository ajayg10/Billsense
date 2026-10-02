import type { Report, Inspection, Options } from './types';
async function request<T>(url:string, options?:RequestInit):Promise<T> {const r=await fetch(url, options);const data=await r.json();if(!r.ok)throw new Error(data.error?.message || data.detail?.[0]?.msg || 'The request could not be completed. Please try again.');return data;}
export const sample=()=>request<Report>('/api/v1/samples/student-project');
export const inspect=(file:File)=>{const f=new FormData();f.append('file',file);return request<Inspection>('/api/v1/inspect',{method:'POST',body:f});};
export function form(files:File[], opts:Options[]){const f=new FormData();f.append('current',files[0]);if(files[1])f.append('previous',files[1]);f.append('options',JSON.stringify({current:opts[0],...(files[1]?{previous:opts[1]}:{})}));return f;}
export const analyze=(files:File[],opts:Options[])=>request<Report>('/api/v1/analyze',{method:'POST',body:form(files,opts)});
export async function explain(files:File[],opts:Options[]){const f=form(files,opts);f.append('consent','true');return request<{mode:string;message?:string;explanations:{finding_id:string;text:string}[]}>('/api/v1/explain',{method:'POST',body:f});}
