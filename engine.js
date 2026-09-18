import { Chess } from 'chess.js'

const VALUE = { p: 100, n: 320, b: 330, r: 500, q: 900, k: 20000 }
const PST = {
  p: [0,0,0,0,0,0,0,0, 50,50,50,50,50,50,50,50, 10,10,20,30,30,20,10,10, 5,5,10,25,25,10,5,5, 0,0,0,20,20,0,0,0, 5,-5,-10,0,0,-10,-5,5, 5,10,10,-20,-20,10,10,5, 0,0,0,0,0,0,0,0],
  n: [-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,0,0,0,-20,-40, -30,0,10,15,15,10,0,-30, -30,5,15,20,20,15,5,-30, -30,0,15,20,20,15,0,-30, -30,5,10,15,15,10,5,-30, -40,-20,0,5,5,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50],
  b: [-20,-10,-10,-10,-10,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,10,10,5,0,-10, -10,5,5,10,10,5,5,-10, -10,0,10,10,10,10,0,-10, -10,10,10,10,10,10,10,-10, -10,5,0,0,0,0,5,-10, -20,-10,-10,-10,-10,-10,-10,-20],
  r: [0,0,0,5,5,0,0,0, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, 5,10,10,10,10,10,10,5, 0,0,0,0,0,0,0,0],
  q: [-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5, 0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10, -20,-10,-10,-5,-5,-10,-10,-20],
  k: [-30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -20,-30,-30,-40,-40,-30,-30,-20, -10,-20,-20,-20,-20,-20,-20,-10, 20,20,0,0,0,0,20,20]
}

function idx(file, rank){ return (7-rank)*8 + file }
function pieceScore(piece, file, rank){
  const table = PST[piece.type]
  const square = piece.color === 'w' ? idx(file, rank) : idx(file, 7-rank)
  return VALUE[piece.type] + (table ? table[square] : 0)
}

export function evaluate(chess){
  let score = 0
  for(let r=0;r<8;r++) for(let f=0;f<8;f++){
    const sq = String.fromCharCode(97+f)+(r+1)
    const p = chess.get(sq)
    if(p) score += (p.color==='w'?1:-1)*pieceScore(p,f,r)
  }
  if(chess.isCheck()) score += chess.turn()==='w' ? -45 : 45
  if(chess.isCheckmate()) score += chess.turn()==='w' ? -30000 : 30000
  return score
}

function orderedMoves(chess){
  return chess.moves({ verbose:true }).sort((a,b)=>{
    const av=(a.captured?VALUE[a.captured]:0)+(a.promotion?VALUE[a.promotion]:0)+(a.san.includes('+')?80:0)
    const bv=(b.captured?VALUE[b.captured]:0)+(b.promotion?VALUE[b.promotion]:0)+(b.san.includes('+')?80:0)
    return bv-av
  })
}

function search(chess, depth, alpha, beta){
  if(depth===0 || chess.isGameOver()) return {score:evaluate(chess)}
  const moves=orderedMoves(chess)
  if(!moves.length) return {score:evaluate(chess)}
  const maximizing=chess.turn()==='w'
  let bestScore=maximizing?-Infinity:Infinity
  let bestMove=moves[0]
  for(const move of moves){
    chess.move(move)
    const result=search(chess,depth-1,alpha,beta)
    chess.undo()
    if(maximizing){
      if(result.score>bestScore){bestScore=result.score;bestMove=move}
      alpha=Math.max(alpha,bestScore)
    }else{
      if(result.score<bestScore){bestScore=result.score;bestMove=move}
      beta=Math.min(beta,bestScore)
    }
    if(beta<=alpha) break
  }
  return {score:bestScore,move:bestMove}
}

export function getBestMove(fen, depth=2){
  const chess=new Chess(fen)
  const result=search(chess,Math.max(1,Math.min(4,depth)),-Infinity,Infinity)
  return result.move ? {uci: result.move.from+result.move.to+(result.move.promotion||''), san:result.move.san, score:result.score} : null
}

export function rankMove(fen, uci, depth=2){
  const chess=new Chess(fen)
  const moves=orderedMoves(chess)
  const ranked=[]
  for(const move of moves){
    chess.move(move)
    const result=search(chess,Math.max(0,depth-1),-Infinity,Infinity).score
    chess.undo()
    const scoreForMover=chess.turn()==='w'?result:-result
    ranked.push({uci:move.from+move.to+(move.promotion||''),score:scoreForMover,san:move.san})
  }
  ranked.sort((a,b)=>b.score-a.score)
  const idx=ranked.findIndex(m=>m.uci===uci)
  const best=ranked[0]
  const played=idx>=0?ranked[idx]:{score:best?.score||0}
  return {rank:idx<0?99:idx+1,best,bestScore:best?.score||0,playedScore:played.score,loss:Math.max(0,(best?.score||0)-played.score)}
}

export function classifyMove(fen, uci, san, depth=2){
  const chess=new Chess(fen)
  const best=getBestMove(fen,depth)
  const stats=rankMove(fen,uci,depth)
  if(chess.history().length<10) return {label:'BOOK MOVE',...stats,bestMove:best?.uci||''}
  if(!best) return {label:'GOOD MOVE',...stats,bestMove:''}
  if(uci===best.uci) return {label:'BEST MOVE',...stats,bestMove:best.uci}
  const move=chess.move({from:uci.slice(0,2),to:uci.slice(2,4),promotion:uci.slice(4)||undefined})
  const brilliant=move?.captured && move?.san?.includes('+') && stats.loss<=35
  if(brilliant) return {label:'BRILLIANT MOVE',...stats,bestMove:best.uci}
  if(stats.rank<=2 && stats.loss<=10) return {label:'GREAT MOVE',...stats,bestMove:best.uci}
  if(stats.rank<=3 && stats.loss<=25) return {label:'EXCELLENT MOVE',...stats,bestMove:best.uci}
  if(stats.rank<=5 && stats.loss<=50) return {label:'GOOD MOVE',...stats,bestMove:best.uci}
  if(stats.loss<=100) return {label:'INACCURACY',...stats,bestMove:best.uci}
  if(stats.loss<=250) return {label:'MISTAKE',...stats,bestMove:best.uci}
  return {label:'BLUNDER',...stats,bestMove:best.uci}
}

export function makeBotMove(fen, level){
  const depth = level==='beginner'?1:level==='intermediate'?2:3
  const best=getBestMove(fen,depth)
  if(!best) return null
  return best
}
