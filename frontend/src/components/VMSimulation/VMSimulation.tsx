import { MousePointer2Icon } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Field,
  FieldContent,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
  FieldTitle,
} from "@/components/ui/field";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Spinner } from "@/components/ui/spinner";
import {
  INBOUND_INSTRUCTION,
  OUTBOUND_INSTRUCTION,
} from "@/components/VMSimulation/state";
import { VENDING_DRINKS } from "@/lib/constants";
import type {
  DetectionData,
  InboundMessage,
  OutboundMessage,
  VendingDrinks,
} from "@/lib/types";

type MessageFn = (message: OutboundMessage) => void;

interface VMSimulationProps {
  simulationState: InboundMessage;
  sendMessage: MessageFn;
}

const _render = (simulationState: InboundMessage, sendMessage: MessageFn) => {
  switch (simulationState.type) {
    case INBOUND_INSTRUCTION.RESET:
      return <Initial sendMessage={sendMessage} />;
    case INBOUND_INSTRUCTION.PROCESSING_USER:
      return <ProcessingUser />;
    case INBOUND_INSTRUCTION.DISPLAY_DRINKS:
      return (
        <DisplayDrinks
          sendMessage={sendMessage}
          simulationState={simulationState}
        />
      );
    case INBOUND_INSTRUCTION.PREPARING_DRINK:
      return <PreparingDrink />;
    case INBOUND_INSTRUCTION.DRINK_READY:
      return <DrinkReady sendMessage={sendMessage} />;
    default:
      return <div>Something went wrong. Sad.</div>;
  }
};

function removeItem<T>(arr: T[], value: T): T[] {
  const index = arr.indexOf(value);
  if (index > -1) {
    arr.splice(index, 1);
  }
  return arr;
}

const _getDrinks = (
  data: DetectionData,
  recommended = false,
): readonly VendingDrinks[] => {
  const ageGroup = data.ageGroup;
  const weather = data.weather;

  if (recommended) {
    return VENDING_DRINKS[ageGroup][weather];
  } else {
    const drinks: VendingDrinks[] = [];

    for (const ageKey in VENDING_DRINKS) {
      const tempAgeGroup = ageKey as keyof typeof VENDING_DRINKS;
      for (const weatherKey in VENDING_DRINKS[tempAgeGroup]) {
        const tempWeather =
          weatherKey as keyof (typeof VENDING_DRINKS)[typeof tempAgeGroup];

        if (ageGroup == tempAgeGroup && weather == tempWeather) continue;

        for (const drink of VENDING_DRINKS[tempAgeGroup][tempWeather])
          drinks.push(drink);
      }
    }

    const drinksDisplay = Array.from(new Set(drinks));
    VENDING_DRINKS[ageGroup][weather].forEach((value) => {
      removeItem(drinksDisplay, value);
    });

    return drinksDisplay;
  }
};

export const VMSimulation = ({
  simulationState,
  sendMessage,
}: VMSimulationProps) => {
  return (
    <div className="flex flex-1 border-1 p-5">
      {_render(simulationState, sendMessage)}
    </div>
  );
};

const Initial = ({ sendMessage }: { sendMessage: MessageFn }) => {
  return (
    <div className="flex flex-1 items-center justify-center">
      <Button
        variant="outline"
        size="lg"
        onClick={() => sendMessage({ type: OUTBOUND_INSTRUCTION.START_ORDER })}
      >
        Order <MousePointer2Icon />
      </Button>
    </div>
  );
};

const ProcessingUser = () => {
  return (
    <div className="flex flex-1 ">
      <div className="flex flex-1 flex-row gap-3 items-center justify-center">
        <h2>Processing</h2>
        <Spinner className="size-10" />
      </div>
    </div>
  );
};

const DisplayDrinks = ({
  sendMessage,
  simulationState,
}: {
  sendMessage: MessageFn;
  simulationState: InboundMessage;
}) => {
  const [selectedDrink, setSelectedDrink] = useState("");
  const [showAllDrinks, setShowAllDrinks] = useState(false);

  return (
    <div className="flex flex-1">
      <FieldGroup>
        <FieldSet>
          <div className="flex flex-row gap-5 items-center capitalize -mb-3">
            <h4>Vending Machine</h4>
            <Badge variant="secondary" className="size-6 w-1/8">
              {simulationState.detectionData?.ageGroup}
            </Badge>
            <Badge variant="secondary" className="size-6 w-1/8">
              {simulationState.detectionData?.weather}
            </Badge>
            <div className="ml-auto">
              <Field orientation="horizontal">
                <Checkbox
                  id="show-all-drinks"
                  name="show-all-drinks"
                  onCheckedChange={(value) => setShowAllDrinks(!!value)}
                />
                <Label htmlFor="show-all-drinks">Show all drinks</Label>
              </Field>
            </div>
          </div>
        </FieldSet>
        <FieldSet>
          {showAllDrinks && <FieldLegend>Drinks Menu</FieldLegend>}
          <RadioGroup
            className="capitalize"
            onValueChange={(value) => setSelectedDrink(value)}
          >
            <div className="grid grid-cols-3 gap-2">
              {simulationState.detectionData &&
                showAllDrinks &&
                _getDrinks(simulationState.detectionData).map((drink) => (
                  <FieldLabel htmlFor={drink} key={drink}>
                    <Field orientation="horizontal">
                      <FieldContent>
                        <FieldTitle>{drink}</FieldTitle>
                      </FieldContent>
                      <RadioGroupItem value={drink} id={drink} />
                    </Field>
                  </FieldLabel>
                ))}
            </div>
            <FieldLegend className="mb-1">Recommended Drinks</FieldLegend>
            <FieldDescription className="lowercase first-letter:uppercase">
              The recommended drinks are based on the age group of the user and
              the current weather conditions.
            </FieldDescription>
            <div className="grid grid-cols-2 gap-10 pl-5 pr-5 pb-5">
              {simulationState.detectionData &&
                _getDrinks(simulationState.detectionData, true).map((drink) => (
                  <FieldLabel htmlFor={drink} key={drink}>
                    <Field orientation="horizontal">
                      <FieldContent>
                        <FieldTitle>{drink}</FieldTitle>
                      </FieldContent>
                      <RadioGroupItem value={drink} id={drink} />
                    </Field>
                  </FieldLabel>
                ))}
            </div>
          </RadioGroup>
          <div className="flex flex-row gap-5 pl-20 pr-20">
            <Field>
              <Button
                variant="outline"
                disabled={!selectedDrink}
                onClick={() =>
                  sendMessage({
                    type: OUTBOUND_INSTRUCTION.VEND,
                    transactionData: {
                      age: simulationState.detectionData?.age ?? -1,
                      ageGroup:
                        simulationState.detectionData?.ageGroup ?? "child",
                      weather: simulationState.detectionData?.weather ?? "cold",
                      drink: selectedDrink,
                    },
                  })
                }
              >
                Vend
              </Button>
            </Field>
            <Field>
              <Button
                variant="outline"
                onClick={() =>
                  sendMessage({ type: OUTBOUND_INSTRUCTION.CANCEL })
                }
              >
                Cancel
              </Button>
            </Field>
          </div>
        </FieldSet>
      </FieldGroup>
    </div>
  );
};

const PreparingDrink = () => {
  return (
    <div className="flex flex-1 ">
      <div className="flex flex-1 flex-row gap-3 items-center justify-center">
        <h2>Preparing</h2>
        <Spinner className="size-10" />
      </div>
    </div>
  );
};

const DrinkReady = ({ sendMessage }: { sendMessage: MessageFn }) => {
  return (
    <div className="flex flex-1 ">
      <div className="flex flex-1 flex-col gap-3 items-center justify-center">
        <h2>Your drink is ready.</h2>
        <Button
          variant="outline"
          onClick={() => sendMessage({ type: OUTBOUND_INSTRUCTION.CANCEL })}
        >
          Take
        </Button>
      </div>
    </div>
  );
};
