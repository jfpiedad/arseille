import { Link } from "@tanstack/react-router";
import { Undo2Icon } from "lucide-react";

import { Button } from "@/components/ui/button";

export const GoBack = () => {
  return (
    <Button variant="secondary" asChild className="w-35 mt-10">
      <Link to="/">
        <Undo2Icon />
        Go Back
      </Link>
    </Button>
  );
};
