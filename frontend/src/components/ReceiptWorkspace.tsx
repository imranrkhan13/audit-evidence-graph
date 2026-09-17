import { createContext, useContext, useEffect, useState } from "react";
import type { Dispatch, ReactNode, SetStateAction } from "react";
import type { ReceiptRecord } from "../receipts";

const Context = createContext<{ records: ReceiptRecord[]; setRecords: Dispatch<SetStateAction<ReceiptRecord[]>> } | null>(null);
export function ReceiptWorkspace({ children }: { children: ReactNode }) {
  const [records, setRecords] = useState<ReceiptRecord[]>([]);
  useEffect(() => {
    if (!records.length) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [records.length]);
  return <Context.Provider value={{records,setRecords}}>{children}</Context.Provider>;
}
export function useReceipts() {
  const value = useContext(Context);
  if (!value) throw new Error("Receipt workspace missing");
  return value;
}
