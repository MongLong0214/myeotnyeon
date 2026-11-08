// Local-file/stdio adapter for Remotion in a sandbox without listening sockets.
// No installed packages are modified. No network access is required.
const path=require('node:path'), fs=require('node:fs'), cp=require('node:child_process');
const root='../..';
const dist=root+'/node_modules/@remotion/renderer/dist/';
const {Connection}=require(dist+'browser/Connection.js');
require(dist+'browser/BrowserRunner.js').makeBrowserRunner=async ({executablePath,processArguments})=>{
 const args=processArguments.filter(a=>!a.startsWith('--remote-debugging-port'));
 args.push('--remote-debugging-pipe','--allow-file-access-from-files');
 const proc=cp.spawn(executablePath,args,{stdio:['ignore','pipe','pipe','pipe','pipe']});
 let pending='';
 const transport={onmessage:null,onclose:null,send(message){proc.stdio[3].write(message+'\0')},close(){proc.stdio[3].destroy();proc.stdio[4].destroy()},forgetEventLoop(){proc.unref();for(const s of proc.stdio) s?.unref?.()},rememberEventLoop(){proc.ref();for(const s of proc.stdio) s?.ref?.()}};
 proc.stdio[4].on('data',chunk=>{pending+=chunk.toString();let i;while((i=pending.indexOf('\0'))!==-1){const line=pending.slice(0,i);pending=pending.slice(i+1);if(line) transport.onmessage?.(line)}});
 proc.stderr.on('data',()=>{});proc.stdout.on('data',()=>{});
 proc.on('exit',()=>transport.onclose?.());
 const connection=new Connection(transport);
 const closeProcess=async()=>{if(proc.exitCode!==null)return;const done=new Promise(r=>proc.once('exit',r));proc.kill('SIGTERM');await done};
 return {connection,listeners:[],closeProcess,deleteBrowserCaches(){},forgetEventLoop:()=>transport.forgetEventLoop(),rememberEventLoop:()=>transport.rememberEventLoop()};
};
const {makeDownloadMap,cleanDownloadMap}=require(dist+'assets/download-map.js');
const {startOffthreadVideoServer}=require(dist+'offthread-video-server.js');
require(dist+'prepare-server.js').prepareServer=async opts=>{
 const bundle=opts.webpackConfigOrServeUrl;
 if(!path.isAbsolute(bundle))throw Error('Offline renderer expects a local bundle');
 const downloadMap=makeDownloadMap(opts.sampleRate);
 const offthread=startOffthreadVideoServer({...opts,downloadMap});
 return {serveUrl:require('node:url').pathToFileURL(path.join(bundle,'index.html')).href,offthreadPort:0,sourceMap:()=>null,downloadMap,compositor:offthread.compositor,closeServer:async()=>{await offthread.close();cleanDownloadMap(downloadMap)}};
};
