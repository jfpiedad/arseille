const INBOUND_INSTRUCTION = {
  PROCESSING_USER: "processing_user",
  DISPLAY_DRINKS: "display_drinks",
  PREPARING_DRINK: "preparing_drink",
  DRINK_READY: "drink_ready",
  RESET: "reset",
} as const;

const OUTBOUND_INSTRUCTION = {
  START_ORDER: "start_order",
  VEND: "vend",
  TAKE_DRINK: "take_drink",
  CANCEL: "cancel",
} as const;

type InboundInstruction =
  (typeof INBOUND_INSTRUCTION)[keyof typeof INBOUND_INSTRUCTION];

type OutboundInstruction =
  (typeof OUTBOUND_INSTRUCTION)[keyof typeof OUTBOUND_INSTRUCTION];

export {
  INBOUND_INSTRUCTION,
  OUTBOUND_INSTRUCTION,
  type InboundInstruction,
  type OutboundInstruction,
};
