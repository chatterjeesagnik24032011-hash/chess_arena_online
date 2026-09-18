// Browser Stockfish adapter with a small FIFO queue so bot thinking and
// evaluation analysis never fight over the same worker.
let worker = null
let readyPromise = null
let queue = []
let active = null
let jobId = 0

function ensure() {
  if (worker) return readyPromise
  worker = new Worker('/stockfish/stockfish-19-lite-single.js')
  readyPromise = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Stockfish failed to start')), 12000)
    const onMessage = e => {
      const line = typeof e.data === 'string' ? e.data : ''
      if (line === 'uciok') {
        clearTimeout(timeout)
        worker.removeEventListener('message', onMessage)
        resolve()
      }
    }
    worker.addEventListener('message', onMessage)
    worker.postMessage('uci')
  })
  worker.addEventListener('message', onWorkerMessage)
  return readyPromise
}

function onWorkerMessage(e) {
  const line = typeof e.data === 'string' ? e.data : ''
  if (!active) return
  if (line.startsWith('info ') && line.includes(' score ')) {
    const mate = line.match(/score mate (-?\d+)/)
    const cp = line.match(/score cp (-?\d+)/)
    if (mate) active.info = { cp: Number(mate[1]) * 10000, mate: Number(mate[1]) }
    else if (cp) active.info = { cp: Number(cp[1]), mate: null }
  }
  const match = line.match(/^bestmove\s+(\S+)/)
  if (match) {
    const job = active
    active = null
    job.resolve({ bestmove: match[1], cp: job.info.cp, mate: job.info.mate })
    pump()
  }
}

async function pump() {
  if (active || queue.length === 0) return
  await ensure()
  const job = queue.shift()
  active = { ...job, info: { cp: 0, mate: null } }
  worker.postMessage('setoption name MultiPV value 1')
  worker.postMessage('position fen ' + job.fen)
  worker.postMessage('go depth ' + job.depth)
}

export async function analyzeFen(fen, { depth = 10 } = {}) {
  await ensure()
  return new Promise((resolve, reject) => {
    queue.push({ id: ++jobId, fen, depth: Math.max(1, Math.min(18, depth)), resolve, reject })
    pump()
  })
}

export function terminateStockfish() {
  if (worker) worker.terminate()
  worker = null
  readyPromise = null
  active = null
  queue.splice(0).forEach(job => job.reject?.(new Error('Stockfish terminated')))
}
