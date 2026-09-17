import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
const source=readFileSync(new URL('../src/receipts.ts',import.meta.url),'utf8');
const {outputText}=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2020}});
const {receiptChecks,receiptCsv,receiptExport}=await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
const receipt={merchant:'Example Cafe',date:'2026-09-17',currency:'USD',subtotal:'10',tax:'1',tip:null,discount:null,total:'11',items:[{description:'Coffee',amount:'10'}],warnings:[]};
test('checks compare extracted amounts and expected total',()=>{
  assert.ok(receiptChecks(receipt,'11').every(c=>c.status==='pass'));
  assert.equal(receiptChecks({...receipt,total:'12'},'11').filter(c=>c.status==='review').length,2);
});
test('unknown amounts are not interpreted as zero or a successful check',()=>{
  const checks=receiptChecks({...receipt,total:null,subtotal:null,currency:null,items:[{amount:null}]});
  assert.equal(checks[0].status,'review');
  assert.equal(checks[1].status,'unknown');
  assert.equal(checks[2].status,'unknown');
});
test('tax, tip and discount use correct signs',()=>{
  assert.equal(receiptChecks({...receipt,tip:'2',discount:'3',total:'10'})[1].status,'pass');
});
test('CSV escapes formulas, quotes and newlines',()=>{
  const csv=receiptCsv([{filename:'=HYPERLINK("bad")',edited:{...receipt,merchant:'Cafe, "hello"\nworld'},reviewed:false}]);
  assert.ok(csv.includes('"\'=HYPERLINK(""bad"")"'));
  assert.ok(csv.includes('"Cafe, ""hello""\nworld"'));
});
test('export preserves original extraction alongside corrections',()=>{
  const record={filename:'receipt.png',fingerprint:'abc',extractedAt:'now',reviewed:true,expected:'12',original:receipt,edited:{...receipt,total:'12'}};
  const result=receiptExport(record);
  assert.equal(result.original_extraction.total,'11');
  assert.equal(result.corrected_fields.total,'12');
  assert.equal(result.reviewed_by_user,true);
});
