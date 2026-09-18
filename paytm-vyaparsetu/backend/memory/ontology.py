"""
memory/ontology.py
Strict Pydantic ontology for the VyaparSetu Cognee Knowledge Graph.
These models map directly to Section 4 of the Master Schema and constrain
Cognee entity extraction to prevent topological drift.
"""

from pydantic import BaseModel, Field

class Customer(BaseModel):
    customer_id: str = Field(description="Unique ID of the customer (e.g., c_...)")
    merchant_id: str = Field(description="The merchant this customer belongs to")
    display_name: str = Field(description="Name of the customer (e.g., Suresh)")

class Transaction(BaseModel):
    txn_id: str = Field(description="Unique ID of the ledger transaction (e.g., txn_...)")
    customer_id: str = Field(description="The customer involved in the transaction")
    amount: float = Field(description="Amount of the transaction")
    txn_type: str = Field(description="Type of transaction (e.g., CREDIT_ADDED, CREDIT_PAID)")

class Distributor(BaseModel):
    distributor_id: str = Field(description="Unique ID of the distributor (e.g., dis_...)")
    merchant_id: str = Field(description="The merchant this distributor supplies to")
    name: str = Field(description="Name of the distributor (e.g., Amul Dairy)")

class Invoice(BaseModel):
    invoice_id: str = Field(description="Unique ID of the invoice (e.g., inv_...)")
    distributor_id: str = Field(description="The distributor who issued the invoice")
    invoice_date: str = Field(description="Date of the invoice (YYYY-MM-DD)")
    total_amount: float = Field(description="Total amount of the invoice")

class LineItem(BaseModel):
    invoice_id: str = Field(description="The invoice this line item belongs to")
    sku: str = Field(description="Name/SKU of the item purchased (e.g., Dahi 200g Pouch)")
    quantity: float = Field(description="Quantity of the item purchased")
    unit_price: float = Field(description="Price per unit of the item")
