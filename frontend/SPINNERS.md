# Loading Spinners

This project includes a collection of themed, quantum-inspired loading spinners that display during page navigation and data fetching.

## Features

- **5 unique animations**: Atom, Wave, Pulse, Orbit, and Tunnel
- **Themed design**: Uses the application's purple accent color scheme
- **Random selection**: A spinner is randomly picked when the page loads
- **Responsive**: Works on all screen sizes
- **Dark mode support**: Colors adapt to system preferences

## Available Spinners

### 1. Atom Spinner
A nucleus with three revolving electrons in orbital patterns. Great for representing quantum concepts or data science.

### 2. Wave Spinner  
Propagating wave bars that rise and fall in sequence. Perfect for representing data flow or streaming.

### 3. Pulse Spinner
Expanding concentric rings with a center point. Represents radiating energy or data spreading outward.

### 4. Orbit Spinner
Multiple orbital rings rotating at different speeds. Classic planetary motion visualized.

### 5. Tunnel Spinner
Shrinking layers creating a tunnel effect. Represents depth or dimensional reduction.

## Usage

### Basic Usage (Automatic)

The main loading spinner is already integrated into `App.vue` and displays automatically during route navigation:

```vue
<LoadingSpinner v-if="isNavigating" label="Loading..." />
```

A random spinner is selected each time the app navigates between pages.

### In Individual Components

Use the `useLoading` composable to show the spinner during data fetching:

```vue
<script setup>
import { useLoading } from '@/composables/useLoading.js'

const { isLoading, withLoading } = useLoading()

const fetchData = async () => {
  await withLoading(async () => {
    // Your async operation here
    const response = await api.fetchData()
  })
}
</script>

<template>
  <LoadingSpinner v-if="isLoading" label="Fetching data..." />
  <div v-show="!isLoading">
    <!-- Your content here -->
  </div>
</template>
```

### Using Specific Spinners

Import individual spinner components for more control:

```vue
<script setup>
import AtomSpinner from '@/components/spinners/AtomSpinner.vue'
</script>

<template>
  <div class="flex items-center justify-center">
    <AtomSpinner />
  </div>
</template>
```

Available spinner components:
- `AtomSpinner.vue`
- `WaveSpinner.vue`
- `PulseSpinner.vue`
- `OrbitSpinner.vue`
- `TunnelSpinner.vue`

### Props

The `LoadingSpinner` component accepts:
- `label` (String, optional): Text to display below the spinner (e.g., "Loading...")

## Styling

All spinners use CSS custom properties and the app's color scheme:
- Primary color: `#833dff` (purple)
- Secondary color: `#c8a8ff` (light purple)
- Accent color: `#ebe0ff` (very light purple)

To customize colors, modify the CSS in individual spinner components or adjust the CSS custom properties in your theme.

## Dark Mode

Spinners automatically adapt to dark mode preferences. The glow effects become more pronounced on dark backgrounds for better visibility.

## Performance

The spinners are pure CSS animations with no JavaScript processing, making them performant and smooth even on low-end devices.

## Showcase

To see all spinners in action, view the `SpinnerShowcase.vue` component. This can be useful for development and design approval.
