import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { CARD_SIZES, type CardSizeKey } from '../config';

interface SettingsStore {
  baseCardSize: CardSizeKey;
  cardScale: number;
  
  setBaseCardSize: (size: CardSizeKey) => void;
  setCardScale: (scale: number) => void;
  getCardHeight: () => number;
  getCardWidth: () => number;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      baseCardSize: 'sm',
      cardScale: 100,

      setBaseCardSize: (size: CardSizeKey) => {
        set({ baseCardSize: size });
      },

      setCardScale: (scale: number) => {
        const clampedScale = Math.min(150, Math.max(50, scale));
        set({ cardScale: clampedScale });
      },

      getCardHeight: () => {
        const { baseCardSize, cardScale } = get();
        return CARD_SIZES[baseCardSize].height * (cardScale / 100);
      },

      getCardWidth: () => {
        const { baseCardSize, cardScale } = get();
        return CARD_SIZES[baseCardSize].width * (cardScale / 100);
      },
    }),
    {
      name: 'commander-settings',
    }
  )
);
