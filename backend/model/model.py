
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Boolean, DateTime, func, LargeBinary, Text
from datetime import datetime

from database.database import Base

# --- SQLAlchemy Models ---

class IncomingStockModel(Base):
    __tablename__ = "incoming_stock"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(255))
    source_name: Mapped[Optional[str]] = mapped_column(String(255))
    date_of_purchase: Mapped[Optional[str]] = mapped_column(String(50))
    quantity: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    price_per_unit: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    tax_percent: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    tax_amount: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    amount: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    payment_status: Mapped[Optional[str]] = mapped_column(String(50))
    amount_paid: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    payment_type: Mapped[Optional[str]] = mapped_column(String(50))
    payment_date: Mapped[Optional[str]] = mapped_column(String(50))
    delivery_date: Mapped[Optional[str]] = mapped_column(String(50))
    product_photo: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    bill_photo: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    bilti_photo: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

class OutgoingStockModel(Base):
    __tablename__ = "outgoing_stock"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_no: Mapped[Optional[str]] = mapped_column(String(100))
    product_name: Mapped[str] = mapped_column(String(255))
    customer_name: Mapped[Optional[str]] = mapped_column(String(255))
    gst_number: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_sale: Mapped[Optional[str]] = mapped_column(String(50))
    quantity: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    price_per_unit: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    total_amount: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    tax: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    tax_percentage: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    payment_status: Mapped[Optional[str]] = mapped_column(String(50))
    amount_paid: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    payment_type: Mapped[Optional[str]] = mapped_column(String(50))
    payment_date: Mapped[Optional[str]] = mapped_column(String(50))
    delivery_date: Mapped[Optional[str]] = mapped_column(String(50))
    bill_photo: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    product_photo: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

class PaymentTransactionModel(Base):
    __tablename__ = "payment_transactions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float)
    payment_date: Mapped[str] = mapped_column(String(50))
    payment_type: Mapped[str] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class SalesPaymentModel(Base):
    __tablename__ = "sales_payments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float)
    payment_date: Mapped[str] = mapped_column(String(50))
    payment_type: Mapped[str] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class ProductDetailModel(Base):
    __tablename__ = "product_details"
    product_name: Mapped[str] = mapped_column(String(255), primary_key=True)
    details: Mapped[Optional[str]] = mapped_column(Text)


# --- Pydantic Schemas ---

class IncomingStockCreate(BaseModel):
    product_name: str
    source_name: Optional[str] = None
    date_of_purchase: Optional[str] = None
    quantity: Optional[float] = 1.0
    unit: Optional[str] = "pcs"
    price_per_unit: Optional[float] = 0.0
    tax_percent: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    payment_status: Optional[str] = "pending"
    amount_paid: Optional[float] = 0.0
    payment_type: Optional[str] = None
    payment_date: Optional[str] = None
    delivery_date: Optional[str] = None
    product_photo: Optional[str] = None
    bill_photo: Optional[str] = None
    bilti_photo: Optional[str] = None

class IncomingStockUpdate(IncomingStockCreate):
    pass

class PaymentCreate(BaseModel):
    amount: float
    payment_date: str
    payment_type: str
    notes: Optional[str] = None

class OutgoingStockCreate(BaseModel):
    invoice_no: Optional[str] = None
    product_name: str
    customer_name: Optional[str] = None
    gst_number: Optional[str] = ""
    date_of_sale: Optional[str] = None
    quantity: Optional[float] = 1.0
    unit: Optional[str] = "pcs"
    price_per_unit: Optional[float] = 0.0
    total_amount: float
    tax: Optional[float] = 0.0
    tax_percentage: Optional[float] = 5.0
    discount_amount: Optional[float] = 0.0
    payment_type: Optional[str] = None
    payment_date: Optional[str] = None
    delivery_date: Optional[str] = None
    bill_photo: Optional[str] = None
    product_photo: Optional[str] = None

class OutgoingStockUpdate(OutgoingStockCreate):
    pass

class ProductDetailsUpdate(BaseModel):
    product_name: str
    details: str

class ScanBillRequest(BaseModel):
    image: str
    suggested_type: Optional[str] = None
