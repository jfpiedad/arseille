import { Link, createFileRoute } from "@tanstack/react-router";
import { MonitorCogIcon, NotebookTextIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

const Index = () => {
  return (
    <div className="flex flex-1 h-screen items-center justify-center">
      <div className="flex flex-col gap-2">
        <h1>ARSEILLE</h1>
        <h2>Image Processing-Based Vending Machine</h2>
        <div className="flex flex-row items-center justify-center gap-10 mt-10">
          <Button variant="secondary" size="lg" className="p-6" asChild>
            <Link to="/vending-machine">
              <MonitorCogIcon />
              Vending Machine
            </Link>
          </Button>
          <Button variant="secondary" size="lg" className="p-6" asChild>
            <Link to="/transaction-details">
              <NotebookTextIcon />
              Transaction Details
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/")({
  component: Index,
});
