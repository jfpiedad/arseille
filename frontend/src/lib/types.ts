import type {
  InboundInstruction,
  OutboundInstruction,
} from "@/components/VMSimulation/state";
import type {
  AGE_GROUP,
  VENDING_DRINKS,
  VENDING_MODE,
  WEATHER,
} from "@/lib/constants";

interface CheckpointStreamData {
  imageUrl: string;
  age: number;
  weather: Weather;
  timestamp: number;
}

interface FullSystemStreamData {
  imageUrl: string;
}

interface DetectionData {
  age: number;
  ageGroup: AgeGroup;
  weather: Weather;
}

interface TransactionData extends DetectionData {
  drink: string;
}

interface TransactionDataDisplay extends TransactionData {
  id: string;
  timestamp: string;
}

interface InboundMessage {
  type: InboundInstruction;
  detectionData?: DetectionData;
}

interface OutboundMessage {
  type: OutboundInstruction;
  transactionData?: TransactionData;
}

type AgeGroup = (typeof AGE_GROUP)[keyof typeof AGE_GROUP];
type Weather = (typeof WEATHER)[keyof typeof WEATHER];
type VendingMode = (typeof VENDING_MODE)[keyof typeof VENDING_MODE];
type VendingDrinks =
  (typeof VENDING_DRINKS)[keyof typeof VENDING_DRINKS][keyof (typeof VENDING_DRINKS)[keyof typeof VENDING_DRINKS]][number];

export {
  type CheckpointStreamData,
  type FullSystemStreamData,
  type DetectionData,
  type TransactionData,
  type TransactionDataDisplay,
  type InboundMessage,
  type OutboundMessage,
  type AgeGroup,
  type Weather,
  type VendingMode,
  type VendingDrinks,
};
