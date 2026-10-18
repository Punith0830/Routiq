const fs=require('node:fs');const version=JSON.parse(fs.readFileSync('package.json','utf8')).version;
fs.writeFileSync('src/app/core/build-version.ts','// Generated from package.json; do not hand-edit.\nexport const APP_VERSION='+JSON.stringify(version)+';\n');

