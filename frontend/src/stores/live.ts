import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * A signal from `/api/events` that something changed: `topic` names the kind
 * ("request", "issue", "asset", "license", "consumable", "order"), `id` the
 * object. Topic "*" asks to reload everything, e.g. after a lost connection.
 */
export type LiveEvent = { topic: string; id: string | null }
type Listener = (event: LiveEvent) => void

const RELOAD_ALL: LiveEvent = { topic: '*', id: null }

/**
 * The live update stream of the signed-in user. Without it (no PostgreSQL on
 * the server, or the connection is down) `connected` is false and pages
 * refresh as before.
 */
export const useLiveStore = defineStore('live', () => {
  const connected = ref(false)
  const listeners = new Set<Listener>()
  let source: EventSource | null = null
  // Whether signals may have been missed since the stream was last open.
  let gap = false
  // The server ends each stream after a while and says so; that reconnect misses nothing.
  let planned = false

  function emit(event: LiveEvent) {
    listeners.forEach((listener) => listener(event))
  }

  function start() {
    if (source) return
    source = new EventSource('/api/events')
    source.onopen = () => {
      connected.value = true
      if (gap) emit(RELOAD_ALL)
      gap = false
    }
    source.onmessage = (message) => {
      let event: LiveEvent
      try {
        event = JSON.parse(message.data) as LiveEvent
      } catch {
        return // a garbled frame: skip it, the next signal comes through
      }
      emit(event)
    }
    source.addEventListener('bye', () => (planned = true))
    source.onerror = () => {
      if (connected.value && !planned) gap = true
      planned = false
      connected.value = false
      // A closed source (e.g. 204: no live updates on this server) is not retried.
      if (source?.readyState === EventSource.CLOSED) source = null
    }
  }

  function stop() {
    source?.close()
    source = null
    connected.value = false
    gap = false
  }

  function subscribe(listener: Listener): () => void {
    listeners.add(listener)
    return () => listeners.delete(listener)
  }

  return { connected, start, stop, subscribe }
})
