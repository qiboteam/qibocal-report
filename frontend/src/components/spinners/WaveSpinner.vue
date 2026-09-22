<template>
  <div class="wave-spinner">
    <div class="wave-bar"></div>
    <div class="wave-bar"></div>
    <div class="wave-bar"></div>
    <div class="wave-bar"></div>
    <div class="wave-bar"></div>
  </div>
</template>

<style scoped>
.wave-spinner {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 4px;
  height: 80px;
}

.wave-bar {
  width: 8px;
  height: 20px;
  background: linear-gradient(to top, #833dff, #c8a8ff);
  border-radius: 4px;
  animation: wave-animation 1.2s ease-in-out infinite;
}

.wave-bar:nth-child(1) {
  animation-delay: 0s;
}

.wave-bar:nth-child(2) {
  animation-delay: 0.2s;
}

.wave-bar:nth-child(3) {
  animation-delay: 0.4s;
}

.wave-bar:nth-child(4) {
  animation-delay: 0.6s;
}

.wave-bar:nth-child(5) {
  animation-delay: 0.8s;
}

@keyframes wave-animation {
  0%, 100% {
    height: 20px;
    opacity: 0.5;
  }
  50% {
    height: 50px;
    opacity: 1;
  }
}
</style>
