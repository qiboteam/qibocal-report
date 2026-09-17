import { defineConfig, presetUno, presetAttributify } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify()
  ],
  theme: {
    duration: {
      DEFAULT: '50ms',
      75: '25ms',
      100: '33ms',
      150: '50ms',
      200: '67ms',
      300: '100ms',
      500: '167ms',
      700: '233ms',
      1000: '333ms'
    },
    animation: {
      durations: {
        'fade-in': '0.33s'
      }
    },
    colors: {
      pale: '#f7f7f7',
      accentLight: '#ebe0ff',
      accentMild: '#c8a8ff',
      accent: '#833dff',
      note: '#4a4a4a'
    }
  }
})
