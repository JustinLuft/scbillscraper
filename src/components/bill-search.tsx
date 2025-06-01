"use client";

import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import type { Bill } from "@/types/bill";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Search, Loader2 } from "lucide-react";

import {
  getFirestore,
  collection,
  getDocs,
  enableIndexedDbPersistence,
  query,
  orderBy,
  limit,
  startAfter,
  DocumentData,
  QueryDocumentSnapshot
} from "firebase/firestore";
import { initializeApp } from "firebase/app";

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

const firebaseConfig = {
  apiKey: "AIzaSyAZKKgAToBo50ehGotcqOFbabJ6scmW4-s",
  authDomain: "scbills-e1545.firebaseapp.com",
  projectId: "scbills-e1545",
  storageBucket: "scbills-e1545.firebasestorage.app",
  messagingSenderId: "459923968272",
  appId: "1:459923968272:web:b7a72a6162be3e7898d595",
  measurementId: "G-6L971HVB53"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

enableIndexedDbPersistence(db).catch(err => {
  if (err.code === "failed-precondition") console.warn("Persistence failed (multiple tabs)");
  else if (err.code === "unimplemented") console.warn("Persistence not supported.");
});

const PAGE_SIZE = 25;

export function BillSearch() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [fiscalImpactFilter, setFiscalImpactFilter] = useState<"all" | "yes" | "no">("all");
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const lastVisibleRef = useRef<QueryDocumentSnapshot<DocumentData> | null>(null);
  const debouncedSearch = useDebounce(searchTerm.trim().toLowerCase().replace(/^0+/, ""), 300);

  const fetchNextPage = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);

    try {
      const billsRef = collection(db, "bills");
      const q = query(
        billsRef,
        orderBy("bill_number"),
        ...(lastVisibleRef.current ? [startAfter(lastVisibleRef.current)] : []),
        limit(PAGE_SIZE)
      );

      const snapshot = await getDocs(q);

      const newBills: Bill[] = snapshot.docs.map(doc => {
        const data = doc.data();
        const rawBillNumber = String(data.bill_number || "");
        const cleanBillNumber = rawBillNumber.replace(/^0+/, "");

        const rawBillName: string = data.bill_name || "";
        const cleanBillName = rawBillName.replace(/^[SH]\*?\s*0*(\d+)/, "$1").trim();

        const chamber: "Senate" | "House" | "Unknown" =
          rawBillName.startsWith("S") ? "Senate" :
          rawBillName.startsWith("H") ? "House" :
          "Unknown";

        return {
          id: doc.id,
          bill_name: cleanBillName,
          bill_number: cleanBillNumber,
          bill_summary: data.bill_summary || "N/A",
          fiscal_impact: data.fiscal_impact === "yes" ? "yes" : "no",
          current_status: data.current_status || "N/A",
          bill_url: data.bill_url || "",
          session: data.session || "Unknown",
          chamber
        };
      });

      setBills(prev => {
        const existingKeys = new Set(prev.map(b => `${b.chamber}-${b.bill_number}`));
        const uniqueNewBills = newBills.filter(b => !existingKeys.has(`${b.chamber}-${b.bill_number}`));
        return [...prev, ...uniqueNewBills];
      });

      if (newBills.length > 0) {
        lastVisibleRef.current = snapshot.docs[snapshot.docs.length - 1];
        if (newBills.length < PAGE_SIZE) setHasMore(false);
      } else {
        setHasMore(false);
      }
    } catch (error) {
      console.error("Error fetching bills:", error);
    } finally {
      setLoading(false);
    }
  }, [loading, hasMore]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (hasMore && !loading) fetchNextPage();
    }, 100);
    return () => clearInterval(interval);
  }, [hasMore, loading, fetchNextPage]);

  const filteredBills = useMemo(() => {
    return bills
      .filter(bill => {
        const nameMatch = bill.bill_name.toLowerCase().includes(debouncedSearch);
        const numberMatch = bill.bill_number.includes(debouncedSearch);
        const fiscalMatch = fiscalImpactFilter === "all" || bill.fiscal_impact === fiscalImpactFilter;
        return (nameMatch || numberMatch) && fiscalMatch;
      })
      .sort((a, b) => Number(a.bill_number) - Number(b.bill_number));
  }, [bills, debouncedSearch, fiscalImpactFilter]);

  return (
    <div className="container mx-auto px-4 md:px-6 lg:px-8">
      <Card className="mb-6 bg-gray-100 p-6">
        <CardHeader className="py-4">
          <CardTitle className="text-3xl font-extrabold flex items-center gap-2 text-gray-800">
            <Search className="h-6 w-6 text-black" /> Search South Carolina Bills
          </CardTitle>
          <CardDescription className="text-gray-600">
            Search by bill number or name, and filter by fiscal impact.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <Input
              className="border-gray-300 rounded-md placeholder:text-gray-400 bg-gray-200 dark:text-black focus-visible:ring-black"
              placeholder="Enter bill number or name..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
            <Select
              value={fiscalImpactFilter}
              onValueChange={value => setFiscalImpactFilter(value as "all" | "yes" | "no")}
            >
              <SelectTrigger className="w-full md:w-[180px] dark:text-white">
                <SelectValue placeholder="Filter by fiscal impact" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Fiscal Impacts</SelectItem>
                <SelectItem value="yes">Has Fiscal Impact</SelectItem>
                <SelectItem value="no">No Fiscal Impact</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <ScrollArea className="h-[calc(100vh-250px)] rounded-md border">
        <div className="p-4">
          {loading && bills.length === 0 ? (
            <div className="flex justify-center items-center h-full">
              <Loader2 className="animate-spin h-10 w-10 text-black dark:text-white" />
            </div>
          ) : filteredBills.length > 0 ? (
            <>
              {filteredBills.map(bill => (
                <Card key={`${bill.chamber}-${bill.bill_number}`} className="mb-4 bg-white border border-gray-300 p-4 rounded-md hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <CardTitle className="text-lg font-bold text-gray-700">
                      <a
                        href={bill.bill_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline"
                      >
                        {bill.bill_name} (Bill #{bill.bill_number})
                      </a>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-2 italic">{bill.current_status}</p>
                    <p className="text-sm text-gray-600 mb-3">{bill.bill_summary}</p>
                    <p className="text-sm font-medium text-gray-700">
                      Fiscal Impact:{" "}
                      <span className={bill.fiscal_impact === "yes" ? "text-red-600 font-semibold" : "text-green-600 font-semibold"}>
                        {bill.fiscal_impact === "yes" ? "Yes" : "No"}
                      </span>
                    </p>
                    <p className="text-sm font-medium text-gray-700">
                      Chamber:{" "}
                      <span className={
                        bill.chamber === "Senate" ? "text-blue-600 font-semibold" :
                        bill.chamber === "House" ? "text-green-600 font-semibold" :
                        "text-gray-600"
                      }>
                        {bill.chamber}
                      </span>
                    </p>
                  </CardContent>
                </Card>
              ))}
              {!hasMore && (
                <p className="text-center text-sm text-gray-400 mt-4">End of results.</p>
              )}
            </>
          ) : (
            <p className="text-center text-muted-foreground py-10">No bills found matching your criteria.</p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
