<template>
  <div class="atom-spinner">
    <div class="nucleus"></div>
    <div class="electron electron-1"></div>
    <div class="electron electron-2"></div>
    <div class="electron electron-3"></div>
  </div>
</template>

<style scoped>
.atom-spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.nucleus {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, #833dff, #c8a8ff);
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(131, 61, 255, 0.6);
}

.electron {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 60px;
  height: 60px;
  border: 2px solid rgba(131, 61, 255, 0.3);
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.electron::before {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  background: #833dff;
  border-radius: 50%;
  top: -4px;
  left: 50%;
  transform: translateX(-50%);
  box-shadow: 0 0 10px rgba(131, 61, 255, 0.8);
}

.electron-1 {
  animation: rotate-electron 3s linear infinite;
}

.electron-2 {
  animation: rotate-electron 3s linear infinite;
  animation-delay: -1s;
  transform: translate(-50%, -50%) rotateZ(60deg);
}

.electron-2::before {
  animation: pulse-dot 3s linear infinite;
}

.electron-3 {
  animation: rotate-electron 3s linear infinite;
  animation-delay: -2s;
  transform: translate(-50%, -50%) rotateZ(120deg);
}

.electron-3::before {
  animation: pulse-dot 3s linear infinite;
  animation-delay: -1s;
}

@keyframes rotate-electron {
  0% {
    transform: translate(-50%, -50%) rotateZ(0deg);
  }
  100% {
    transform: translate(-50%, -50%) rotateZ(360deg);
  }
}

@keyframes pulse-dot {
  0%, 100% {
    box-shadow: 0 0 10px rgba(131, 61, 255, 0.8);
  }
  50% {
    box-shadow: 0 0 20px rgba(131, 61, 255, 1);
  }
}

@media (prefers-color-scheme: dark) {
  .nucleus {
    box-shadow: 0 0 20px rgba(200, 168, 255, 0.8);
  }

  .electron::before {
    box-shadow: 0 0 10px rgba(200, 168, 255, 1);
  }
}
</style>
