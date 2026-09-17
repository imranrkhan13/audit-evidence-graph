export type Amount = string | null;
export interface ReceiptItem { description: string; quantity: Amount; unit_price: Amount; amount: Amount }
export interface ReceiptData {
  receipt_detected: boolean; merchant: string | null; receipt_number: string | null;
  date: string | null; currency: string | null; subtotal: Amount; tax: Amount;
  tip: Amount; discount: Amount; total: Amount; items: ReceiptItem[];
  warnings: string[]; source_text: string;
}
export interface ReceiptResult { receipt: ReceiptData; file_sha256: string; provider: string; stored_on_server: boolean }
export interface ReceiptRecord {
  id: string; filename: string; file: File; extractedAt: string; original: ReceiptData;
  edited: ReceiptData; fingerprint: string; reviewed: boolean; expected: string;
}
export type ReceiptCheck = { label: string; status: "pass" | "review" | "unknown"; detail: string };
const number = (value: Amount) => value !== null && value.trim() !== "" && Number.isFinite(Number(value)) ? Number(value) : null;
const round = (value: number) => Math.round((value + Number.EPSILON) * 100) / 100;

export function receiptChecks(data: ReceiptData, expected = ""): ReceiptCheck[] {
  const checks: ReceiptCheck[] = [];
  const total = number(data.total), subtotal = number(data.subtotal);
  const missing = [!data.merchant && "store name", !data.date && "date", total === null && "total", !data.currency && "currency"].filter(Boolean);
  checks.push({ label: "Key details", status: missing.length ? "review" : "pass", detail: missing.length ? `Check the missing ${missing.join(", ")}.` : "Store, date, total and currency are present. Check them against the original." });
  const compare = (label: string, calculated: number, printed: number) => {
    const difference = round(calculated - printed);
    checks.push({label, status: Math.abs(difference) <= 0.01 ? "pass" : "review", detail: Math.abs(difference) <= 0.01 ? "Amounts agree within 0.01." : `Difference: ${difference.toFixed(2)} ${data.currency || "(currency unconfirmed)"}. Check the original receipt.`});
  };
  if (total !== null && subtotal !== null) {
    compare("Subtotal to total", subtotal + (number(data.tax) ?? 0) + (number(data.tip) ?? 0) - (number(data.discount) ?? 0), total);
  } else checks.push({label:"Subtotal to total", status:"unknown", detail:"A subtotal and total are needed. Blank tax, tip and discount count as zero in this comparison."});
  const amounts = data.items.map(item => number(item.amount));
  if (subtotal !== null && amounts.length && amounts.every(amount => amount !== null)) compare("Line items to subtotal", amounts.reduce<number>((sum, amount) => sum + (amount ?? 0), 0), subtotal);
  else checks.push({label:"Line items to subtotal", status:"unknown", detail:"A subtotal and an amount for every line item are needed."});
  if (expected.trim()) {
    const target = number(expected);
    if (total !== null && target !== null) compare("Your expected amount", total, target);
    else checks.push({label:"Your expected amount", status:"unknown", detail:"Enter a valid amount and check the extracted total."});
  }
  return checks;
}

export function receiptExport(record: ReceiptRecord) {
  return { source: "Uploaded receipt", filename: record.filename, file_sha256: record.fingerprint,
    provider: "Interfaze", extracted_at: record.extractedAt, reviewed_by_user: record.reviewed,
    original_extraction: record.original, corrected_fields: record.edited,
    expected_amount: record.expected || null, checks: receiptChecks(record.edited, record.expected),
    note: "AI extraction reviewed in a browser. Arithmetic checks are not an audit opinion. No independent ledger was connected." };
}

export function receiptCsv(records: ReceiptRecord[]) {
  // Prevent spreadsheet software from treating extracted text as a formula.
  const cell = (value: unknown) => {
    let text = String(value ?? "");
    if (/^[\s]*[=+\-@\t\r]/.test(text)) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  };
  const rows = [["File", "Store", "Receipt number", "Date", "Currency", "Subtotal", "Tax", "Tip", "Discount", "Total", "Reviewed"],
    ...records.map(r => [r.filename,r.edited.merchant,r.edited.receipt_number,r.edited.date,r.edited.currency,r.edited.subtotal,r.edited.tax,r.edited.tip,r.edited.discount,r.edited.total,r.reviewed ? "Yes" : "No"])];
  return rows.map(row => row.map(cell).join(",")).join("\r\n");
}
