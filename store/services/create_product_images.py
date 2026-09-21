"""
Generate premium SVG artwork for all 26 catalog products in FoodBasket.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / 'static' / 'images' / 'products'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SVGS = {
    'red-apples': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="appleGrad" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#FF5252"/>
      <stop offset="45%" stop-color="#E53935"/>
      <stop offset="85%" stop-color="#C62828"/>
      <stop offset="100%" stop-color="#8E0000"/>
    </radialGradient>
    <linearGradient id="leafGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#66BB6A"/>
      <stop offset="100%" stop-color="#2E7D32"/>
    </linearGradient>
    <linearGradient id="stemGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#8D6E63"/>
      <stop offset="100%" stop-color="#4E342E"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="6" stdDeviation="6" flood-opacity="0.22" flood-color="#5A0000"/>
    </filter>
  </defs>
  <!-- Background glow circle -->
  <circle cx="80" cy="80" r="72" fill="#FEE2E2" opacity="0.6"/>
  <!-- Stem -->
  <path d="M78 48 C77 34, 86 22, 94 18 C93 23, 89 36, 82 48 Z" fill="url(#stemGrad)"/>
  <!-- Leaf -->
  <path d="M82 32 C98 22, 118 28, 122 40 C108 46, 88 42, 82 32 Z" fill="url(#leafGrad)" filter="url(#shadow)"/>
  <path d="M84 33 Q102 34 118 39" stroke="#A5D6A7" stroke-width="1.2" fill="none"/>
  <!-- Apple Body -->
  <path d="M80 52 C56 50, 32 64, 32 94 C32 126, 56 142, 74 142 C79 142, 80 139, 86 139 C92 139, 93 142, 98 142 C116 142, 140 126, 140 94 C140 64, 116 50, 92 52 C86 52, 83 56, 80 56 C77 56, 74 52, 68 52 Z" fill="url(#appleGrad)" filter="url(#shadow)"/>
  <!-- Highlights -->
  <ellipse cx="58" cy="74" rx="14" ry="24" transform="rotate(-25 58 74)" fill="#FFFFFF" opacity="0.28"/>
  <circle cx="50" cy="66" r="5" fill="#FFFFFF" opacity="0.45"/>
  <circle cx="56" cy="82" r="3" fill="#FFFFFF" opacity="0.3"/>
</svg>''',

    'bananas': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="banGrad1" x1="20%" y1="0%" x2="80%" y2="100%">
      <stop offset="0%" stop-color="#FFF176"/>
      <stop offset="50%" stop-color="#FDD835"/>
      <stop offset="90%" stop-color="#FBC02D"/>
      <stop offset="100%" stop-color="#827717"/>
    </linearGradient>
    <linearGradient id="banGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFEE58"/>
      <stop offset="60%" stop-color="#FBC02D"/>
      <stop offset="100%" stop-color="#689F38"/>
    </linearGradient>
    <filter id="dropB" x="-10%" y="-10%" width="125%" height="125%">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.18" flood-color="#7B6000"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF9C3" opacity="0.65"/>
  <!-- Banana Back -->
  <path d="M42 42 C64 54, 98 72, 114 108 C120 122, 112 128, 102 124 C82 92, 54 70, 36 50 Z" fill="#EAB308" opacity="0.5"/>
  <!-- Banana 1 -->
  <path d="M40 38 C68 46, 108 72, 126 112 C130 122, 122 128, 114 126 C90 92, 58 64, 34 46 Z" fill="url(#banGrad1)" filter="url(#dropB)"/>
  <!-- Banana 2 Front -->
  <path d="M38 48 C66 58, 102 86, 116 122 C118 128, 110 134, 104 130 C78 100, 50 74, 30 56 Z" fill="url(#banGrad2)" filter="url(#dropB)"/>
  <!-- Stem top -->
  <path d="M32 42 C30 36, 36 32, 44 36 L40 46 Z" fill="#556B2F"/>
  <!-- Tips -->
  <circle cx="120" cy="120" r="3.5" fill="#5D4037"/>
  <circle cx="110" cy="128" r="3" fill="#5D4037"/>
  <!-- Highlight -->
  <path d="M46 54 C72 68, 96 90, 106 114" stroke="#FFFDE7" stroke-width="3.5" stroke-linecap="round" fill="none" opacity="0.55"/>
</svg>''',

    'mangoes': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="mangoGrad" cx="40%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#FFD54F"/>
      <stop offset="35%" stop-color="#FFA000"/>
      <stop offset="70%" stop-color="#FF5722"/>
      <stop offset="100%" stop-color="#D84315"/>
    </radialGradient>
    <filter id="mShadow">
      <feDropShadow dx="0" dy="6" stdDeviation="6" flood-opacity="0.2" flood-color="#8B3000"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF3C7" opacity="0.65"/>
  <!-- Leaf -->
  <path d="M82 36 C102 24, 126 30, 130 42 C114 48, 92 46, 82 36 Z" fill="#2E7D32"/>
  <path d="M84 37 Q106 38 124 41" stroke="#81C784" stroke-width="1.2" fill="none"/>
  <!-- Stem -->
  <rect x="76" y="32" width="6" height="14" rx="3" fill="#4E342E"/>
  <!-- Mango body -->
  <path d="M78 44 C52 46, 32 68, 34 100 C36 128, 62 144, 90 140 C118 136, 134 112, 130 84 C126 58, 102 42, 78 44 Z" fill="url(#mangoGrad)" filter="url(#mShadow)"/>
  <!-- Blush and highlight -->
  <ellipse cx="64" cy="72" rx="14" ry="24" transform="rotate(-30 64 72)" fill="#FFFFFF" opacity="0.32"/>
  <circle cx="56" cy="64" r="5" fill="#FFFFFF" opacity="0.5"/>
</svg>''',

    'watermelon': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="wmFlesh" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FF1744"/>
      <stop offset="100%" stop-color="#D50000"/>
    </linearGradient>
    <filter id="wmS">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-opacity="0.2" flood-color="#003810"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#DCFCE7" opacity="0.6"/>
  <!-- Outer Rind Green -->
  <path d="M22 76 C22 120, 52 144, 80 144 C108 144, 138 120, 138 76 Z" fill="#1B5E20" filter="url(#wmS)"/>
  <!-- Light green layer -->
  <path d="M26 78 C26 118, 54 140, 80 140 C106 140, 134 118, 134 78 Z" fill="#A5D6A7"/>
  <!-- White rind ring -->
  <path d="M29 80 C29 116, 55 137, 80 137 C105 137, 131 116, 131 80 Z" fill="#F1F8E9"/>
  <!-- Red Juicy Flesh -->
  <path d="M33 80 C33 113, 56 133, 80 133 C104 133, 127 113, 127 80 Z" fill="url(#wmFlesh)"/>
  <!-- Seeds -->
  <ellipse cx="55" cy="95" rx="2.5" ry="4" transform="rotate(-20 55 95)" fill="#212121"/>
  <ellipse cx="70" cy="112" rx="2.5" ry="4" transform="rotate(5 70 112)" fill="#212121"/>
  <ellipse cx="90" cy="112" rx="2.5" ry="4" transform="rotate(-5 90 112)" fill="#212121"/>
  <ellipse cx="105" cy="95" rx="2.5" ry="4" transform="rotate(20 105 95)" fill="#212121"/>
  <ellipse cx="80" cy="96" rx="2.5" ry="4" fill="#212121"/>
  <!-- Slice Top Edge Highlight -->
  <path d="M26 78 L134 78" stroke="#FFFFFF" stroke-width="2.5" opacity="0.4"/>
</svg>''',

    'grapes': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="grapeGrad" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#C084FC"/>
      <stop offset="40%" stop-color="#9333EA"/>
      <stop offset="90%" stop-color="#6B21A8"/>
      <stop offset="100%" stop-color="#3B0764"/>
    </radialGradient>
    <filter id="gShadow">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.22" flood-color="#2E0854"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#F3E8FF" opacity="0.6"/>
  <!-- Vine Stem and Leaves -->
  <path d="M80 20 Q84 34 78 48" stroke="#78350F" stroke-width="4.5" fill="none" stroke-linecap="round"/>
  <path d="M78 32 C96 22, 114 26, 118 36 C106 44, 88 42, 78 32 Z" fill="#15803D"/>
  <!-- Grape cluster -->
  <g filter="url(#gShadow)">
    <circle cx="64" cy="56" r="14" fill="url(#grapeGrad)"/>
    <circle cx="94" cy="56" r="14" fill="url(#grapeGrad)"/>
    <circle cx="79" cy="62" r="14" fill="url(#grapeGrad)"/>
    <circle cx="54" cy="76" r="13" fill="url(#grapeGrad)"/>
    <circle cx="76" cy="80" r="14" fill="url(#grapeGrad)"/>
    <circle cx="98" cy="76" r="13" fill="url(#grapeGrad)"/>
    <circle cx="62" cy="98" r="13" fill="url(#grapeGrad)"/>
    <circle cx="86" cy="98" r="13" fill="url(#grapeGrad)"/>
    <circle cx="72" cy="116" r="12" fill="url(#grapeGrad)"/>
    <circle cx="86" cy="118" r="11" fill="url(#grapeGrad)"/>
    <circle cx="78" cy="132" r="9" fill="url(#grapeGrad)"/>
  </g>
  <!-- Gloss dots -->
  <circle cx="75" cy="58" r="3" fill="#FFF" opacity="0.4"/>
  <circle cx="72" cy="76" r="3" fill="#FFF" opacity="0.4"/>
  <circle cx="82" cy="94" r="2.5" fill="#FFF" opacity="0.4"/>
</svg>''',

    'spinach': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="spinach1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4ADE80"/>
      <stop offset="60%" stop-color="#16A34A"/>
      <stop offset="100%" stop-color="#14532D"/>
    </linearGradient>
    <linearGradient id="spinach2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#22C55E"/>
      <stop offset="70%" stop-color="#15803D"/>
      <stop offset="100%" stop-color="#052E16"/>
    </linearGradient>
    <filter id="spinS">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.18" flood-color="#032D14"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#DCFCE7" opacity="0.6"/>
  <!-- Leaves back -->
  <path d="M42 98 C30 50, 60 26, 80 22 C100 26, 128 50, 116 98 C108 116, 92 134, 80 144 C66 134, 50 116, 42 98 Z" fill="url(#spinach2)" filter="url(#spinS)"/>
  <!-- Leaves Left -->
  <path d="M32 92 C24 58, 48 38, 70 38 C76 60, 72 90, 60 114 C50 110, 36 104, 32 92 Z" fill="url(#spinach1)"/>
  <!-- Leaves Right -->
  <path d="M128 92 C136 58, 112 38, 90 38 C84 60, 88 90, 100 114 C110 110, 124 104, 128 92 Z" fill="url(#spinach1)"/>
  <!-- Central Veins -->
  <path d="M80 144 Q80 84 80 32" stroke="#86EFAC" stroke-width="2.5" fill="none"/>
  <path d="M80 80 Q62 68 50 64" stroke="#86EFAC" stroke-width="1.8" fill="none"/>
  <path d="M80 80 Q98 68 110 64" stroke="#86EFAC" stroke-width="1.8" fill="none"/>
  <path d="M80 102 Q64 94 54 92" stroke="#86EFAC" stroke-width="1.8" fill="none"/>
  <path d="M80 102 Q96 94 106 92" stroke="#86EFAC" stroke-width="1.8" fill="none"/>
</svg>''',

    'tomatoes': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="tomGrad" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#FF5252"/>
      <stop offset="50%" stop-color="#E53935"/>
      <stop offset="85%" stop-color="#C62828"/>
      <stop offset="100%" stop-color="#7F0000"/>
    </radialGradient>
    <filter id="tomS">
      <feDropShadow dx="0" dy="6" stdDeviation="6" flood-opacity="0.22" flood-color="#4A0000"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEE2E2" opacity="0.6"/>
  <!-- Tomato Body -->
  <ellipse cx="80" cy="88" rx="52" ry="46" fill="url(#tomGrad)" filter="url(#tomS)"/>
  <!-- Sepals (Green crown) -->
  <g fill="#2E7D32">
    <path d="M80 44 L80 30 C80 30, 83 26, 88 28 C87 34, 84 38, 81 44 Z" fill="#4E342E"/>
    <path d="M80 46 C76 34, 60 30, 56 32 C62 38, 70 42, 80 46 Z"/>
    <path d="M80 46 C84 34, 100 30, 104 32 C98 38, 90 42, 80 46 Z"/>
    <path d="M80 46 C70 46, 54 50, 48 58 C56 58, 68 52, 80 46 Z"/>
    <path d="M80 46 C90 46, 106 50, 112 58 C104 58, 92 52, 80 46 Z"/>
    <path d="M80 46 C80 54, 76 66, 78 72 C80 66, 82 56, 80 46 Z"/>
  </g>
  <!-- Specular highlights -->
  <ellipse cx="58" cy="72" rx="14" ry="20" transform="rotate(-30 58 72)" fill="#FFFFFF" opacity="0.32"/>
  <circle cx="52" cy="66" r="4.5" fill="#FFFFFF" opacity="0.5"/>
</svg>''',

    'onions': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="onionGrad" cx="40%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#F472B6"/>
      <stop offset="40%" stop-color="#DB2777"/>
      <stop offset="85%" stop-color="#831843"/>
      <stop offset="100%" stop-color="#500724"/>
    </radialGradient>
    <filter id="onS">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.2" flood-color="#4C0519"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FCE7F3" opacity="0.6"/>
  <!-- Top sprout stem -->
  <path d="M80 24 C82 36, 81 48, 80 54 C78 48, 76 36, 74 24 C77 22, 79 22, 80 24 Z" fill="#65A30D"/>
  <path d="M78 40 Q84 46 80 56" stroke="#4D7C0F" stroke-width="3"/>
  <!-- Onion bulb -->
  <path d="M80 50 C50 50, 32 74, 34 102 C36 126, 60 140, 80 140 C100 140, 124 126, 126 102 C128 74, 110 50, 80 50 Z" fill="url(#onionGrad)" filter="url(#onS)"/>
  <!-- Onion skin lines -->
  <path d="M80 50 Q60 92 80 140" stroke="#FBCFE8" stroke-width="1.5" fill="none" opacity="0.45"/>
  <path d="M80 50 Q46 92 72 138" stroke="#FBCFE8" stroke-width="1.5" fill="none" opacity="0.4"/>
  <path d="M80 50 Q100 92 80 140" stroke="#FBCFE8" stroke-width="1.5" fill="none" opacity="0.45"/>
  <path d="M80 50 Q114 92 88 138" stroke="#FBCFE8" stroke-width="1.5" fill="none" opacity="0.4"/>
  <!-- Root hairs -->
  <path d="M76 140 L74 148 M80 140 L80 150 M84 140 L86 148" stroke="#A16207" stroke-width="2" stroke-linecap="round"/>
</svg>''',

    'potatoes': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="potGrad" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#FDE68A"/>
      <stop offset="40%" stop-color="#D97706"/>
      <stop offset="85%" stop-color="#92400E"/>
      <stop offset="100%" stop-color="#5C2503"/>
    </radialGradient>
    <filter id="potS">
      <feDropShadow dx="0" dy="6" stdDeviation="6" flood-opacity="0.22" flood-color="#451A03"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF3C7" opacity="0.55"/>
  <!-- Back Potato -->
  <path d="M90 45 C116 48, 134 68, 132 94 C130 118, 110 132, 88 128 C66 124, 62 102, 68 80 C74 58, 76 43, 90 45 Z" fill="#B45309" opacity="0.6"/>
  <!-- Front Big Potato -->
  <path d="M54 54 C82 46, 118 58, 120 86 C122 116, 96 136, 68 134 C40 132, 28 110, 30 84 C32 60, 40 58, 54 54 Z" fill="url(#potGrad)" filter="url(#potS)"/>
  <!-- Eyes / Dimples -->
  <path d="M52 74 Q56 76 60 74" stroke="#78350F" stroke-width="2.5" stroke-linecap="round" fill="none"/>
  <circle cx="56" cy="74" r="1.5" fill="#451A03"/>
  <path d="M82 66 Q86 68 90 66" stroke="#78350F" stroke-width="2.5" stroke-linecap="round" fill="none"/>
  <circle cx="86" cy="66" r="1.5" fill="#451A03"/>
  <path d="M72 104 Q76 106 80 104" stroke="#78350F" stroke-width="2.5" stroke-linecap="round" fill="none"/>
  <circle cx="76" cy="104" r="1.5" fill="#451A03"/>
  <path d="M102 96 Q106 98 110 96" stroke="#78350F" stroke-width="2.5" stroke-linecap="round" fill="none"/>
  <!-- Highlight -->
  <ellipse cx="60" cy="62" rx="16" ry="8" transform="rotate(-15 60 62)" fill="#FFFFFF" opacity="0.25"/>
</svg>''',

    'broccoli': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="floretG1" cx="30%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#4ADE80"/>
      <stop offset="50%" stop-color="#16A34A"/>
      <stop offset="100%" stop-color="#14532D"/>
    </radialGradient>
    <radialGradient id="floretG2" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#86EFAC"/>
      <stop offset="60%" stop-color="#22C55E"/>
      <stop offset="100%" stop-color="#15803D"/>
    </radialGradient>
    <linearGradient id="stalkG" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#86EFAC"/>
      <stop offset="50%" stop-color="#4ADE80"/>
      <stop offset="100%" stop-color="#22C55E"/>
    </linearGradient>
    <filter id="brocS">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-opacity="0.2" flood-color="#052E16"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#DCFCE7" opacity="0.6"/>
  <!-- Stalk -->
  <path d="M70 94 L68 136 C68 142, 92 142, 92 136 L90 94 Z" fill="url(#stalkG)"/>
  <!-- Florets cluster -->
  <g filter="url(#brocS)">
    <circle cx="48" cy="74" r="22" fill="url(#floretG1)"/>
    <circle cx="112" cy="74" r="22" fill="url(#floretG1)"/>
    <circle cx="56" cy="52" r="24" fill="url(#floretG2)"/>
    <circle cx="104" cy="52" r="24" fill="url(#floretG2)"/>
    <circle cx="80" cy="44" r="26" fill="url(#floretG2)"/>
    <circle cx="80" cy="74" r="26" fill="url(#floretG1)"/>
  </g>
  <!-- Texture dots -->
  <circle cx="76" cy="40" r="3" fill="#BBF7D0" opacity="0.7"/>
  <circle cx="86" cy="44" r="2.5" fill="#BBF7D0" opacity="0.7"/>
  <circle cx="56" cy="50" r="2.5" fill="#BBF7D0" opacity="0.6"/>
  <circle cx="102" cy="50" r="2.5" fill="#BBF7D0" opacity="0.6"/>
</svg>''',

    'carrots': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="carrGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FB923C"/>
      <stop offset="40%" stop-color="#F97316"/>
      <stop offset="85%" stop-color="#EA580C"/>
      <stop offset="100%" stop-color="#9A3412"/>
    </linearGradient>
    <filter id="carrS">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-opacity="0.2" flood-color="#7C2D12"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FFEDD5" opacity="0.6"/>
  <!-- Foliage green tops -->
  <path d="M78 46 C66 18, 48 14, 46 16 C50 28, 64 36, 76 48 Z" fill="#16A34A"/>
  <path d="M80 44 C80 12, 88 8, 90 10 C90 24, 86 36, 82 46 Z" fill="#22C55E"/>
  <path d="M82 46 C94 18, 112 14, 114 16 C110 28, 96 36, 84 48 Z" fill="#15803D"/>
  <!-- Main Carrot Cone Body -->
  <path d="M62 48 C74 46, 88 46, 98 48 C98 56, 84 126, 80 144 C76 126, 62 56, 62 48 Z" fill="url(#carrGrad)" filter="url(#carrS)"/>
  <!-- Ridges -->
  <path d="M68 62 Q78 64 88 62" stroke="#C2410C" stroke-width="2.2" stroke-linecap="round" fill="none"/>
  <path d="M70 78 Q78 80 90 78" stroke="#C2410C" stroke-width="2.2" stroke-linecap="round" fill="none"/>
  <path d="M72 96 Q78 98 86 96" stroke="#C2410C" stroke-width="2.2" stroke-linecap="round" fill="none"/>
  <path d="M74 114 Q78 116 84 114" stroke="#C2410C" stroke-width="2" stroke-linecap="round" fill="none"/>
  <!-- Highlight -->
  <path d="M68 52 Q74 90 77 122" stroke="#FFEDD5" stroke-width="2.5" stroke-linecap="round" fill="none" opacity="0.4"/>
</svg>''',

    'full-cream-milk': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="milkBot" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#E2E8F0"/>
      <stop offset="25%" stop-color="#FFFFFF"/>
      <stop offset="75%" stop-color="#F8FAFC"/>
      <stop offset="100%" stop-color="#CBD5E1"/>
    </linearGradient>
    <linearGradient id="blueLabel" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="100%" stop-color="#0284C7"/>
    </linearGradient>
    <filter id="mBotS">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.18" flood-color="#0369A1"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#E0F2FE" opacity="0.6"/>
  <!-- Bottle Cap -->
  <rect x="68" y="24" width="24" height="10" rx="3" fill="#0284C7"/>
  <!-- Bottle Neck -->
  <path d="M72 34 L72 46 C72 52, 54 60, 52 74 L52 134 C52 140, 56 144, 64 144 L96 144 C104 144, 108 140, 108 134 L108 74 C106 60, 88 52, 88 46 L88 34 Z" fill="url(#milkBot)" filter="url(#mBotS)"/>
  <!-- Label -->
  <rect x="52" y="80" width="56" height="38" rx="4" fill="url(#blueLabel)"/>
  <!-- Label details -->
  <text x="80" y="96" font-family="system-ui, sans-serif" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">MILK</text>
  <text x="80" y="107" font-family="system-ui, sans-serif" font-size="6.5" font-weight="600" fill="#E0F2FE" text-anchor="middle">FULL CREAM</text>
  <path d="M52 108 Q80 114 108 108" stroke="#BAE6FD" stroke-width="1.5" fill="none"/>
  <!-- Glass reflection -->
  <path d="M58 56 L58 136" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" opacity="0.6"/>
</svg>''',

    'paneer': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="pTop" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#F1F5F9"/>
    </linearGradient>
    <linearGradient id="pFront" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#F1F5F9"/>
      <stop offset="100%" stop-color="#E2E8F0"/>
    </linearGradient>
    <linearGradient id="pSide" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#CBD5E1"/>
      <stop offset="100%" stop-color="#94A3B8"/>
    </linearGradient>
    <filter id="panS">
      <feDropShadow dx="0" dy="6" stdDeviation="6" flood-opacity="0.18" flood-color="#334155"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#F8FAFC" opacity="0.65"/>
  <!-- Main Paneer Block 3D isometric -->
  <g filter="url(#panS)">
    <!-- Top Face -->
    <polygon points="80,42 128,66 80,90 32,66" fill="url(#pTop)"/>
    <!-- Left Front Face -->
    <polygon points="32,66 80,90 80,126 32,102" fill="url(#pFront)"/>
    <!-- Right Front Face -->
    <polygon points="80,90 128,66 128,102 80,126" fill="url(#pSide)"/>
  </g>
  <!-- Mint Leaf Garnish on Top -->
  <path d="M80 58 C74 50, 64 52, 62 56 C68 60, 76 60, 80 58 Z" fill="#16A34A"/>
  <path d="M80 58 C86 50, 96 52, 98 56 C92 60, 84 60, 80 58 Z" fill="#22C55E"/>
  <circle cx="80" cy="58" r="2" fill="#15803D"/>
  <!-- Cut slice lines -->
  <line x1="56" y1="54" x2="104" y2="78" stroke="#E2E8F0" stroke-width="1.2"/>
  <line x1="56" y1="78" x2="56" y2="114" stroke="#CBD5E1" stroke-width="1.2"/>
</svg>''',

    'curd-yogurt': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="potGradY" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FB923C"/>
      <stop offset="50%" stop-color="#EA580C"/>
      <stop offset="100%" stop-color="#9A3412"/>
    </linearGradient>
    <radialGradient id="curdCream" cx="45%" cy="40%" r="55%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="70%" stop-color="#F8FAFC"/>
      <stop offset="100%" stop-color="#E2E8F0"/>
    </radialGradient>
    <filter id="curdS">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-opacity="0.2" flood-color="#7C2D12"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FFEDD5" opacity="0.6"/>
  <!-- Matka / Clay Bowl Body -->
  <path d="M28 72 C26 108, 48 138, 80 138 C112 138, 134 108, 132 72 Z" fill="url(#potGradY)" filter="url(#curdS)"/>
  <!-- Matka Rim -->
  <ellipse cx="80" cy="72" rx="52" ry="16" fill="#C2410C"/>
  <!-- Creamy Curd Fill -->
  <ellipse cx="80" cy="72" rx="46" ry="13" fill="url(#curdCream)"/>
  <!-- Curd Swirl / Dollop -->
  <path d="M72 68 Q80 62 88 68 Q80 74 72 68 Z" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1"/>
  <!-- Clay pot decorative band -->
  <path d="M38 98 Q80 114 122 98" stroke="#7C2D12" stroke-width="2.5" fill="none" opacity="0.6"/>
  <path d="M46 112 Q80 124 114 112" stroke="#7C2D12" stroke-width="1.8" fill="none" opacity="0.5"/>
</svg>''',

    'butter': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="butTop" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FEF08A"/>
      <stop offset="100%" stop-color="#FDE047"/>
    </linearGradient>
    <linearGradient id="butFront" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FACC15"/>
      <stop offset="100%" stop-color="#EAB308"/>
    </linearGradient>
    <linearGradient id="butSide" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#CA8A04"/>
      <stop offset="100%" stop-color="#A16207"/>
    </linearGradient>
    <filter id="butS">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-opacity="0.2" flood-color="#854D0E"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF9C3" opacity="0.6"/>
  <!-- Dish Base -->
  <ellipse cx="80" cy="116" rx="60" ry="20" fill="#E2E8F0"/>
  <ellipse cx="80" cy="114" rx="56" ry="17" fill="#FFFFFF"/>
  <!-- Butter Block -->
  <g filter="url(#butS)">
    <!-- Top Face -->
    <polygon points="80,56 122,76 80,96 38,76" fill="url(#butTop)"/>
    <!-- Front Face -->
    <polygon points="38,76 80,96 80,122 38,102" fill="url(#butFront)"/>
    <!-- Side Face -->
    <polygon points="80,96 122,76 122,102 80,122" fill="url(#butSide)"/>
  </g>
  <!-- Butter curl on top -->
  <path d="M72 70 C72 64, 82 62, 88 66 C84 72, 74 72, 72 70 Z" fill="#FEF08A" stroke="#EAB308" stroke-width="1.2"/>
</svg>''',

    'cheese-slices': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="chGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FDE047"/>
      <stop offset="60%" stop-color="#F59E0B"/>
      <stop offset="100%" stop-color="#D97706"/>
    </linearGradient>
    <filter id="chS">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.2" flood-color="#92400E"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF3C7" opacity="0.6"/>
  <!-- Bottom Slice -->
  <polygon points="36,72 108,52 126,108 54,128" fill="#D97706" opacity="0.5"/>
  <!-- Middle Slice -->
  <polygon points="38,68 112,50 128,104 54,122" fill="#F59E0B" opacity="0.8"/>
  <!-- Top Slice -->
  <g filter="url(#chS)">
    <polygon points="42,60 116,46 124,102 50,116" fill="url(#chGrad)"/>
    <!-- Cheese Holes -->
    <ellipse cx="68" cy="74" rx="6" ry="4" fill="#D97706" opacity="0.5"/>
    <ellipse cx="96" cy="68" rx="8" ry="5" fill="#D97706" opacity="0.5"/>
    <ellipse cx="80" cy="94" rx="7" ry="4.5" fill="#D97706" opacity="0.5"/>
    <ellipse cx="106" cy="88" rx="5" ry="3.5" fill="#D97706" opacity="0.5"/>
  </g>
</svg>''',

    'whole-wheat-bread': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="crust" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#B45309"/>
      <stop offset="100%" stop-color="#78350F"/>
    </linearGradient>
    <linearGradient id="crumb" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FEF3C7"/>
      <stop offset="100%" stop-color="#FDE68A"/>
    </linearGradient>
    <filter id="brS">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-opacity="0.2" flood-color="#451A03"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF3C7" opacity="0.6"/>
  <!-- Loaf Back -->
  <path d="M50 56 C70 42, 116 44, 126 62 L126 114 C120 120, 102 122, 94 122 Z" fill="#92400E"/>
  <!-- Front Slice -->
  <g filter="url(#brS)">
    <!-- Crust outline -->
    <path d="M38 68 C34 52, 48 44, 62 46 C70 38, 90 38, 98 46 C112 44, 126 52, 122 68 C124 94, 120 118, 114 124 C100 128, 60 128, 46 124 C40 118, 36 94, 38 68 Z" fill="url(#crust)"/>
    <!-- Crumb face -->
    <path d="M43 70 C40 57, 50 50, 63 51 C70 44, 88 44, 95 51 C108 50, 118 57, 116 70 C118 92, 115 114, 109 119 C98 123, 62 123, 51 119 C45 114, 42 92, 43 70 Z" fill="url(#crumb)"/>
  </g>
  <!-- Texture Seeds -->
  <circle cx="68" cy="72" r="1.5" fill="#B45309"/>
  <circle cx="84" cy="66" r="1.8" fill="#B45309"/>
  <circle cx="98" cy="78" r="1.5" fill="#B45309"/>
  <circle cx="74" cy="94" r="1.5" fill="#B45309"/>
  <circle cx="90" cy="100" r="1.5" fill="#B45309"/>
</svg>''',

    'croissants': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="croissG" cx="40%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#FDE047"/>
      <stop offset="40%" stop-color="#F59E0B"/>
      <stop offset="80%" stop-color="#D97706"/>
      <stop offset="100%" stop-color="#78350F"/>
    </radialGradient>
    <filter id="crS">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-opacity="0.22" flood-color="#78350F"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF9C3" opacity="0.6"/>
  <!-- Crescent shape layers -->
  <g filter="url(#crS)">
    <!-- Main Crescent Body -->
    <path d="M26 102 C30 68, 54 48, 80 48 C106 48, 130 68, 134 102 C134 114, 122 118, 114 108 C104 90, 88 80, 80 80 C72 80, 56 90, 46 108 C38 118, 26 114, 26 102 Z" fill="url(#croissG)"/>
    <!-- Fold 1 Center -->
    <path d="M60 52 C72 48, 88 48, 100 52 C94 76, 86 82, 80 82 C74 82, 66 76, 60 52 Z" fill="#FBBF24" opacity="0.6"/>
    <!-- Fold lines -->
    <path d="M48 64 Q60 76 66 94" stroke="#78350F" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.45"/>
    <path d="M112 64 Q100 76 94 94" stroke="#78350F" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.45"/>
    <path d="M68 52 Q80 62 80 80" stroke="#78350F" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.45"/>
    <path d="M92 52 Q80 62 80 80" stroke="#78350F" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.45"/>
  </g>
  <!-- Glaze shine -->
  <path d="M68 56 Q80 52 92 56" stroke="#FEF08A" stroke-width="3" stroke-linecap="round" fill="none"/>
</svg>''',

    'multigrain-biscuits': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="biscG" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#FDE68A"/>
      <stop offset="50%" stop-color="#F59E0B"/>
      <stop offset="90%" stop-color="#D97706"/>
      <stop offset="100%" stop-color="#92400E"/>
    </radialGradient>
    <filter id="biS">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.2" flood-color="#78350F"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF3C7" opacity="0.6"/>
  <!-- Biscuit 1 Back -->
  <circle cx="94" cy="74" r="38" fill="#B45309" opacity="0.5"/>
  <!-- Biscuit 2 Front -->
  <g filter="url(#biS)">
    <circle cx="74" cy="84" r="40" fill="url(#biscG)"/>
    <!-- Scalloped rim or inner border -->
    <circle cx="74" cy="84" r="35" stroke="#B45309" stroke-width="1.2" stroke-dasharray="3,3" fill="none"/>
    <!-- Docking holes -->
    <circle cx="64" cy="74" r="2" fill="#78350F"/>
    <circle cx="74" cy="74" r="2" fill="#78350F"/>
    <circle cx="84" cy="74" r="2" fill="#78350F"/>
    <circle cx="58" cy="84" r="2" fill="#78350F"/>
    <circle cx="74" cy="84" r="2" fill="#78350F"/>
    <circle cx="90" cy="84" r="2" fill="#78350F"/>
    <circle cx="64" cy="94" r="2" fill="#78350F"/>
    <circle cx="74" cy="94" r="2" fill="#78350F"/>
    <circle cx="84" cy="94" r="2" fill="#78350F"/>
  </g>
  <!-- Flakes -->
  <ellipse cx="68" cy="66" rx="3" ry="1.5" fill="#FEF9C3"/>
  <ellipse cx="82" cy="88" rx="3" ry="1.5" transform="rotate(30 82 88)" fill="#FEF9C3"/>
</svg>''',

    'chocolate-cake': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="chocFrost" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#451A03"/>
      <stop offset="100%" stop-color="#1E0B02"/>
    </linearGradient>
    <linearGradient id="chocSponge" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#78350F"/>
      <stop offset="100%" stop-color="#451A03"/>
    </linearGradient>
    <filter id="cakeS">
      <feDropShadow dx="0" dy="6" stdDeviation="6" flood-opacity="0.25" flood-color="#1E0B02"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FCE7F3" opacity="0.6"/>
  <!-- Cake slice 3D -->
  <g filter="url(#cakeS)">
    <!-- Top triangular frosting -->
    <polygon points="80,48 132,84 32,84" fill="url(#chocFrost)"/>
    <!-- Side sponge face -->
    <polygon points="32,84 132,84 132,126 32,126" fill="url(#chocSponge)"/>
    <!-- Layer Cream 1 -->
    <rect x="32" y="96" width="100" height="4" fill="#FDF2F8"/>
    <!-- Layer Cream 2 -->
    <rect x="32" y="112" width="100" height="4" fill="#FDF2F8"/>
  </g>
  <!-- Cherry on Top -->
  <circle cx="80" cy="42" r="10" fill="#E11D48"/>
  <circle cx="77" cy="39" r="2.5" fill="#FFFFFF" opacity="0.6"/>
  <path d="M80 34 C82 22, 94 18, 98 20" stroke="#15803D" stroke-width="2" fill="none" stroke-linecap="round"/>
</svg>''',

    'orange-juice': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="ojGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FDBA74"/>
      <stop offset="30%" stop-color="#FB923C"/>
      <stop offset="100%" stop-color="#EA580C"/>
    </linearGradient>
    <filter id="ojS">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.2" flood-color="#9A3412"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FFEDD5" opacity="0.65"/>
  <!-- Straw -->
  <line x1="88" y1="20" x2="68" y2="120" stroke="#22C55E" stroke-width="5" stroke-linecap="round"/>
  <line x1="88" y1="20" x2="102" y2="16" stroke="#22C55E" stroke-width="5" stroke-linecap="round"/>
  <!-- Glass Cup -->
  <g filter="url(#ojS)">
    <!-- Liquid -->
    <polygon points="56,60 104,60 98,132 62,132" fill="url(#ojGrad)"/>
    <!-- Glass Outline -->
    <polygon points="52,48 108,48 100,136 60,136" fill="#FFFFFF" fill-opacity="0.2" stroke="#FFFFFF" stroke-width="2.5"/>
  </g>
  <!-- Orange slice on rim -->
  <circle cx="50" cy="48" r="18" fill="#F97316"/>
  <circle cx="50" cy="48" r="15" fill="#FFEDD5"/>
  <circle cx="50" cy="48" r="13" fill="#EA580C"/>
  <path d="M50 48 L50 35 M50 48 L61 41 M50 48 L61 55 M50 48 L50 61 M50 48 L39 55 M50 48 L39 41" stroke="#FFEDD5" stroke-width="1.2"/>
  <!-- Glass Sheen -->
  <line x1="62" y1="56" x2="68" y2="128" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" opacity="0.5"/>
</svg>''',

    'green-tea': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="teaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#A7F3D0"/>
      <stop offset="50%" stop-color="#34D399"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <filter id="teaS">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.18" flood-color="#064E3B"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#ECFDF5" opacity="0.65"/>
  <!-- Steam Swirls -->
  <path d="M68 40 Q72 30 68 20" stroke="#34D399" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.6"/>
  <path d="M80 42 Q86 28 80 18" stroke="#34D399" stroke-width="2.5" stroke-linecap="round" fill="none" opacity="0.7"/>
  <path d="M92 40 Q96 30 92 20" stroke="#34D399" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.6"/>
  <!-- Saucer -->
  <ellipse cx="80" cy="132" rx="54" ry="12" fill="#E2E8F0"/>
  <ellipse cx="80" cy="130" rx="48" ry="10" fill="#FFFFFF"/>
  <!-- Mug Body -->
  <g filter="url(#teaS)">
    <!-- Handle -->
    <path d="M104 68 C120 68, 120 102, 102 102" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round" fill="none"/>
    <path d="M104 68 C120 68, 120 102, 102 102" stroke="#E2E8F0" stroke-width="4" stroke-linecap="round" fill="none"/>
    <!-- Cup Exterior -->
    <path d="M48 54 L56 120 C56 124, 66 128, 80 128 C94 128, 104 124, 104 120 L112 54 Z" fill="#FFFFFF"/>
    <!-- Cup Rim Liquid -->
    <ellipse cx="80" cy="54" rx="32" ry="10" fill="url(#teaGrad)"/>
  </g>
  <!-- Floating Tea Leaf -->
  <path d="M80 54 C74 50, 68 52, 66 54 C72 56, 78 56, 80 54 Z" fill="#047857"/>
</svg>''',

    'coconut-water': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="cocoGrad" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#86EFAC"/>
      <stop offset="40%" stop-color="#22C55E"/>
      <stop offset="85%" stop-color="#15803D"/>
      <stop offset="100%" stop-color="#14532D"/>
    </radialGradient>
    <filter id="cocS">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-opacity="0.2" flood-color="#052E16"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#DCFCE7" opacity="0.6"/>
  <!-- Straw -->
  <line x1="88" y1="20" x2="76" y2="76" stroke="#EF4444" stroke-width="5" stroke-linecap="round"/>
  <line x1="88" y1="20" x2="104" y2="16" stroke="#EF4444" stroke-width="5" stroke-linecap="round"/>
  <!-- Coconut Body -->
  <g filter="url(#cocS)">
    <path d="M38 68 C34 104, 46 138, 80 138 C114 138, 126 104, 122 68 C118 56, 104 50, 80 50 C56 50, 42 56, 38 68 Z" fill="url(#cocoGrad)"/>
    <!-- Cut Top Hole -->
    <ellipse cx="80" cy="62" rx="26" ry="12" fill="#FFFFFF"/>
    <ellipse cx="80" cy="63" rx="22" ry="9" fill="#E0F2FE"/>
  </g>
  <!-- Little flower decoration -->
  <circle cx="106" cy="64" r="5" fill="#F43F5E"/>
  <circle cx="106" cy="64" r="2" fill="#FEF08A"/>
</svg>''',

    'mixed-nuts': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="almondGrad" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#FDE68A"/>
      <stop offset="40%" stop-color="#D97706"/>
      <stop offset="100%" stop-color="#78350F"/>
    </radialGradient>
    <radialGradient id="cashewGrad" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="60%" stop-color="#FEF3C7"/>
      <stop offset="100%" stop-color="#FCD34D"/>
    </radialGradient>
    <filter id="nutS">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.2" flood-color="#451A03"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF3C7" opacity="0.6"/>
  <!-- Nuts collection -->
  <g filter="url(#nutS)">
    <!-- Almond 1 -->
    <path d="M52 56 C68 44, 84 56, 80 76 C76 92, 54 94, 46 80 C40 68, 44 60, 52 56 Z" fill="url(#almondGrad)"/>
    <path d="M54 62 Q66 70 64 82" stroke="#78350F" stroke-width="1.2" fill="none" opacity="0.5"/>
    <!-- Cashew -->
    <path d="M96 60 C114 62, 122 82, 114 96 C106 108, 92 104, 94 92 C96 82, 106 82, 102 74 C98 68, 88 68, 96 60 Z" fill="url(#cashewGrad)"/>
    <!-- Walnut Half -->
    <ellipse cx="68" cy="110" rx="20" ry="16" fill="#B45309"/>
    <path d="M56 110 Q68 98 80 110 Q68 122 56 110 Z" fill="#78350F"/>
    <ellipse cx="68" cy="110" rx="5" ry="8" fill="#FDE68A" opacity="0.6"/>
    <!-- Almond 2 -->
    <path d="M98 94 C112 88, 122 102, 114 116 C108 128, 92 124, 88 114 C84 104, 90 98, 98 94 Z" fill="url(#almondGrad)"/>
  </g>
</svg>''',

    'potato-chips': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <radialGradient id="chipGrad" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#FEF08A"/>
      <stop offset="40%" stop-color="#FACC15"/>
      <stop offset="85%" stop-color="#EAB308"/>
      <stop offset="100%" stop-color="#A16207"/>
    </radialGradient>
    <filter id="chipS">
      <feDropShadow dx="0" dy="5" stdDeviation="5" flood-opacity="0.22" flood-color="#854D0E"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF9C3" opacity="0.65"/>
  <!-- Chips Stack / Pile -->
  <g filter="url(#chipS)">
    <!-- Back Chip -->
    <path d="M52 58 C74 44, 114 52, 118 76 C122 96, 92 110, 70 102 C48 94, 38 70, 52 58 Z" fill="#CA8A04" opacity="0.6"/>
    <!-- Front Chip 1 (Saddle shape) -->
    <path d="M42 78 C44 54, 84 50, 112 66 C124 74, 126 94, 108 108 C84 122, 54 118, 44 102 C38 92, 40 84, 42 78 Z" fill="url(#chipGrad)"/>
    <!-- Ripple marks -->
    <path d="M52 74 Q78 82 104 74" stroke="#A16207" stroke-width="1.8" stroke-linecap="round" fill="none" opacity="0.4"/>
    <path d="M54 88 Q80 96 106 88" stroke="#A16207" stroke-width="1.8" stroke-linecap="round" fill="none" opacity="0.4"/>
    <path d="M56 102 Q82 110 102 102" stroke="#A16207" stroke-width="1.8" stroke-linecap="round" fill="none" opacity="0.4"/>
  </g>
  <!-- Salt crystals -->
  <circle cx="70" cy="78" r="1.5" fill="#FFFFFF"/>
  <circle cx="88" cy="84" r="1.5" fill="#FFFFFF"/>
  <circle cx="64" cy="94" r="1.5" fill="#FFFFFF"/>
  <circle cx="94" cy="96" r="1.5" fill="#FFFFFF"/>
</svg>''',

    'dark-chocolate': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%">
  <defs>
    <linearGradient id="chocBar" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#582C12"/>
      <stop offset="50%" stop-color="#3B1B09"/>
      <stop offset="100%" stop-color="#241005"/>
    </linearGradient>
    <linearGradient id="goldFoil" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FDE047"/>
      <stop offset="50%" stop-color="#CA8A04"/>
      <stop offset="100%" stop-color="#854D0E"/>
    </linearGradient>
    <filter id="chocS">
      <feDropShadow dx="0" dy="6" stdDeviation="5" flood-opacity="0.25" flood-color="#241005"/>
    </filter>
  </defs>
  <circle cx="80" cy="80" r="72" fill="#FEF3C7" opacity="0.5"/>
  <!-- Gold Foil Peek -->
  <polygon points="40,88 120,72 126,134 46,140" fill="url(#goldFoil)" filter="url(#chocS)"/>
  <!-- Chocolate Bar Body -->
  <g filter="url(#chocS)">
    <polygon points="36,44 116,28 122,96 42,108" fill="url(#chocBar)"/>
    <!-- Squares Grid -->
    <!-- Row 1 -->
    <polygon points="44,48 76,42 78,66 46,70" fill="#2E1507" stroke="#6B3410" stroke-width="1.2"/>
    <polygon points="82,40 110,34 112,58 84,62" fill="#2E1507" stroke="#6B3410" stroke-width="1.2"/>
    <!-- Row 2 -->
    <polygon points="48,74 80,68 82,92 50,96" fill="#2E1507" stroke="#6B3410" stroke-width="1.2"/>
    <polygon points="86,66 114,60 116,84 88,88" fill="#2E1507" stroke="#6B3410" stroke-width="1.2"/>
  </g>
  <!-- Sheen / Highlight on edge -->
  <line x1="38" y1="44" x2="116" y2="28" stroke="#FFFFFF" stroke-width="1.5" opacity="0.4"/>
</svg>''',
}

def main():
    print(f"Generating {len(SVGS)} product SVGs into {OUTPUT_DIR}...")
    for slug, svg_code in SVGS.items():
        file_path = OUTPUT_DIR / f"{slug}.svg"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(svg_code.strip() + '\n')
        print(f"  [OK] {slug}.svg")
    print("Done generating all product SVG assets!")

if __name__ == '__main__':
    main()
