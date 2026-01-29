import { AspectRatio } from "@radix-ui/react-aspect-ratio";
import type { ReactNode } from "react";

import { ConnectionState } from "@/components/common/ConnectionState";
import { Navbar } from "@/components/Navbar/Navbar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface DisplayProps {
  wsState?: number;
  reconnectFn?: () => void;
  videoDisplay: ReactNode;
  mode: ReactNode;
  modeDescription: ReactNode;
  vmData: ReactNode;
}

export const Display = ({
  wsState,
  reconnectFn,
  videoDisplay,
  mode,
  modeDescription,
  vmData,
}: DisplayProps) => {
  return (
    <div className="flex flex-col h-screen">
      <Navbar />
      <div className="flex flex-1">
        <Card className="flex flex-1 ml-10 mr-10 mb-10 mt-3">
          <CardHeader>
            <CardTitle className="mb-2">Video Feed</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-1">
            <AspectRatio ratio={16 / 9} className="flex flex-1 h-full">
              <ConnectionState
                wsState={wsState}
                reconnectFn={reconnectFn}
                display={videoDisplay}
              />
            </AspectRatio>
          </CardContent>
        </Card>
        <Card className="flex flex-1 ml-10 mr-10 mb-10 mt-3">
          <CardHeader>
            <CardTitle className="mb-2">{mode}</CardTitle>
            <CardDescription>{modeDescription}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-1">{vmData}</CardContent>
        </Card>
      </div>
    </div>
  );
};
