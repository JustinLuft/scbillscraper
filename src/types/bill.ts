export interface Bill {
  id: string;
  bill_name: string;
  bill_number: string;
  bill_summary: string;
  fiscal_impact: string;
  current_status: string;
  bill_url: string;
  session: string;
  chamber: "Senate" | "House" | "Unknown"; 
}
