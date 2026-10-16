/**
 * The keys of one page: `j` and `k` over its list, letters on the one
 * under the cursor.
 *
 * A page says how long its list is and what each letter does; the cursor
 * is kept here, and the page draws it — `focused(index)` — as the outline.
 * While the page is on screen its keys are on the cheatsheet; `Escape`
 * clears the cursor. Nothing here fires while something is being typed:
 * the global dispatcher has already seen to that.
 */
import { onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import { registerPageKeys } from '../shortcuts.js'
import { state } from '../state.js'
import { pageShortcuts } from '../pagekeys.js'

/**
 * `page` names the entry in `PAGE_KEYS`; `count()` is the list's length;
 * `actions` maps a key to what it does with the index under the cursor;
 * `onCursor(index)`, when given, is told of every move — for a page whose
 * list is also its selection.
 */
export function usePageKeys({ page, count, actions = {}, onCursor = null }) {
  const cursor = ref(-1)

  function move(delta) {
    const length = count()
    if (!length) {
      cursor.value = -1
      return
    }
    const next = cursor.value < 0
      ? (delta > 0 ? 0 : length - 1)
      : Math.max(0, Math.min(length - 1, cursor.value + delta))
    cursor.value = next
    onCursor?.(next)
    nextTick(() => document.querySelector('.lx-focus')?.scrollIntoView({ block: 'nearest' }))
  }

  function handle(event) {
    const key = event.key
    if (key === 'j') {
      move(1)
      return true
    }
    if (key === 'k') {
      move(-1)
      return true
    }
    if (key === 'Escape') {
      if (cursor.value < 0) return false
      cursor.value = -1
      return true
    }
    const action = actions[key]
    if (!action || cursor.value < 0 || cursor.value >= count()) return false
    action(cursor.value, event)
    return true
  }

  let unregister = null
  onMounted(() => {
    unregister = registerPageKeys(handle)
    state.pageShortcuts = pageShortcuts(page)
  })
  onBeforeUnmount(() => {
    unregister?.()
    if (state.pageShortcuts?.title === pageShortcuts(page)?.title) state.pageShortcuts = null
  })

  // A list that shrinks under the cursor leaves it on its last entry.
  watch(count, length => {
    if (cursor.value >= length) cursor.value = length - 1
  })

  return {
    cursor,
    focused: index => cursor.value === index,
    /** Put the cursor somewhere, as when the page selects by other means. */
    place: index => { cursor.value = index }
  }
}
