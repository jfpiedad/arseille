import { type ColumnDef } from "@tanstack/react-table";
import {
  CalendarClockIcon,
  CloudIcon,
  CupSodaIcon,
  IdCardIcon,
  UsersRoundIcon,
} from "lucide-react";

import type { TransactionDataDisplay } from "@/lib/types";

export const columns: ColumnDef<TransactionDataDisplay>[] = [
  {
    accessorKey: "id",
    header: () => {
      return (
        <div className="flex flex-row gap-2 items-center">
          <IdCardIcon strokeWidth={1.5} size={22} />
          <p>Transaction ID</p>
        </div>
      );
    },
    cell: ({ row }) => {
      return (
        <div className="flex">
          <span className="uppercase">{row.original.id}</span>
        </div>
      );
    },
    filterFn: "includesString",
  },
  {
    accessorKey: "drink",
    header: () => {
      return (
        <div className="flex flex-row gap-2 items-center">
          <CupSodaIcon strokeWidth={1.5} size={22} />
          <p>Drink</p>
        </div>
      );
    },
    cell: ({ row }) => {
      return (
        <div className="flex">
          <span className="capitalize">{row.original.drink}</span>
        </div>
      );
    },
  },
  {
    accessorKey: "ageGroup",
    header: () => {
      return (
        <div className="flex flex-row gap-2 items-center">
          <UsersRoundIcon strokeWidth={1.5} size={22} />
          <p>Age Group</p>
        </div>
      );
    },
    cell: ({ row }) => {
      return (
        <div className="flex">
          <span className="capitalize">{row.original.ageGroup}</span>
        </div>
      );
    },
  },
  {
    accessorKey: "weather",
    header: () => {
      return (
        <div className="flex flex-row gap-2 items-center">
          <CloudIcon strokeWidth={1.5} size={22} />
          <p>Weather</p>
        </div>
      );
    },
    cell: ({ row }) => {
      return (
        <div className="flex">
          <span className="capitalize">{row.original.weather}</span>
        </div>
      );
    },
  },
  {
    accessorKey: "timestamp",
    header: () => {
      return (
        <div className="flex flex-row gap-2 items-center">
          <CalendarClockIcon strokeWidth={1.5} size={22} />
          <p>Date & Time</p>
        </div>
      );
    },
    accessorFn: (row) =>
      new Intl.DateTimeFormat("en-GB", {
        second: "numeric",
        minute: "numeric",
        hour: "numeric",
        day: "2-digit",
        month: "short",
        year: "numeric",
        timeZone: "Asia/Manila",
      }).format(new Date(row.timestamp)),
    cell: ({ getValue }) => {
      return (
        <div className="flex">
          <span>{getValue<string>()}</span>
        </div>
      );
    },
  },
];
