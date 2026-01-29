import axios from "axios";

import type { TransactionDataDisplay } from "@/lib/types";

const BASE_URL = "http://127.0.0.1:8000/vending-machine/transactions";

const getTransactions = async (): Promise<TransactionDataDisplay[]> => {
  const response = await axios.get<TransactionDataDisplay[]>(BASE_URL);
  return response.data;
};

export { getTransactions };
