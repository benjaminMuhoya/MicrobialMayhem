import { defineConfig } from "@playwright/test";
export default defineConfig({testDir:"./e2e",timeout:45_000,use:{baseURL:"http://127.0.0.1:3000",viewport:{width:1280,height:900}},webServer:{command:"npm run build:pages && python3 -m http.server 3000 --bind 127.0.0.1 --directory dist/pages",url:"http://127.0.0.1:3000",reuseExistingServer:true,timeout:120_000},reporter:"line"});
