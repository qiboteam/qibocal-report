import { nextTick, watch } from 'vue'

export function useMagneticFollow({ protocols, live, container, lastCard }) {
  let revision = 0
  watch(live, () => { revision++ }, { flush: 'sync' })

  watch(
    () => protocols().map(protocol => protocol.id),
    async (ids, previousIds, onCleanup) => {
      const currentRevision = ++revision
      onCleanup(() => { revision++ })
      const lastId = ids.at(-1)
      const element = container.value
      if (!live() || !element || element.clientHeight <= 0 || lastId === undefined || previousIds.includes(lastId)) return

      // Measure the old layout before Vue appends the new protocols.
      if (lastCard) {
        const card = lastCard()
        if (!card) return
        const viewportTop = element.getBoundingClientRect().top + element.clientTop
        const bounds = card.getBoundingClientRect()
        if (bounds.bottom <= viewportTop || bounds.top >= viewportTop + element.clientHeight) return
      } else if (element.scrollHeight - element.scrollTop - element.clientHeight > 1) {
        return
      }

      await nextTick()
      if (revision !== currentRevision || !live() || container.value !== element) return
      if (lastCard) {
        const card = lastCard()
        if (card) {
          const viewportTop = element.getBoundingClientRect().top + element.clientTop
          element.scrollTop += card.getBoundingClientRect().top - viewportTop
        }
      } else {
        element.scrollTop = element.scrollHeight
      }
    }
  )
}
