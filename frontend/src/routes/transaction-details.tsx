import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { getTransactions } from "@/api/transactionApi";
import { DataTable } from "@/components/common/DataTable";
import { GoBack } from "@/components/common/GoBack";
import { columns } from "@/components/Transaction/columns";
import { Spinner } from "@/components/ui/spinner";

const TransactionDetails = () => {
  const { data, isError, isPending, error } = useQuery({
    queryKey: ["transaction"],
    queryFn: getTransactions,
  });

  if (isPending) {
    return (
      <div className="flex flex-row h-screen justify-center items-center gap-5">
        <h2>Fetching Data</h2>
        <Spinner className="size-10" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col h-screen justify-center items-center gap-5">
        <h2>{error.message}</h2>
        <GoBack />
      </div>
    );
  }

  return (
    <div className="flex h-screen justify-center">
      {data ? <DataTable columns={columns} data={data} /> : "Empty Data"}
    </div>
  );
};
export const Route = createFileRoute("/transaction-details")({
  component: TransactionDetails,
});
