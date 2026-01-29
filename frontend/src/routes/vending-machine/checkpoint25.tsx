import { createFileRoute } from "@tanstack/react-router";
// import Kimshin from "@/assets/kimshin.jpeg";

import { Display } from "@/components/Display/Display";
import { Badge } from "@/components/ui/badge";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { useWebSocketCheckpoint } from "@/hooks/useWebSocket";
import { VENDING_MODE } from "@/lib/constants";

const Checkpoint25 = () => {
  const { wsState, reconnect, checkpointStreamData } = useWebSocketCheckpoint(
    VENDING_MODE.CHECKPOINT_25,
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
      mode="Checkpoint 25"
      modeDescription={
        <div className="flex flex-col">
          <Badge variant="secondary" className="w-1/8 h-6 text-sm mb-2">
            Description
          </Badge>
          Detects human faces in real time and highlights them with bounding
          boxes.
        </div>
      }
      vmData={
        <Empty className="text-lg flex flex-col w-full border-1 border-b-neutral-700 items-center justify-center">
          <EmptyHeader>
            <EmptyTitle>No Data / Prompts Available.</EmptyTitle>
            <EmptyDescription>
              The vending machine mode currently running does not include any
              type of detection data or prompts.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      }
    ></Display>
  );
};

export const Route = createFileRoute("/vending-machine/checkpoint25")({
  component: Checkpoint25,
});
