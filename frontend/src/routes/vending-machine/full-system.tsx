import { AspectRatio } from "@radix-ui/react-aspect-ratio";
import { createFileRoute } from "@tanstack/react-router";

import { ConnectionState } from "@/components/common/ConnectionState";
import { Navbar } from "@/components/Navbar/Navbar";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { VMSimulation } from "@/components/VMSimulation/VMSimulation";
import {
  useWebSocketFullSystem,
  useWebSocketSimulation,
} from "@/hooks/useWebSocket";

const FullSystemStream = () => {
  const { wsState, reconnect, fullSystemStreamData } = useWebSocketFullSystem();

  return (
    <Card className="flex flex-1 ml-10 mr-10 mb-10 mt-3">
      <CardHeader>
        <CardTitle className="mb-2">Video Feed</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-1">
        <AspectRatio ratio={16 / 9} className="flex flex-1 h-full">
          <ConnectionState
            wsState={wsState}
            reconnectFn={reconnect}
            display={
              <img
                src={fullSystemStreamData?.imageUrl}
                alt="Video Feed Image"
                className="h-full w-full object-contain"
              ></img>
            }
          />
        </AspectRatio>
      </CardContent>
    </Card>
  );
};

const FullSystemSimulation = () => {
  const { wsState, reconnect, simulationState, sendMessage } =
    useWebSocketSimulation();

  return (
    <Card className="flex flex-1 ml-10 mr-10 mb-10 mt-3">
      <CardHeader>
        <CardTitle className="mb-2">Full System</CardTitle>
        <CardDescription>
          <div className="flex flex-col">
            <Badge variant="secondary" className="w-1/8 h-6 text-sm mb-2">
              Description
            </Badge>
            Functions similarly like a real vending machine but with image
            processing capabilities.
          </div>
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-1">
        <ConnectionState
          wsState={wsState}
          reconnectFn={reconnect}
          display={
            <VMSimulation
              simulationState={simulationState}
              sendMessage={sendMessage}
            />
          }
        />
      </CardContent>
    </Card>
  );
};

const FullSystem = () => {
  return (
    <div className="flex flex-col h-screen">
      <Navbar />
      <div className="flex flex-1">
        <FullSystemStream />
        <FullSystemSimulation />
      </div>
    </div>
  );
};

export const Route = createFileRoute("/vending-machine/full-system")({
  component: FullSystem,
});
