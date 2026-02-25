export const CARD_SIZES = {
  xs: { width: 103, height: 144 },
  sm: { width: 114, height: 160 },
  md: { width: 172, height: 240 },
  lg: { width: 229, height: 320 },
} as const;

export type CardSizeKey = keyof typeof CARD_SIZES;

export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || 'http://localhost:8000/ws',
} as const;
