// Asynchronous browser engine adapter.
// Uses the bundled Arena search inside a Web Worker, so bot thinking never
// blocks the React/UI thread. A Stockfish worker can be plugged in later.
let worker = null
let nextId = 0
const pending = new Map()

function ensureWorker() {
  if (worker) return worker
  worker = new Worker(new URL('./botWorker.js', import.meta.url), { type: 'module' })
  worker.onmessage = (event) => {
    const { id, ok, result, error } = event.data || {}
    const job = pending.get(id)
    if (!job) return
    pending.delete(id)
    if (ok) job.resolve({
      bestmove: result?.uci || '(none)',
      cp: result?.score ?? 0,
      mate: null,
      san: result?.san || ''
    })
    else job.reject(new Error(error || 'Bot search failed'))
  }
  worker.onerror = (event) => {
    const error = new Error(event.message || 'Bot worker failed')
    for (const job of pending.values()) job.reject(error)
    pending.clear()
    worker?.terminate()
    worker = null
  }
  return worker
}

export async function analyzeFen(fen, { depth = 3, timeout = 9000 } = {}) {
  const w = ensureWorker()
  const id = ++nextId
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      const job = pending.get(id)
      if (!job) return
      pending.delete(id)
      reject(new Error('Bot search timed out'))
    }, timeout)
    pending.set(id, {
      resolve: value => { clearTimeout(timer); resolve(value) },
      reject: error => { clearTimeout(timer); reject(error) }
    })
    w.postMessage({ id, fen, depth: Math.max(1, Math.min(4, depth)) })
  })
}

export function terminateStockfish() {
  if (worker) worker.terminate()
  worker = null
  for (const job of pending.values()) job.reject(new Error('Engine terminated'))
  pending.clear()
}
