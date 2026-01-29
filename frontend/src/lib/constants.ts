const AGE_GROUP = {
  CHILD: "child",
  TEEN: "teen",
  ADULT: "adult",
  SENIOR: "senior",
} as const;

const WEATHER = {
  COLD: "cold",
  MODERATE: "moderate",
  HOT: "hot",
} as const;

const VENDING_MODE = {
  CHECKPOINT_25: 1,
  CHECKPOINT_50: 2,
  CHECKPOINT_75: 3,
  FULL_SYSTEM: 4,
} as const;

const VENDING_DRINKS = {
  child: {
    cold: ["warm milk", "hot chocolate"],
    moderate: ["water", "fruit smoothies"],
    hot: ["juice", "flavored milk"],
  },
  teen: {
    cold: ["hot chocolate", "tea"],
    moderate: ["energy drinks", "flavored water"],
    hot: ["soda", "iced tea"],
  },
  adult: {
    cold: ["coffee", "tea"],
    moderate: ["herbal tea", "sparkling water"],
    hot: ["iced coffee", "soft drinks"],
  },
  senior: {
    cold: ["herbal tea", "warm water"],
    moderate: ["green tea", "fruit juice"],
    hot: ["water", "iced tea"],
  },
} as const;

export { AGE_GROUP, WEATHER, VENDING_MODE, VENDING_DRINKS };
