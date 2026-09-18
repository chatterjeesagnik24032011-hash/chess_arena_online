import React, {useEffect, useMemo, useState} from 'react'
import {createRoot} from 'react-dom/client'
import {Chess} from 'chess.js'
import {supabase} from './supabase'
import './styles.css'

const PIECES={w:{p:'♙',n:'♘',b:'♗',r:'♖',q:'♕',k:'♔'},b:{p:'♟',n:'♞',b:'♝',r:'♜',q:'♛',k:'♚'}}
const CLASS_INFO={
  'BRILLIANT MOVE':{icon:'!!',color:'#3aa7ff'},
  'BOOK MOVE':{icon:'▣',color:'#d7b98b'},
  'BEST MOVE':{icon:'✓',color:'#7ca58a'},
  'GREAT MOVE':{icon:'!',color:'#72a9d8'},
  'EXCELLENT MOVE':{icon:'★',color:'#80bd4b'},
  'GOOD MOVE':{icon:'👍',color:'#92b77b'},
  'INACCURACY':{icon:'?!',color:'#f0c72b'},
  'MISTAKE':{icon:'?',color:'#f19a45'},
  'BLUNDER':{icon:'??',color:'#ef5757'}
}

function classify(game, move){
  // Client-side placeholder classification for live multiplayer. Offline/AI review can be upgraded with Stockfish later.
  if(game.history().length<=8) return 'BOOK MOVE'
  if(move.san.includes('#')) return 'BLUNDER'
  if(move.san.includes('+') && (move.captured || move.piece==='q')) return 'EXCELLENT MOVE'
  if(move.captured) return 'GOOD MOVE'
  if(move.san.includes('+')) return 'GREAT MOVE'
  return 'GOOD MOVE'
}

function Auth({onReady}){
  const [mode,setMode]=useState('login'),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[name,setName]=useState(''),[msg,setMsg]=useState('')
  const submit=async e=>{e.preventDefault();setMsg('')
    if(!supabase){setMsg('Add Supabase environment variables first.');return}
    let result
    if(mode==='login') result=await supabase.auth.signInWithPassword({email,password})
    else result=await supabase.auth.signUp({email,password,options:{data:{display_name:name}}})
    if(result.error){setMsg(result.error.message);return}
    if(mode==='signup' && result.data.user){await supabase.from('profiles').upsert({id:result.data.user.id,display_name:name||email.split('@')[0]});setMsg('Account created. Check your email if confirmation is enabled.')}
    else onReady(result.data.user)
  }
  return <div className="auth"><div className="auth-card"><div className="brand">♞ CHESS ARENA</div><h1>{mode==='login'?'Log in':'Create account'}</h1><p className="muted">Your display name is used in online games.</p>
    <form onSubmit={submit}>{mode==='signup'&&<input placeholder="Display name" value={name} onChange={e=>setName(e.target.value)} required/>}<input type="email" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} required/><input type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)} minLength="6" required/><button className="primary">{mode==='login'?'Log in':'Create account'}</button></form>
    {msg&&<div className="notice">{msg}</div>}<button className="link" onClick={()=>setMode(mode==='login'?'signup':'login')}>{mode==='login'?'Create a new account':'I already have an account'}</button>
  </div></div>
}

function App(){
  const [session,setSession]=useState(null),[profile,setProfile]=useState(null),[screen,setScreen]=useState('home'),[gameId,setGameId]=useState(null),[games,setGames]=useState([]),[game,setGame]=useState(null),[error,setError]=useState(''),[refresh,setRefresh]=useState(0)
  useEffect(()=>{if(!supabase)return;supabase.auth.getSession().then(({data})=>setSession(data.session));const {data}=supabase.auth.onAuthStateChange((_e,s)=>setSession(s));return()=>data.subscription.unsubscribe()},[])
  useEffect(()=>{if(!session||!supabase)return;supabase.from('profiles').select('*').eq('id',session.user.id).maybeSingle().then(({data})=>setProfile(data));loadGames()},[session,refresh])
  async function loadGames(){const {data}=await supabase.from('games').select('*').or(`white_id.eq.${session.user.id},black_id.eq.${session.user.id}`).order('created_at',{ascending:false}).limit(20);if(data)setGames(data)}
  if(!session)return <Auth onReady={u=>setSession({user:u})}/>;
  if(screen==='game'&&gameId)return <OnlineGame id={gameId} session={session} profile={profile} onBack={()=>{setScreen('home');setGameId(null);setRefresh(x=>x+1)}}/>
  return <Home session={session} profile={profile} games={games} onOpen={id=>{setGameId(id);setScreen('game')}} onCreated={id=>{setGameId(id);setScreen('game')}} />
}

function Home({session,profile,games,onOpen,onCreated}){
 const [code,setCode]=useState(''),[side,setSide]=useState('random'),[msg,setMsg]=useState('')
 const create=async()=>{const {data,error}=await supabase.from('games').insert({white_id:side==='black'?null:session.user.id,black_id:side==='white'?null:session.user.id,status:'waiting',fen:new Chess().fen(),moves:[]}).select().single();if(error)setMsg(error.message);else onCreated(data.id)}
 const join=async()=>{if(!code.trim())return;const {data,error}=await supabase.from('games').select('*').eq('id',code.trim()).single();if(error){setMsg('Game not found.');return}const update=data.white_id?{black_id:session.user.id,status:'active'}:{white_id:session.user.id,status:'active'};const r=await supabase.from('games').update(update).eq('id',data.id);if(r.error)setMsg(r.error.message);else onCreated(data.id)}
 return <div className="shell"><header><div className="brand">♞ CHESS ARENA ONLINE</div><div>{profile?.display_name||session.user.email} <button className="small" onClick={()=>supabase.auth.signOut()}>Log out</button></div></header><main className="home"><section className="hero"><h1>Play chess online.</h1><p>Create a game, share the game code, and play live against another person.</p><div className="cards"><div className="card"><h3>New game</h3><select value={side} onChange={e=>setSide(e.target.value)}><option value="random">Random side</option><option value="white">Play White</option><option value="black">Play Black</option></select><button className="primary" onClick={create}>Create online game</button></div><div className="card"><h3>Join game</h3><input placeholder="Paste game ID" value={code} onChange={e=>setCode(e.target.value)}/><button className="primary" onClick={join}>Join game</button></div></div>{msg&&<div className="notice">{msg}</div>}</section><section><h2>Your games</h2><div className="game-list">{games.map(g=><button key={g.id} className="game-row" onClick={()=>onOpen(g.id)}><span>{g.id}</span><span>{g.status}</span><span>{new Date(g.created_at).toLocaleString()}</span></button>)}{!games.length&&<p className="muted">No saved games yet.</p>}</div></section></main></div>
}

function OnlineGame({id,session,profile,onBack}){
 const [row,setRow]=useState(null),[chess,setChess]=useState(()=>new Chess()),[selected,setSelected]=useState(null),[msg,setMsg]=useState(''),[review,setReview]=useState([])
 const color=useMemo(()=>row?(row.white_id===session.user.id?'w':'b'):null,[row,session.user.id])
 useEffect(()=>{let channel;async function load(){const {data,error}=await supabase.from('games').select('*').eq('id',id).single();if(error){setMsg(error.message);return}setRow(data);const c=new Chess(data.fen);setChess(c);setReview(data.moves||[]);channel=supabase.channel(`game:${id}`,{config:{private:false}}).on('broadcast',{event:'move'},({payload})=>{const c2=new Chess(payload.fen);setChess(c2);setRow(r=>({...r,fen:payload.fen,moves:payload.moves,status:payload.status}));setReview(payload.moves||[])}).subscribe()}load();return()=>{if(channel)supabase.removeChannel(channel)}},[id])
 const play=async(square)=>{if(!row||row.status!=='active')return;if((color==='w') !== (chess.turn()==='w'))return;const piece=chess.get(square);if(!selected){if(piece&&piece.color===chess.turn()&&piece.color===color)setSelected(square);return}let c=new Chess(chess.fen());let move;try{move=c.move({from:selected,to:square,promotion:'q'})}catch{setSelected(piece&&piece.color===color?square:null);return}const cls=classify(chess,move), item={ply:(row.moves?.length||0)+1,san:move.san,uci:selected+square,label:cls,at:new Date().toISOString()};const moves=[...(row.moves||[]),item];const nextStatus=c.isGameOver()?'finished':'active';const {data,error}=await supabase.from('games').update({fen:c.fen(),moves,status:nextStatus,updated_at:new Date().toISOString()}).eq('id',id).select().single();if(error){setMsg(error.message);return}setChess(c);setRow(data);setReview(moves);setSelected(null);await supabase.channel(`game:${id}`).send({type:'broadcast',event:'move',payload:{fen:c.fen(),moves,status:nextStatus}})}
 const squares=[];for(let r=7;r>=0;r--)for(let f=0;f<8;f++)squares.push(String.fromCharCode(97+f)+(r+1))
 return <div className="review-shell"><header><button className="back" onClick={onBack}>←</button><div className="brand">♞ GAME REVIEW / ONLINE</div><div className="pill">{profile?.display_name||'Player'} · {color==='w'?'White':'Black'}</div></header><div className="game-layout"><div><div className="board">{squares.map(s=>{const p=chess.get(s);const dark=((s.charCodeAt(0)-97)+(Number(s[1])-1))%2===1;return <button key={s} className={`sq ${dark?'dark':'light'} ${selected===s?'sel':''}`} onClick={()=>play(s)}>{p&&<span className={`piece ${p.color}`}>{PIECES[p.color][p.type]}</span>}</button>})}</div><div className="share">Game ID: <b>{id}</b><button className="small" onClick={()=>navigator.clipboard?.writeText(id)}>Copy</button></div>{msg&&<div className="notice">{msg}</div>}</div><aside className="review-panel"><div className="review-top"><span>◉ Game Review</span><span>⌕</span></div><div className="last-card">{review.length?<><span className="class-icon" style={{background:CLASS_INFO[review[review.length-1].label].color}}>{CLASS_INFO[review[review.length-1].label].icon}</span><b>{review[review.length-1].san} is the last {review[review.length-1].label.toLowerCase()}</b></>:<b>Make the first move</b>}<span className="eval">0.33</span></div><button className="next">Next</button><div className="moves">{review.map((m,i)=>{const inf=CLASS_INFO[m.label]||CLASS_INFO['GOOD MOVE'];return <div className="move-row" key={i}><span>{i+1}.</span><span>{m.san}</span><span className="mini-icon" style={{background:inf.color}}>{inf.icon}</span><span className="label">{m.label}</span></div>})}</div><div className="graph"><div className="line"></div><div className="dots">{review.map((m,i)=><i key={i} style={{left:`${Math.min(98,(i+1)/Math.max(1,review.length)*100)}%`}}></i>)}</div></div><div className="nav"><button>⏮</button><button>‹</button><button>▶</button><button>›</button><button>⏭</button></div></aside></div></div>
}

createRoot(document.getElementById('root')).render(<App/>)
