import { RefreshCwIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Spinner } from "@/components/ui/spinner";

interface ConnectionStateProps {
  wsState: number | undefined;
  reconnectFn?: () => void;
  display: ReactNode;
}

const _render = (
  wsState: number | undefined,
  reconnectFn: (() => void) | undefined,
  display: ReactNode,
) => {
  switch (wsState) {
    case WebSocket.CONNECTING:
      return (
        <div className="flex flex-1 ">
          <div className="flex flex-1 flex-row gap-3 items-center justify-center">
            <h2>Connecting</h2>
            <Spinner className="size-10" />
          </div>
        </div>
      );
    case WebSocket.OPEN:
      return display;
    case WebSocket.CLOSED:
      return (
        <div className="flex flex-1">
          <Empty className="text-lg flex flex-col w-full border-1 border-b-neutral-700 items-center justify-center">
            <EmptyHeader>
              <EmptyTitle>Vending Machine Is Busy</EmptyTitle>
              <EmptyDescription>
                The vending machine can only run one mode at a time.
              </EmptyDescription>
              <EmptyContent className="flex-row justify-center gap-2">
                <Button variant="outline" onClick={reconnectFn}>
                  <span className="hidden sm:block">Try Again</span>{" "}
                  <RefreshCwIcon />
                </Button>
              </EmptyContent>
            </EmptyHeader>
          </Empty>
        </div>
      );
    default:
      return display;
  }
};
export const ConnectionState = ({
  wsState,
  reconnectFn,
  display,
}: ConnectionStateProps) => {
  return (
    <div className="flex flex-1">{_render(wsState, reconnectFn, display)}</div>
  );
};
