import React,{useEffect,useMemo,useRef,useState} from 'react'
import {createRoot} from 'react-dom/client'
import {Chess} from 'chess.js'
import {supabase} from './supabase'
import {classifyMove} from './engine'
import {analyzeFen} from './stockfish'
import './styles.css'

const PIECES={w:{p:'♙',n:'♘',b:'♗',r:'♖',q:'♕',k:'♔'},b:{p:'♟',n:'♞',b:'♝',r:'♜',q:'♛',k:'♚'}}
const INFO={
 'BOOK MOVE':{icon:'▣',tone:'book'},'BEST MOVE':{icon:'✓',tone:'best'},'BRILLIANT MOVE':{icon:'!!',tone:'brilliant'},'GREAT MOVE':{icon:'!',tone:'great'},'EXCELLENT MOVE':{icon:'★',tone:'excellent'},'GOOD MOVE':{icon:'•',tone:'good'},'INACCURACY':{icon:'?!',tone:'inaccuracy'},'MISTAKE':{icon:'?',tone:'mistake'},'BLUNDER':{icon:'??',tone:'blunder'}
}
const BOT={beginner:{name:'Beginner Bot',depth:1},intermediate:{name:'Intermediate Bot',depth:2},pro:{name:'Pro Bot',depth:3}}

function fmtTime(ms){const s=Math.max(0,Math.ceil(ms/1000));return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`}
function initialClock(minutes=10,increment=0){return {w:minutes*60*1000,b:minutes*60*1000,increment}}
function scoreLabel(cp){if(Math.abs(cp)>29000)return cp>0?'MATE':'-MATE';return `${cp>=0?'+':''}${(cp/100).toFixed(2)}`}

function Auth({onDone}){
 const [mode,setMode]=useState('login'),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[name,setName]=useState(''),[msg,setMsg]=useState('')
 const submit=async e=>{e.preventDefault();setMsg('');if(!supabase){setMsg('Supabase is not configured in Vercel.');return}
  const r=mode==='login'?await supabase.auth.signInWithPassword({email,password}):await supabase.auth.signUp({email,password,options:{data:{display_name:name}}})
  if(r.error){setMsg(r.error.message);return}
  if(mode==='signup'&&r.data.user){await supabase.from('profiles').upsert({id:r.data.user.id,display_name:name||email.split('@')[0]});setMsg('Account created. If email confirmation is enabled, confirm your email, then log in.')}else onDone(r.data.session)
 }
 return <div className="auth"><div className="auth-card"><div className="brand">♞ CHESS ARENA</div><h1>{mode==='login'?'Welcome back':'Create your account'}</h1><p className="muted">Online multiplayer, bots and game review in one board.</p><form onSubmit={submit}>{mode==='signup'&&<input value={name} onChange={e=>setName(e.target.value)} placeholder="Display name" required/>}<input value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" type="email" required/><input value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" type="password" minLength="6" required/><button className="primary">{mode==='login'?'Log in':'Create account'}</button></form>{msg&&<div className="notice">{msg}</div>}<button className="link" onClick={()=>setMode(mode==='login'?'signup':'login')}>{mode==='login'?'Create a new account':'I already have an account'}</button></div></div>
}

function App(){
 const [session,setSession]=useState(null),[profile,setProfile]=useState(null),[screen,setScreen]=useState('home'),[mode,setMode]=useState(null),[botClock,setBotClock]=useState({minutes:10,increment:0}),[gameId,setGameId]=useState(null)
 useEffect(()=>{if(!supabase)return;supabase.auth.getSession().then(({data})=>setSession(data.session));const {data}=supabase.auth.onAuthStateChange((_e,s)=>setSession(s));return()=>data.subscription.unsubscribe()},[])
 useEffect(()=>{if(!session||!supabase)return;supabase.from('profiles').select('*').eq('id',session.user.id).maybeSingle().then(({data})=>setProfile(data))},[session])
 if(!supabase)return <div className="auth"><div className="auth-card"><div className="brand">♞ CHESS ARENA</div><h1>Setup required</h1><p>Add <b>VITE_SUPABASE_URL</b> and <b>VITE_SUPABASE_PUBLISHABLE_KEY</b> to Vercel, then redeploy.</p></div></div>
 if(!session)return <Auth onDone={setSession}/>
 if(screen==='online')return <OnlineGame id={gameId} session={session} profile={profile} onBack={()=>{setScreen('home');setGameId(null)}}/>
 if(screen==='bot')return <BotGame level={mode||'beginner'} profile={profile} timeControl={botClock} onBack={()=>{setScreen('home');setMode(null)}}/>
 return <Home session={session} profile={profile} onOpenOnline={id=>{setGameId(id);setScreen('online')}} onPlayBot={(l,t)=>{setMode(l);setBotClock(t);setScreen('bot')}}/>
}

function Home({session,profile,onOpenOnline,onPlayBot}){
 const [tab,setTab]=useState('play'),[code,setCode]=useState(''),[side,setSide]=useState('random'),[botTime,setBotTime]=useState('10+0'),[onlineTime,setOnlineTime]=useState('10+0'),[msg,setMsg]=useState(''),[games,setGames]=useState([])
 const parseTC=v=>{const [m,i]=v.split('+').map(Number);return {minutes:m,increment:i*1000}}
 const load=async()=>{const {data}=await supabase.from('games').select('*').or(`white_id.eq.${session.user.id},black_id.eq.${session.user.id}`).order('updated_at',{ascending:false}).limit(20);if(data)setGames(data)}
 useEffect(()=>{load()},[])
 const create=async()=>{setMsg('');const tc=parseTC(onlineTime);const white=side==='random'?(Math.random()>.5?session.user.id:null):side==='white'?session.user.id:null;const black=side==='black'?session.user.id:null;const r=await supabase.from('games').insert({white_id:white,black_id:black,status:'waiting',fen:new Chess().fen(),moves:[],white_time:tc.minutes*60000,black_time:tc.minutes*60000,increment:tc.increment}).select().single();if(r.error)setMsg(r.error.message);else onOpenOnline(r.data.id)}
 const join=async()=>{const id=code.trim();if(!id)return;setMsg('');const r=await supabase.from('games').select('*').eq('id',id).single();if(r.error){setMsg('Game not found.');return}if(r.data.white_id===session.user.id||r.data.black_id===session.user.id){onOpenOnline(id);return}if(r.data.white_id&&r.data.black_id){setMsg('That game already has two players.');return}const patch=r.data.white_id?{black_id:session.user.id,status:'active'}:{white_id:session.user.id,status:'active'};const u=await supabase.from('games').update(patch).eq('id',id);if(u.error)setMsg(u.error.message);else onOpenOnline(id)}
 const randomMatch=async()=>{setMsg('');const tc=parseTC(onlineTime);const r=await supabase.rpc('find_or_join_random_game',{p_minutes:tc.minutes,p_increment:Math.round(tc.increment)});if(r.error){setMsg(r.error.message||'Could not join random matchmaking.');return}const result=Array.isArray(r.data)?r.data[0]:r.data;if(!result?.game_id){setMsg('No matchmaking room was returned.');return}onOpenOnline(result.game_id)}
 return <div className="app"><header className="topbar"><div className="brand">♞ CHESS ARENA</div><nav><button className={tab==='play'?'active':''} onClick={()=>setTab('play')}>Play</button><button className={tab==='history'?'active':''} onClick={()=>setTab('history')}>History</button></nav><div className="user">{profile?.display_name||session.user.email}<button className="ghost" onClick={()=>supabase.auth.signOut()}>Log out</button></div></header>{tab==='play'?<main className="dashboard"><section className="hero"><div><div className="eyebrow">ONLINE CHESS ARENA</div><h1>Play chess your way.</h1><p>Challenge another player online or train against three bot levels.</p></div><div className="hero-badge">10+0<br/><span>standard</span></div></section><section className="mode-grid"><div className="mode-card online-card"><div className="card-icon">♟</div><h2>Play Online</h2><p>Create a room, choose your side, or get matched with a random player worldwide.</p><div className="time-row"><label>Time control</label><select value={onlineTime} onChange={e=>setOnlineTime(e.target.value)}><option value="1+0">1+0</option><option value="3+0">3+0</option><option value="5+0">5+0</option><option value="10+0">10+0</option><option value="15+10">15+10</option><option value="30+0">30+0</option></select></div><button className="random-match" onClick={randomMatch}>🌎 Join Random Player</button><div className="random-note">Worldwide matchmaking • first available opponent • colors assigned automatically</div><div className="row"><select value={side} onChange={e=>setSide(e.target.value)}><option value="random">Random side</option><option value="white">Play White</option><option value="black">Play Black</option></select><button className="primary" onClick={create}>Create private game</button></div><div className="join"><input value={code} onChange={e=>setCode(e.target.value)} placeholder="Game ID"/><button className="secondary" onClick={join}>Join</button></div></div><div className="mode-card"><div className="card-icon">♛</div><h2>Play vs Bot</h2><p>Use the same board, clock and review tools as your Python version.</p><div className="time-row"><label>Time control</label><select value={botTime} onChange={e=>setBotTime(e.target.value)}><option value="1+0">1+0</option><option value="3+0">3+0</option><option value="5+0">5+0</option><option value="10+0">10+0</option><option value="15+10">15+10</option><option value="30+0">30+0</option></select></div><div className="bot-grid">{Object.entries(BOT).map(([k,b])=><button key={k} onClick={()=>{const t=parseTC(botTime);onPlayBot(k,t)}}><b>{b.name}</b><span>{k==='beginner'?'Easy':k==='intermediate'?'Medium':'Strong'}</span></button>)}</div></div></section>{msg&&<div className="notice">{msg}</div>}</main>:<main className="dashboard"><section className="panel"><h2>Game history</h2>{games.length?games.map(g=><button className="history-row" key={g.id} onClick={()=>onOpenOnline(g.id)}><span>{g.id.slice(0,8)}…</span><span>{g.status}</span><span>{new Date(g.updated_at).toLocaleString()}</span></button>):<p className="muted">No online games yet.</p>}</section></main>}</div>
}

function Board({chess,orientation='w',selected,onSquare,onMove,legalTargets=[],lastMove,engineCp=0}){
 const files=orientation==='w'?'abcdefgh':'hgfedcba',ranks=orientation==='w'?'87654321':'12345678'
 return <div className="board-wrap"><div className="eval-side"><div className="eval-black" style={{height:`${Math.max(4,Math.min(96,50-(engineCp/1200)*50))}%`}}></div><div className="eval-white"></div><span>{scoreLabel(engineCp)}</span></div><div className="board">{ranks.split('').flatMap(rank=>files.split('').map(file=>{const s=file+rank,p=chess.get(s),dark=((file.charCodeAt(0)-97)+(Number(rank)-1))%2===1;const target=legalTargets.includes(s);const last=lastMove&&(lastMove.from===s||lastMove.to===s);return <button key={s} className={`sq ${dark?'dark':'light'} ${selected===s?'sel':''} ${target?'target':''} ${last?'last':''}`} onClick={()=>onSquare(s)}>{p&&<span className={`piece ${p.color}`}>{PIECES[p.color][p.type]}</span>}{target&&<i className="dot"/>}<small>{file==='a'&&<em>{rank}</em>}{rank==='1'&&<em>{file}</em>}</small></button>}))}</div></div>
}

function ReviewPanel({items,onJump,current}){
 const counts=Object.fromEntries(Object.keys(INFO).map(k=>[k,items.filter(x=>x.label===k).length]));const avg=items.length?items.reduce((a,x)=>a+(x.loss||0),0)/items.length:0;const accuracy=Math.max(0,Math.min(100,100-avg/10));
 return <aside className="panel review-panel"><div className="panel-title"><span>GAME REVIEW</span><span className="live-dot">● LIVE</span></div><div className="review-summary"><div><b>{accuracy.toFixed(1)}%</b><span>Accuracy</span></div><div><b>{avg.toFixed(0)}</b><span>Avg loss</span></div><div><b>{items.length}</b><span>Moves</span></div></div><div className="review-list">{items.length?items.map((m,i)=>{const info=INFO[m.label]||INFO['GOOD MOVE'];return <button key={i} className={`review-row ${current===i?'current':''}`} onClick={()=>onJump(i)}><span className="num">{i+1}.</span><b>{m.san}</b><span className={`badge ${info.tone}`}>{info.icon}</span><span className="label">{m.label}</span></button>}):<div className="empty-review">Make the first move to start the review.</div>}</div><div className="review-chart">{items.map((m,i)=><div key={i} className={`chart-bar ${INFO[m.label]?.tone||'good'}`} style={{height:`${Math.min(90,8+(m.loss||0)/6)}%`}} title={`${m.label}: ${Math.round(m.loss||0)} cp`}></div>)}</div><div className="counts">{Object.entries(counts).filter(([,n])=>n).map(([k,n])=><span key={k}>{INFO[k].icon} {n}</span>)}</div></aside>
}

function Clock({clock,turn,paused}){return <div className="clocks"><div className={`clock ${turn==='b'?'active-clock':''}`}><span>BLACK</span><b>{fmtTime(clock.b)}</b></div><div className={`clock ${turn==='w'?'active-clock':''}`}><span>WHITE</span><b>{fmtTime(clock.w)}</b></div>{paused&&<span className="paused">PAUSED</span>}</div>}

function BotGame({level,profile,timeControl={minutes:10,increment:0},onBack}){
 const [chess,setChess]=useState(()=>new Chess()),[selected,setSelected]=useState(null),[targets,setTargets]=useState([]),[items,setItems]=useState([]),[current,setCurrent]=useState(-1),[clock,setClock]=useState(initialClock(timeControl.minutes,timeControl.increment)),[orientation,setOrientation]=useState('w'),[status,setStatus]=useState('active'),[thinking,setThinking]=useState(false),[lastMove,setLastMove]=useState(null),[engineCp,setEngineCp]=useState(0),[stockfishReady,setStockfishReady]=useState(false)
 const botColor='b'
 useEffect(()=>{let cancelled=false;analyzeFen(chess.fen(),{depth:3}).then(r=>{if(!cancelled){setEngineCp(r.cp);setStockfishReady(true)}}).catch(()=>{});return()=>{cancelled=true}},[chess])
 useEffect(()=>{
  if(status!=='active'||chess.turn()!==botColor||thinking)return
  let cancelled=false
  setThinking(true)
  const depth=level==='beginner'?2:level==='intermediate'?3:4
  const delay=level==='beginner'?250:level==='intermediate'?450:700
  const timer=setTimeout(async()=>{
    try{
      const result=await analyzeFen(chess.fen(),{depth,timeout:7000})
      if(!cancelled && result?.bestmove && result.bestmove!=='(none)') commit(result.bestmove,true)
      else if(!cancelled) { const moves=chess.moves({verbose:true}); if(moves[0]) commit(moves[0].from+moves[0].to+(moves[0].promotion||''),true) }
    }catch(e){
      if(!cancelled){
        console.error('Bot engine error',e)
        const moves=chess.moves({verbose:true})
        if(moves[0]) commit(moves[0].from+moves[0].to+(moves[0].promotion||''),true)
      }
    }finally{
      if(!cancelled)setThinking(false)
    }
  },delay)
  return()=>{cancelled=true;clearTimeout(timer)}
 },[chess,level,status,thinking])
 useEffect(()=>{if(status!=='active')return;const t=setInterval(()=>setClock(c=>{const next={...c};next[chess.turn()]=Math.max(0,next[chess.turn()]-250);if(next[chess.turn()]<=0)setStatus(chess.turn()==='w'?'black-won-on-time':'white-won-on-time');return next}),250);return()=>clearInterval(t)},[chess,status])
 function commit(uci,isBot=false){const c=new Chess(chess.fen());let mv;try{mv=c.move({from:uci.slice(0,2),to:uci.slice(2,4),promotion:uci.slice(4)||'q'})}catch{return}const before=chess.fen();const mover=chess.turn();const nextClock={...clock,[mover]:clock[mover]+(timeControl.increment||0)};const analysis=isBot?{label:'BEST MOVE',loss:0,rank:1,bestMove:uci}:{...classifyMove(before,uci,mv.san,1)};const item={ply:items.length+1,san:mv.san,uci,label:analysis.label,loss:analysis.loss,rank:analysis.rank,bestMove:analysis.bestMove,at:Date.now(),by:isBot?'bot':'human'};setItems(x=>[...x,item]);setCurrent(items.length);setClock(nextClock);setLastMove({from:uci.slice(0,2),to:uci.slice(2,4)});setChess(c);setSelected(null);setTargets([]);if(c.isGameOver())setStatus(c.isCheckmate()?(c.turn()==='w'?'black-won':'white-won'):'draw')}
 function square(s){if(status!=='active'||thinking&&chess.turn()==='b'||chess.turn()!=='w')return;const p=chess.get(s);if(!selected){if(p?.color==='w'){setSelected(s);setTargets(chess.moves({square:s,verbose:true}).map(m=>m.to))}return}if(selected===s){setSelected(null);setTargets([]);return}const move=chess.moves({square:selected,verbose:true}).find(m=>m.to===s);if(!move){if(p?.color==='w'){setSelected(s);setTargets(chess.moves({square:s,verbose:true}).map(m=>m.to))}return}commit(selected+s+(move.promotion||''))}
 return <GameFrame title={`VS ${BOT[level].name.toUpperCase()}`} profile={profile} onBack={onBack} clocks={<Clock clock={clock} turn={chess.turn()} />} board={<Board chess={chess} orientation={orientation} selected={selected} legalTargets={targets} lastMove={lastMove} engineCp={engineCp} onSquare={square}/>} leftTools={<><button onClick={()=>setOrientation(o=>o==='w'?'b':'w')}>Flip board</button><button onClick={()=>{setChess(new Chess());setItems([]);setClock(initialClock(timeControl.minutes,timeControl.increment));setStatus('active');setLastMove(null);setThinking(false)}}>New game</button></>} right={<><div className="engine-card"><span>ENGINE</span><b>{thinking?'Thinking…':scoreLabel(engineCp)}</b><small>Arena Engine · bot depth {level==='beginner'?2:level==='intermediate'?3:4}</small></div><ReviewPanel items={items} current={current} onJump={i=>setCurrent(i)}/></>} status={status}/>
}

function GameFrame({title,profile,onBack,clocks,board,leftTools,right,status}){return <div className="game-page"><header className="topbar gamebar"><button className="back" onClick={onBack}>←</button><div className="brand">♞ CHESS ARENA <span>/ {title}</span></div><div className="game-user">{profile?.display_name||'Player'}</div></header><main className="game-main"><section className="board-column">{clocks}{board}<div className="toolbar">{leftTools}</div><div className="status-line">{status==='active'?'Your move':status.replaceAll('-',' ')}</div></section><section className="side-column">{right}</section></main></div>}

function OnlineGame({id,session,profile,onBack}){
 const [row,setRow]=useState(null),[chess,setChess]=useState(()=>new Chess()),[selected,setSelected]=useState(null),[targets,setTargets]=useState([]),[items,setItems]=useState([]),[orientation,setOrientation]=useState('w'),[clock,setClock]=useState(initialClock()),[msg,setMsg]=useState(''),[lastMove,setLastMove]=useState(null),[engineCp,setEngineCp]=useState(0),[stockfishReady,setStockfishReady]=useState(false)
 const channelRef=useRef(null)
 const color=useMemo(()=>row?(row.white_id===session.user.id?'w':row.black_id===session.user.id?'b':null):null,[row,session.user.id])
 useEffect(()=>{let alive=true;async function load(){const r=await supabase.from('games').select('*').eq('id',id).single();if(r.error){setMsg(r.error.message);return}if(!alive)return;setRow(r.data);setChess(new Chess(r.data.fen));setItems(r.data.moves||[]);setClock({w:r.data.white_time??600000,b:r.data.black_time??600000});if(r.data.moves?.length){const last=r.data.moves[r.data.moves.length-1];setLastMove({from:last.uci?.slice(0,2),to:last.uci?.slice(2,4)})}channelRef.current=supabase.channel(`game-${id}`).on('postgres_changes',{event:'UPDATE',schema:'public',table:'games',filter:`id=eq.${id}`},payload=>sync(payload.new)).subscribe()}load();return()=>{alive=false;if(channelRef.current)supabase.removeChannel(channelRef.current)}},[id])
 function sync(next){setRow(next);setChess(new Chess(next.fen));setItems(next.moves||[]);setClock({w:next.white_time??600000,b:next.black_time??600000});const m=(next.moves||[]).at(-1);if(m)setLastMove({from:m.uci?.slice(0,2),to:m.uci?.slice(2,4)})}
 useEffect(()=>{let cancelled=false;analyzeFen(chess.fen(),{depth:3}).then(r=>{if(!cancelled){setEngineCp(r.cp);setStockfishReady(true)}}).catch(()=>{});return()=>{cancelled=true}},[chess])
 useEffect(()=>{if(!row||row.status!=='active')return;const t=setInterval(()=>setClock(c=>{const n={...c};n[chess.turn()]=Math.max(0,n[chess.turn()]-250);return n}),250);return()=>clearInterval(t)},[row,chess])
 async function play(s){if(!row||row.status!=='active'||!color||chess.turn()!==color)return;const p=chess.get(s);if(!selected){if(p?.color===color){setSelected(s);setTargets(chess.moves({square:s,verbose:true}).map(m=>m.to))}return}if(selected===s){setSelected(null);setTargets([]);return}const move=chess.moves({square:selected,verbose:true}).find(m=>m.to===s);if(!move){if(p?.color===color){setSelected(s);setTargets(chess.moves({square:s,verbose:true}).map(m=>m.to))}return}const c=new Chess(chess.fen());const mv=c.move({from:selected,to:s,promotion:move.promotion||'q'});const uci=selected+s+(move.promotion||'');const analysis=classifyMove(chess.fen(),uci,mv.san,2);const nextMoves=[...(row.moves||[]),{ply:(row.moves||[]).length+1,san:mv.san,uci,label:analysis.label,loss:analysis.loss,rank:analysis.rank,bestMove:analysis.bestMove,at:Date.now(),by:color}];const nextStatus=c.isGameOver()?'finished':(row.white_id&&row.black_id?'active':'waiting');const patch={fen:c.fen(),moves:nextMoves,status:nextStatus,white_time:clock.w,black_time:clock.b,updated_at:new Date().toISOString()};const r=await supabase.from('games').update(patch).eq('id',id);if(r.error){setMsg(r.error.message);return}setSelected(null);setTargets([]);setLastMove({from:selected,to:s});setChess(c);setItems(nextMoves);setRow(x=>({...x,...patch}))}
 const gameStatus=row?.status==='waiting'?'Waiting for opponent…':row?.status==='finished'?'Game finished':color?`${color==='w'?'White':'Black'} to move`:'Spectator'
 return <GameFrame title="ONLINE" profile={profile} onBack={onBack} clocks={<Clock clock={clock} turn={chess.turn()}/>} board={<Board chess={chess} orientation={orientation} selected={selected} legalTargets={targets} lastMove={lastMove} engineCp={engineCp} onSquare={play}/>} leftTools={<><button onClick={()=>setOrientation(o=>o==='w'?'b':'w')}>Flip board</button><button onClick={()=>navigator.clipboard?.writeText(id)}>Copy Game ID</button></>} right={<><div className="online-info"><b>{gameStatus}</b><span>{id}</span><small>{stockfishReady?'Stockfish 19 Lite analysis active':'Loading engine analysis…'}</small></div><ReviewPanel items={items} current={items.length-1} onJump={()=>{}}/></>} status={gameStatus}/>
}

createRoot(document.getElementById('root')).render(<App/>)
