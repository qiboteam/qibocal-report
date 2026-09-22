<template>
  <div class="pulse-spinner">
    <div class="pulse-ring"></div>
    <div class="pulse-ring"></div>
    <div class="pulse-ring"></div>
  </div>
</template>

<style scoped>
.pulse-spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid rgba(131, 61, 255, 0.4);
  border-radius: 50%;
  animation: pulse-expand 2s ease-out infinite;
}

.pulse-ring:nth-child(1) {
  animation-delay: 0s;
}

.pulse-ring:nth-child(2) {
  animation-delay: 0.6s;
}

.pulse-ring:nth-child(3) {
  animation-delay: 1.2s;
}

.pulse-spinner::before {
  content: '';
  position: absolute;
  width: 12px;
  height: 12px;
  background: #833dff;
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 15px rgba(131, 61, 255, 0.8);
  z-index: 10;
}

@keyframes pulse-expand {
  0% {
    transform: scale(0.2);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}
</style>
