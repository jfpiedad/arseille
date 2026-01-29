import { Link } from "@tanstack/react-router";
import {
  type ColumnDef,
  type PaginationState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronsLeftIcon,
  ChevronsRightIcon,
  Undo2Icon,
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
}

export const DataTable = <TData, TValue>({
  columns,
  data,
}: DataTableProps<TData, TValue>) => {
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    globalFilterFn: "includesString",
    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setPagination,
    state: {
      pagination,
    },
    defaultColumn: {
      size: 300,
    },
  });

  return (
    <div className="flex flex-col gap-4 m-10">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                return (
                  <TableHead
                    key={header.id}
                    style={{ width: header.getSize() }}
                    className="p-3"
                  >
                    <div className="flex flex-col gap-2">
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                      {header.column.getCanFilter() && (
                        <div className="w-4/5">
                          <Input
                            onChange={(e) =>
                              header.column.setFilterValue(e.target.value)
                            }
                            placeholder="Filter"
                          ></Input>
                        </div>
                      )}
                    </div>
                  </TableHead>
                );
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                data-state={row.getIsSelected() && "selected"}
                className="h-15"
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell
                    key={cell.id}
                    style={{ width: cell.column.getSize() }}
                    className="p-3"
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                <Empty className="w-1/2 justify-self-center">
                  <EmptyHeader>
                    <EmptyTitle>No Results</EmptyTitle>
                    <EmptyDescription>
                      There are no results found.
                    </EmptyDescription>
                  </EmptyHeader>
                </Empty>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      <div className="flex items-center justify-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => table.firstPage()}
          disabled={!table.getCanPreviousPage()}
        >
          <ChevronsLeftIcon strokeWidth={3} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          <ChevronLeftIcon strokeWidth={3} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          <ChevronRightIcon strokeWidth={3} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => table.lastPage()}
          disabled={!table.getCanNextPage()}
        >
          <ChevronsRightIcon strokeWidth={3} />
        </Button>

        <span className="flex items-center justify-center whitespace-nowrap gap-3">
          <p className="text-sm">Go to Page:</p>
          <Input
            placeholder="Enter page number"
            type="number"
            onChange={(e) => {
              const page = e.target.value ? Number(e.target.value) - 1 : 0;
              table.setPageIndex(Math.min(table.getPageCount() - 1, page));
            }}
          ></Input>
        </span>
      </div>
      <div className="flex justify-center text-sm opacity-50 gap-3">
        <p>
          {table.getRowCount() > 0 ? (
            <>
              Showing {table.getState().pagination.pageIndex * 10 + 1} to{" "}
              {table.getState().pagination.pageIndex * 10 +
                table.getPaginationRowModel().rows.length}{" "}
              of {table.getRowCount()} rows
            </>
          ) : (
            "No rows found."
          )}
        </p>
        <Separator orientation="vertical" />
        <p>
          {table.getPageCount() > 0 ? (
            <>
              Page {table.getState().pagination.pageIndex + 1} of{" "}
              {table.getPageCount()}
            </>
          ) : (
            "No pages found."
          )}
        </p>
      </div>
      <div className="flex justify-center">
        <Button variant="secondary" asChild className="w-35 mt-10">
          <Link to="/">
            <Undo2Icon />
            Go Back
          </Link>
        </Button>
      </div>
    </div>
  );
};
