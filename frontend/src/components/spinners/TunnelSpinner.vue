<template>
  <div class="tunnel-spinner">
    <div class="tunnel-layer tunnel-layer-1"></div>
    <div class="tunnel-layer tunnel-layer-2"></div>
    <div class="tunnel-layer tunnel-layer-3"></div>
  </div>
</template>

<style scoped>
.tunnel-spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.tunnel-layer {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid;
  border-radius: 50%;
  top: 0;
  left: 0;
  animation: tunnel-shrink 1.8s ease-in infinite;
}

.tunnel-layer-1 {
  border-color: #833dff;
  animation-delay: 0s;
}

.tunnel-layer-2 {
  border-color: #c8a8ff;
  animation-delay: 0.6s;
}

.tunnel-layer-3 {
  border-color: #ebe0ff;
  animation-delay: 1.2s;
}

@keyframes tunnel-shrink {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(0.3);
    opacity: 0;
  }
}
</style>
