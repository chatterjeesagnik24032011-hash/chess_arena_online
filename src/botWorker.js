import { getBestMove } from './engine.js'

self.onmessage = (event) => {
  const { id, fen, depth } = event.data || {}
  try {
    const result = getBestMove(fen, depth)
    self.postMessage({ id, ok: true, result })
  } catch (error) {
    self.postMessage({ id, ok: false, error: error?.message || 'Bot search failed' })
  }
}
