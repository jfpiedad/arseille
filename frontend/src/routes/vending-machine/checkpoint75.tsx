import { createFileRoute } from "@tanstack/react-router";

import { Display } from "@/components/Display/Display";
import { Badge } from "@/components/ui/badge";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useWebSocketCheckpoint } from "@/hooks/useWebSocket";
import { VENDING_MODE } from "@/lib/constants";

const Checkpoint75 = () => {
  const { wsState, reconnect, checkpointStreamData } = useWebSocketCheckpoint(
    VENDING_MODE.CHECKPOINT_75,
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
      mode="Checkpoint 75"
      modeDescription={
        <div className="flex flex-col">
          <Badge variant="secondary" className="w-1/8 h-6 text-sm mb-2">
            Description
          </Badge>
          Detects human faces, displays bounding boxes, estimates the age of the
          nearest detected face, and shows current weather data alongside the
          results.
        </div>
      }
      vmData={
        <div className="flex flex-col w-full border-1 border-b-neutral-700 items-center justify-center">
          <FieldGroup className="items-center justify-center">
            <Field className="w-1/4">
              <FieldLabel htmlFor="age">Age</FieldLabel>
              <Input
                id="age"
                value={checkpointStreamData?.age ?? ""}
                disabled
              />
            </Field>
            <Field className="w-1/4">
              <FieldLabel htmlFor="weather">Weather</FieldLabel>
              <Input
                id="weather"
                value={checkpointStreamData?.weather ?? ""}
                disabled
              />
            </Field>
          </FieldGroup>
        </div>
      }
    ></Display>
  );
};

export const Route = createFileRoute("/vending-machine/checkpoint75")({
  component: Checkpoint75,
});
