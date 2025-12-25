from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MegaMix API",
    description="API for MegaMix platform.",
    version="0.1.0"
)

import os

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.123.34:3000"
]

env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    origins.extend(env_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

from modules.auth.router import router as auth_router
from modules.inventory.router import router as inventory_router
from modules.clients.router import router as clients_router
from modules.sales.router import router as sales_router
from modules.analytics.router import router as analytics_router
from modules.expenses.router import router as expenses_router

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication & Users"])
app.include_router(inventory_router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(clients_router, prefix="/api/clients", tags=["Clients"])
app.include_router(sales_router, prefix="/api/sales", tags=["Sales"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(expenses_router, prefix="/api/expenses", tags=["Expenses"])


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the MegaMix API!"}