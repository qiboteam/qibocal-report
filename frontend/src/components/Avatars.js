// Library of 10 elegant abstract quantum SVG icons and procedural generator (Issue #4)

export const AVATAR_KEYS = [
  "quantum-ring",
  "bloch-sphere",
  "wave-packet",
  "lattice",
  "flux-loop",
  "resonator",
  "orbital",
  "prism",
  "qubit-cross",
  "hadamard"
]

export const AVATAR_SVGS = {
  "quantum-ring": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <circle cx="40" cy="40" r="32" stroke="#ebe0ff" stroke-width="4"/>
      <circle cx="40" cy="40" r="22" stroke="#833dff" stroke-width="3" stroke-dasharray="6 4"/>
      <circle cx="40" cy="40" r="10" fill="#833dff"/>
      <circle cx="40" cy="18" r="4" fill="#c8a8ff"/>
      <circle cx="58" cy="48" r="3" fill="#833dff"/>
    </svg>
  `,
  "bloch-sphere": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <circle cx="40" cy="40" r="30" stroke="#833dff" stroke-width="2.5" fill="#faf8ff"/>
      <ellipse cx="40" cy="40" rx="30" ry="12" stroke="#c8a8ff" stroke-width="2" stroke-dasharray="4 3"/>
      <line x1="40" y1="10" x2="40" y2="70" stroke="#833dff" stroke-width="2"/>
      <line x1="40" y1="40" x2="62" y2="24" stroke="#4a4a4a" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="62" cy="24" r="4" fill="#833dff"/>
    </svg>
  `,
  "wave-packet": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <rect width="80" height="80" rx="16" fill="#f6f2ff"/>
      <path d="M12 40 Q26 15 40 40 T68 40" stroke="#833dff" stroke-width="3.5" fill="none" stroke-linecap="round"/>
      <path d="M16 40 Q28 28 40 40 T64 40" stroke="#c8a8ff" stroke-width="2" fill="none"/>
      <circle cx="40" cy="40" r="4" fill="#833dff"/>
    </svg>
  `,
  "lattice": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <rect width="80" height="80" rx="16" fill="#faf7ff"/>
      <polygon points="40,16 64,30 64,58 40,72 16,58 16,30" stroke="#c8a8ff" stroke-width="2.5" fill="none"/>
      <polygon points="40,28 52,35 52,49 40,56 28,49 28,35" stroke="#833dff" stroke-width="2" fill="#ebe0ff"/>
      <circle cx="40" cy="42" r="5" fill="#833dff"/>
    </svg>
  `,
  "flux-loop": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <rect width="80" height="80" rx="16" fill="#fbfaff"/>
      <rect x="20" y="20" width="40" height="40" rx="10" stroke="#833dff" stroke-width="3" fill="none"/>
      <line x1="34" y1="20" x2="46" y2="20" stroke="#ffffff" stroke-width="5"/>
      <line x1="36" y1="16" x2="44" y2="24" stroke="#833dff" stroke-width="2.5"/>
      <line x1="44" y1="16" x2="36" y2="24" stroke="#833dff" stroke-width="2.5"/>
      <circle cx="40" cy="40" r="6" fill="#c8a8ff"/>
    </svg>
  `,
  "resonator": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <rect width="80" height="80" rx="16" fill="#f8f4ff"/>
      <path d="M16 26 H32 V40 H48 V54 H64" stroke="#833dff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      <circle cx="16" cy="26" r="4" fill="#833dff"/>
      <circle cx="64" cy="54" r="4" fill="#833dff"/>
    </svg>
  `,
  "orbital": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <rect width="80" height="80" rx="16" fill="#fcfaff"/>
      <ellipse cx="40" cy="28" rx="12" ry="16" fill="#ebe0ff" stroke="#833dff" stroke-width="2"/>
      <ellipse cx="40" cy="52" rx="12" ry="16" fill="#833dff" opacity="0.85"/>
      <circle cx="40" cy="40" r="3" fill="#000000"/>
    </svg>
  `,
  "prism": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <rect width="80" height="80" rx="16" fill="#f7f5fe"/>
      <polygon points="40,16 68,64 12,64" stroke="#833dff" stroke-width="3" fill="#ebe0ff" fill-opacity="0.5"/>
      <line x1="8" y1="42" x2="33" y2="40" stroke="#4a4a4a" stroke-width="2.5"/>
      <line x1="47" y1="40" x2="72" y2="30" stroke="#833dff" stroke-width="2.5"/>
      <line x1="47" y1="40" x2="72" y2="48" stroke="#c8a8ff" stroke-width="2.5"/>
    </svg>
  `,
  "qubit-cross": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <rect width="80" height="80" rx="16" fill="#faf8ff"/>
      <path d="M34 16 H46 V34 H64 V46 H46 V64 H34 V46 H16 V34 H34 Z" fill="#833dff"/>
      <circle cx="40" cy="40" r="5" fill="#ffffff"/>
    </svg>
  `,
  "hadamard": `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <rect x="15" y="15" width="50" height="50" rx="10" fill="#833dff"/>
      <text x="40" y="49" fill="#ffffff" font-size="28" font-family="serif" font-weight="bold" text-anchor="middle">H</text>
    </svg>
  `
}

export function renderAvatar(key, seed = "") {
  if (key && AVATAR_SVGS[key]) {
    return AVATAR_SVGS[key]
  }

  // Procedural fallback identicon
  const hash = (seed || key || "seed")
    .split("")
    .reduce((acc, char) => (acc * 31 + char.charCodeAt(0)) % 1000000, 0)

  const c1 = "#833dff"
  const c2 = "#c8a8ff"
  const c3 = "#ebe0ff"
  const d1 = (hash % 30) + 20
  const d2 = ((hash >> 2) % 25) + 15

  return `
    <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
      <rect width="80" height="80" rx="16" fill="${c3}"/>
      <circle cx="40" cy="40" r="${d1}" fill="${c2}" opacity="0.6"/>
      <rect x="${40 - d2/2}" y="${40 - d2/2}" width="${d2}" height="${d2}" rx="6" fill="${c1}"/>
      <circle cx="40" cy="40" r="4" fill="#ffffff"/>
    </svg>
  `
}
