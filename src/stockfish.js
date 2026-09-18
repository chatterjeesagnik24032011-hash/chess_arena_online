// Browser Stockfish adapter. Vercel proxies the official npm package files through /stockfish/.
let worker=null
let readyPromise=null
let queue=[]
let active=null

function ensure(){
  if(worker) return readyPromise
  worker=new Worker('/stockfish/stockfish-19-lite-single.js')
  readyPromise=new Promise(resolve=>{
    const onMessage=e=>{const line=typeof e.data==='string'?e.data:'';if(line==='uciok'){worker.removeEventListener('message',onMessage);resolve()}}
    worker.addEventListener('message',onMessage)
    worker.postMessage('uci')
  })
  worker.addEventListener('message',e=>{
    const line=typeof e.data==='string'?e.data:''
    if(!active)return
    if(line.startsWith('info ') && line.includes(' score ')){
      const mate=line.match(/score mate (-?\d+)/),cp=line.match(/score cp (-?\d+)/)
      if(mate)active.info={cp:Number(mate[1])*10000,mate:Number(mate[1])}
      else if(cp)active.info={cp:Number(cp[1]),mate:null}
    }
    const m=line.match(/^bestmove\s+(\S+)/)
    if(m){const a=active;active=null;a.resolve({bestmove:m[1],cp:a.info?.cp??0,mate:a.info?.mate??null})}
  })
  return readyPromise
}

export async function analyzeFen(fen,{depth=12,multipv=1}={}){
  await ensure()
  if(active){worker.postMessage('stop');await new Promise(r=>setTimeout(r,10))}
  return new Promise(resolve=>{
    active={resolve,info:{cp:0,mate:null}}
    worker.postMessage('setoption name MultiPV value '+multipv)
    worker.postMessage('position fen '+fen)
    worker.postMessage('go depth '+depth)
  })
}

export function terminateStockfish(){if(worker)worker.terminate();worker=null;readyPromise=null;active=null}
