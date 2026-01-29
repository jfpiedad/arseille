import { Link } from "@tanstack/react-router";
import { ArrowLeftIcon, MonitorCogIcon, RefreshCwIcon } from "lucide-react";

import { ModeToggle } from "@/components/mode-toggle";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export const Navbar = () => {
  return (
    <div className="flex flex-row items-center p-3">
      <div className="flex-1">
        <Button variant="outline" asChild>
          <Link to="/">
            <ArrowLeftIcon />
            Return
          </Link>
        </Button>
      </div>
      <div className="flex-1 text-center">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="mr-5 w-40">
              <MonitorCogIcon />
              Select Mode
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-55" align="start">
            <DropdownMenuGroup>
              <DropdownMenuLabel className="text-xs opacity-65">
                Select Mode
              </DropdownMenuLabel>
              <DropdownMenuItem asChild>
                <Link to="/vending-machine/checkpoint25">Checkpoint 25</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/vending-machine/checkpoint50">Checkpoint 50</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/vending-machine/checkpoint75">Checkpoint 75</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/vending-machine/full-system">Full System</Link>
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
        <Button variant="outline" asChild className="ml-5 w-40">
          <Link to="/vending-machine">
            <RefreshCwIcon />
            Reset
          </Link>
        </Button>
      </div>
      <div className="flex-1 text-end">
        <ModeToggle />
      </div>
    </div>
  );
};
