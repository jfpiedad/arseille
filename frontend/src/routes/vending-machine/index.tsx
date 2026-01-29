import { createFileRoute } from "@tanstack/react-router";

import { Display } from "@/components/Display/Display";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";

const VendingIndex = () => {
  return (
    <Display
      videoDisplay={
        <Empty className="text-lg flex flex-col w-full border-1 items-center justify-center">
          <EmptyHeader>
            <EmptyTitle>No Video Feed Available.</EmptyTitle>
            <EmptyDescription>
              Select a vending machine mode with the button on the top.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      }
      mode="No mode selected"
      modeDescription=""
      vmData={
        <Empty className="text-lg flex flex-col w-full border-1items-center justify-center">
          <EmptyHeader>
            <EmptyTitle>No Data / Prompts Available.</EmptyTitle>
            <EmptyDescription>
              Select a vending machine mode with the button on the top.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      }
    ></Display>
  );
};

export const Route = createFileRoute("/vending-machine/")({
  component: VendingIndex,
});
