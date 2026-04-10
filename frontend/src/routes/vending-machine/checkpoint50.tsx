import { createFileRoute } from "@tanstack/react-router";

import { Display } from "@/components/Display/Display";
import { Badge } from "@/components/ui/badge";
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useWebSocketCheckpoint } from "@/hooks/useWebSocket";
import { VENDING_MODE } from "@/lib/constants";

const Checkpoint50 = () => {
  const { wsState, reconnect, checkpointStreamData } = useWebSocketCheckpoint(
    VENDING_MODE.CHECKPOINT_50,
  );

  return (
    <Display
      wsState={wsState}
      reconnectFn={reconnect}
      videoDisplay={
        <img
          src={checkpointStreamData?.imageUrl}
          alt="Video Feed Image"
          className="h-full w-full object-contain"
        ></img>
      }
      mode="Checkpoint 50"
      modeDescription={
        <div className="flex flex-col">
          <Badge variant="secondary" className="w-30 text-sm h-6 mb-2">
            Description
          </Badge>
          Detects human faces, displays bounding boxes, and estimates the age of
          the nearest detected face.
        </div>
      }
      vmData={
        <div className="flex flex-col w-full border-1 border-b-neutral-700 items-center justify-center">
          <Field className="w-1/4 min-w-24">
            <FieldLabel htmlFor="age">Age</FieldLabel>
            <Input id="age" value={checkpointStreamData?.age ?? ""} disabled />
          </Field>
        </div>
      }
    ></Display>
  );
};

export const Route = createFileRoute("/vending-machine/checkpoint50")({
  component: Checkpoint50,
});
