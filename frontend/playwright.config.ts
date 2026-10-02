import {defineConfig} from '@playwright/test';
import chromium from '@sparticuz/chromium';
const packaged=process.env.BILLSENSE_PACKAGED_BROWSER==='1';
export default defineConfig({testDir:'./tests',workers:1,use:{baseURL:'http://127.0.0.1:5173',headless:true,launchOptions:packaged?{executablePath:await chromium.executablePath(),args:chromium.args.filter(a=>!['--single-process','--disable-web-security','--allow-running-insecure-content'].includes(a))}:{}},reporter:'list',timeout:30000});
