import { useEffect, useRef, useState } from "react";

import {
  INBOUND_INSTRUCTION,
  OUTBOUND_INSTRUCTION,
} from "@/components/VMSimulation/state";
import { checkpointStreamParser, fullSystemStreamParser } from "@/lib/parser";
import {
  type CheckpointStreamData,
  type FullSystemStreamData,
  type InboundMessage,
  type OutboundMessage,
} from "@/lib/types";

const BASE_URL = "ws://127.0.0.1:8000";
const CHECKPOINT = 1;
const FULL_SYSTEM = 2;

const useWebSocketStream = (url: string, runType: number) => {
  const [wsState, setWsState] = useState<number>(WebSocket.CONNECTING);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  const [checkpointStreamData, setCheckpointStreamData] =
    useState<CheckpointStreamData>();
  const [fullSystemStreamData, setFullSystemStreamData] =
    useState<FullSystemStreamData>();

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.binaryType = "arraybuffer";

    ws.addEventListener("close", () => {
      console.log("WebSocket connection is disconnected.");
      setWsState(WebSocket.CLOSED);
    });

    ws.addEventListener("open", () => {
      console.log("WebSocket connection is open.");
      setWsState(WebSocket.OPEN);
    });

    ws.addEventListener("error", () => {
      setWsState(WebSocket.CLOSED);
    });

    let processing = false;

    ws.addEventListener("message", (event: MessageEvent<ArrayBuffer>) => {
      if (processing) return;
      processing = true;

      try {
        if (runType == CHECKPOINT) {
          checkpointStreamParser(event, setCheckpointStreamData);
        } else {
          fullSystemStreamParser(event, setFullSystemStreamData);
        }
      } catch (error) {
        console.error(`Error parsing binary message: ${String(error)}`);
      } finally {
        processing = false;
      }
    });

    return () => {
      ws.close();
      setWsState(WebSocket.CONNECTING);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, reconnectAttempt]);

  const reconnect = () => setReconnectAttempt((prev) => prev + 1);

  return {
    wsState,
    reconnect,
    checkpointStreamData,
    fullSystemStreamData,
  };
};

const useWebSocketCheckpoint = (mode: number | string) => {
  const url = `${BASE_URL}/vending-machine/checkpoint?mode=${mode}`;
  const { wsState, reconnect, checkpointStreamData } = useWebSocketStream(
    url,
    CHECKPOINT,
  );

  return {
    wsState,
    reconnect,
    checkpointStreamData,
  };
};

const useWebSocketFullSystem = () => {
  const url = `${BASE_URL}/vending-machine/camera-stream`;
  const { wsState, reconnect, fullSystemStreamData } = useWebSocketStream(
    url,
    FULL_SYSTEM,
  );

  return {
    wsState,
    reconnect,
    fullSystemStreamData,
  };
};

const useWebSocketSimulation = () => {
  const url = `${BASE_URL}/vending-machine/full-system`;
  const [wsState, setWsState] = useState<number>(WebSocket.CONNECTING);
  const [simulationState, setSimulationState] = useState<InboundMessage>({
    type: INBOUND_INSTRUCTION.RESET,
    detectionData: { age: -1, ageGroup: "adult", weather: "hot" },
  });
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  const client = useRef<WebSocket>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    client.current = ws;

    ws.addEventListener("close", () => {
      console.log("WebSocket connection is disconnected.");
      setWsState(WebSocket.CLOSED);
    });

    ws.addEventListener("open", () => {
      console.log("WebSocket connection is open.");
      sendMessage({ type: OUTBOUND_INSTRUCTION.CANCEL }); // Initial signal that its ready.
      setWsState(WebSocket.OPEN);
    });

    ws.addEventListener("error", () => {
      setWsState(WebSocket.CLOSED);
    });

    ws.addEventListener("message", (event: MessageEvent<string>) => {
      const message = JSON.parse(event.data) as InboundMessage;
      setSimulationState({
        type: message.type,
        detectionData: message.detectionData,
      });
    });

    return () => {
      ws.close();
      setWsState(WebSocket.CONNECTING);
    };
  }, [url, reconnectAttempt]);

  const reconnect = () => setReconnectAttempt((prev) => prev + 1);
  const sendMessage = (message: OutboundMessage) => {
    if (client.current) {
      client.current.send(JSON.stringify(message));
    }
  };

  return {
    wsState,
    simulationState,
    reconnect,
    sendMessage,
  };
};

export {
  useWebSocketCheckpoint,
  useWebSocketFullSystem,
  useWebSocketSimulation,
};
