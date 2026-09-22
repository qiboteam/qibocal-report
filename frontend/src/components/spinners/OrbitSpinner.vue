<template>
  <div class="orbit-spinner">
    <div class="orbit-ring orbit-ring-1"></div>
    <div class="orbit-ring orbit-ring-2"></div>
    <div class="orbit-center"></div>
  </div>
</template>

<style scoped>
.orbit-spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.orbit-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid transparent;
  border-top-color: #833dff;
  border-right-color: #c8a8ff;
  border-radius: 50%;
  top: 0;
  left: 0;
  animation: orbit-rotate 2s linear infinite;
}

.orbit-ring-1 {
  animation-duration: 2s;
}

.orbit-ring-2 {
  width: 60px;
  height: 60px;
  top: 10px;
  left: 10px;
  border-top-color: #c8a8ff;
  border-right-color: #ebe0ff;
  animation-duration: 1.5s;
  animation-direction: reverse;
}

.orbit-center {
  position: absolute;
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, #833dff, #c8a8ff);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 15px rgba(131, 61, 255, 0.8);
}

@keyframes orbit-rotate {
  0% {
    transform: rotateZ(0deg);
  }
  100% {
    transform: rotateZ(360deg);
  }
}
</style>
