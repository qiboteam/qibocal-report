import { ref } from 'vue'

/**
 * Composable for managing loading state during async operations.
 * Shows/hides the loading spinner overlay while data is being fetched.
 */
export function useLoading() {
  const isLoading = ref(false)

  const withLoading = async (asyncFn) => {
    isLoading.value = true
    try {
      return await asyncFn()
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    withLoading
  }
}
