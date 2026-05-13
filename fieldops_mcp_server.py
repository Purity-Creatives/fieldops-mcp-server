#!/usr/bin/env python3
"""
FieldOps MCP Server
===================
A Model Context Protocol (MCP) server for last-mile delivery
and asset finance collections — built for the operational reality
of African fintech and pay-as-you-go device financing.

Inspired by M-KOPA's field operations model: solar panels,
smartphones, and appliances financed and delivered to
underserved communities across Kenya, Uganda, Nigeria, and Ghana.

Use cases (Delivery):
- "Show me all failed deliveries in Nairobi today"
- "Which agents have the lowest delivery success rate this week?"
- "How many devices are still in transit across Uganda?"
- "Flag all orders that have missed their delivery window"

Use cases (Collections):
- "List customers who are 30+ days overdue in Mombasa"
- "What is the total collections exposure in Lagos this month?"
- "Show me customers whose devices are at risk of remote lock"
- "Which field agents have the best repayment recovery rate?"

Use cases (Combined):
- "Show me the full journey for customer C-00123"
- "How many delivered devices have zero repayments after 14 days?"
- "Which regions have the highest delivery success but worst collections?"

Author  : Purity Wanjiru
GitHub  : github.com/Purity-Creatives/fieldops-mcp-server
Products: roraflow.com
Protocol: Model Context Protocol (MCP) — anthropic.com/mcp
"""

import json
import asyncio
import random
from datetime import datetime, timedelta
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import types

# ── Server init ──────────────────────────────────────────────────────
server = Server("fieldops-mcp")

# ── Reference data ───────────────────────────────────────────────────

REGIONS = {
    "NBI": "Nairobi",     "MSA": "Mombasa",   "KSM": "Kisumu",
    "NKR": "Nakuru",      "ELD": "Eldoret",   "KMP": "Kampala",
    "LAG": "Lagos",       "ACC": "Accra",     "DAR": "Dar es Salaam",
}

PRODUCTS = {
    "P01": {"name": "M-KOPA Solar 5L",        "value_usd": 199, "category": "Solar"},
    "P02": {"name": "M-KOPA Solar 8L",        "value_usd": 299, "category": "Solar"},
    "P03": {"name": "Samsung A15 Bundle",      "value_usd": 149, "category": "Smartphone"},
    "P04": {"name": "Tecno Spark 20 Bundle",   "value_usd": 129, "category": "Smartphone"},
    "P05": {"name": "M-KOPA TV 32\"",          "value_usd": 249, "category": "Appliance"},
    "P06": {"name": "M-KOPA Refrigerator 90L", "value_usd": 349, "category": "Appliance"},
    "P07": {"name": "M-KOPA Cooker 2-Plate",   "value_usd": 179, "category": "Appliance"},
}

AGENTS = {
    f"AGT-{str(i).zfill(3)}": {
        "name": random.choice([
            "James Mwangi", "Grace Akinyi", "Samuel Odhiambo", "Faith Njeri",
            "Peter Kamau", "Rose Atieno", "David Mutua", "Mary Wanjiku",
            "John Otieno", "Anne Muthoni"
        ]),
        "region": random.choice(list(REGIONS.keys())),
        "active": True
    }
    for i in range(1, 21)
}

DELIVERY_STATUSES  = ["delivered", "delivered", "delivered", "in_transit",
                       "in_transit", "failed", "pending_reschedule", "returned"]
COLLECTION_STATUSES = ["current", "current", "current", "current",
                        "1_30_dpd", "1_30_dpd", "31_60_dpd", "61_90_dpd", "90_plus_dpd"]
FAILURE_REASONS    = ["customer_absent", "wrong_address", "customer_refused",
                       "access_issue", "agent_no_show"]

def _rand_date(days_back_max=60):
    days = random.randint(0, days_back_max)
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

def _generate_customers(n=120):
    customers = []
    for i in range(1, n + 1):
        agent_id   = random.choice(list(AGENTS.keys()))
        product_id = random.choice(list(PRODUCTS.keys()))
        product    = PRODUCTS[product_id]
        region     = AGENTS[agent_id]["region"]
        order_date = _rand_date(60)
        del_status = random.choice(DELIVERY_STATUSES)

        # Delivery details
        delivery_date     = None
        failure_reason    = None
        delivery_attempts = 1
        if del_status == "delivered":
            delivery_date = order_date
        elif del_status == "failed":
            failure_reason    = random.choice(FAILURE_REASONS)
            delivery_attempts = random.randint(1, 3)
        elif del_status == "pending_reschedule":
            delivery_attempts = random.randint(1, 2)
            failure_reason    = random.choice(FAILURE_REASONS)

        # Collections — only relevant for delivered devices
        col_status       = "not_applicable"
        days_overdue     = 0
        total_due_usd    = 0
        total_paid_usd   = 0
        device_locked    = False
        repayment_rate   = 0

        if del_status == "delivered":
            col_status     = random.choice(COLLECTION_STATUSES)
            deposit        = round(product["value_usd"] * 0.15, 2)
            total_due_usd  = round(product["value_usd"] * random.uniform(0.3, 0.9), 2)
            total_paid_usd = round(total_due_usd * random.uniform(0.1, 1.0), 2)
            repayment_rate = round(total_paid_usd / total_due_usd * 100, 1)

            if col_status == "31_60_dpd":
                days_overdue = random.randint(31, 60)
            elif col_status == "61_90_dpd":
                days_overdue  = random.randint(61, 90)
                device_locked = random.choice([True, False])
            elif col_status == "90_plus_dpd":
                days_overdue  = random.randint(91, 180)
                device_locked = True

        customers.append({
            "customer_id":       f"C-{str(i).zfill(5)}",
            "name":              f"Customer {i:05d}",   # anonymised
            "region":            region,
            "region_name":       REGIONS[region],
            "agent_id":          agent_id,
            "agent_name":        AGENTS[agent_id]["name"],
            "product_id":        product_id,
            "product_name":      product["name"],
            "product_category":  product["category"],
            "product_value_usd": product["value_usd"],
            "order_date":        order_date,
            "delivery_status":   del_status,
            "delivery_date":     delivery_date,
            "delivery_attempts": delivery_attempts,
            "failure_reason":    failure_reason,
            "collection_status": col_status,
            "days_overdue":      days_overdue,
            "total_due_usd":     total_due_usd,
            "total_paid_usd":    round(total_paid_usd, 2),
            "balance_usd":       round(max(total_due_usd - total_paid_usd, 0), 2),
            "repayment_rate_%":  repayment_rate,
            "device_locked":     device_locked,
        })
    return customers

CUSTOMERS = _generate_customers(120)


# ── TOOL DEFINITIONS ─────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [

        # ── DELIVERY TOOLS ──────────────────────────────────────
        types.Tool(
            name="get_delivery_summary",
            description=(
                "Get a summary of all delivery orders — total count, "
                "breakdown by status (delivered, in_transit, failed, "
                "pending_reschedule, returned), and success rate. "
                "Optionally filter by region."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {
                        "type": "string",
                        "description": "Region code to filter by (e.g. NBI, MSA, KMP). Leave blank for all regions."
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Days to look back (default 30)",
                        "default": 30
                    }
                }
            }
        ),

        types.Tool(
            name="get_failed_deliveries",
            description=(
                "List all failed or pending-reschedule deliveries. "
                "Returns customer ID, region, agent, product, failure reason, "
                "and number of attempts. Essential for field ops recovery planning."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {
                        "type": "string",
                        "description": "Filter by region code (optional)"
                    }
                }
            }
        ),

        types.Tool(
            name="get_agent_delivery_performance",
            description=(
                "Rank field agents by delivery success rate. "
                "Shows deliveries attempted, delivered, failed, "
                "and success rate percentage per agent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {
                        "type": "string",
                        "description": "Filter by region (optional)"
                    },
                    "min_deliveries": {
                        "type": "integer",
                        "description": "Minimum deliveries to include agent (default 3)",
                        "default": 3
                    }
                }
            }
        ),

        types.Tool(
            name="get_devices_in_transit",
            description=(
                "Show all devices currently in transit — not yet delivered "
                "or failed. Useful for daily logistics tracking and "
                "identifying orders approaching SLA breach."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {
                        "type": "string",
                        "description": "Filter by region (optional)"
                    }
                }
            }
        ),

        # ── COLLECTIONS TOOLS ───────────────────────────────────
        types.Tool(
            name="get_collections_summary",
            description=(
                "Get portfolio-level collections summary — total active "
                "accounts, total outstanding balance, breakdown by DPD bucket "
                "(current, 1-30, 31-60, 61-90, 90+), and at-risk exposure."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {
                        "type": "string",
                        "description": "Filter by region (optional)"
                    }
                }
            }
        ),

        types.Tool(
            name="get_overdue_accounts",
            description=(
                "List customers with overdue repayments. "
                "Filter by DPD bucket: 1_30, 31_60, 61_90, or 90_plus. "
                "Returns customer, region, product, balance, days overdue, "
                "repayment rate, and device lock status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dpd_bucket": {
                        "type": "string",
                        "description": "DPD bucket: 1_30_dpd, 31_60_dpd, 61_90_dpd, or 90_plus_dpd",
                        "enum": ["1_30_dpd", "31_60_dpd", "61_90_dpd", "90_plus_dpd"]
                    },
                    "region_code": {
                        "type": "string",
                        "description": "Filter by region (optional)"
                    }
                },
                "required": ["dpd_bucket"]
            }
        ),

        types.Tool(
            name="get_device_lock_candidates",
            description=(
                "Identify delivered devices eligible for remote lock — "
                "accounts 61+ DPD with outstanding balances. "
                "Returns customer ID, product, balance, days overdue, "
                "and current lock status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {
                        "type": "string",
                        "description": "Filter by region (optional)"
                    }
                }
            }
        ),

        types.Tool(
            name="get_agent_collections_performance",
            description=(
                "Rank field agents by repayment recovery performance. "
                "Shows total accounts managed, average repayment rate, "
                "overdue accounts, and total outstanding balance per agent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {
                        "type": "string",
                        "description": "Filter by region (optional)"
                    }
                }
            }
        ),

        # ── COMBINED TOOLS ──────────────────────────────────────
        types.Tool(
            name="get_customer_journey",
            description=(
                "Get the complete journey for a single customer — "
                "from order placement through delivery to current "
                "repayment status. The full picture in one query."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID (e.g. C-00001)"
                    }
                },
                "required": ["customer_id"]
            }
        ),

        types.Tool(
            name="get_zero_repayment_report",
            description=(
                "Find customers whose devices were delivered but have "
                "made zero or near-zero repayments — the highest-risk "
                "segment for early default. Filter by days since delivery."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "days_since_delivery": {
                        "type": "integer",
                        "description": "Minimum days since delivery to flag (default 14)",
                        "default": 14
                    },
                    "region_code": {
                        "type": "string",
                        "description": "Filter by region (optional)"
                    }
                }
            }
        ),

        types.Tool(
            name="get_regional_performance",
            description=(
                "Compare all regions on delivery success rate AND "
                "collections repayment rate side by side. "
                "Identifies which regions are strong on delivery "
                "but weak on collections — and vice versa."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


# ── TOOL HANDLERS ────────────────────────────────────────────────────

def _filter(data, region_code=None, days_back=None, status_field=None, status_value=None):
    result = data
    if region_code:
        result = [c for c in result if c["region"] == region_code.upper()]
    if days_back:
        cutoff = datetime.now() - timedelta(days=days_back)
        result = [c for c in result
                  if datetime.strptime(c["order_date"], "%Y-%m-%d") >= cutoff]
    if status_field and status_value:
        result = [c for c in result if c[status_field] == status_value]
    return result


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:

    # ── DELIVERY ─────────────────────────────────────────────────────

    if name == "get_delivery_summary":
        region    = arguments.get("region_code")
        days_back = arguments.get("days_back", 30)
        data      = _filter(CUSTOMERS, region_code=region, days_back=days_back)

        by_status = {}
        for c in data:
            s = c["delivery_status"]
            by_status[s] = by_status.get(s, 0) + 1

        delivered = by_status.get("delivered", 0)
        total     = len(data)
        success   = round(delivered / total * 100, 1) if total else 0

        by_region = {}
        for c in data:
            r = c["region_name"]
            by_region.setdefault(r, {"total": 0, "delivered": 0})
            by_region[r]["total"] += 1
            if c["delivery_status"] == "delivered":
                by_region[r]["delivered"] += 1
        for r in by_region:
            t = by_region[r]["total"]
            d = by_region[r]["delivered"]
            by_region[r]["success_rate_%"] = round(d / t * 100, 1) if t else 0

        result = {
            "period":            f"Last {days_back} days",
            "region_filter":     REGIONS.get(region, "All regions") if region else "All regions",
            "total_orders":      total,
            "delivery_success_%": success,
            "by_status":         by_status,
            "by_region":         by_region,
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_failed_deliveries":
        region = arguments.get("region_code")
        data   = _filter(CUSTOMERS, region_code=region)
        failed = [c for c in data
                  if c["delivery_status"] in ("failed", "pending_reschedule")]

        result = {
            "failed_count":  len(failed),
            "region_filter": REGIONS.get(region, "All regions") if region else "All regions",
            "deliveries": [{
                "customer_id":       c["customer_id"],
                "region":            c["region_name"],
                "agent":             c["agent_name"],
                "product":           c["product_name"],
                "status":            c["delivery_status"],
                "failure_reason":    c["failure_reason"],
                "attempts":          c["delivery_attempts"],
                "order_date":        c["order_date"],
                "action":            "Reschedule — contact customer" if c["delivery_status"] == "failed"
                                     else "Awaiting reschedule confirmation",
            } for c in failed]
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_agent_delivery_performance":
        region       = arguments.get("region_code")
        min_del      = arguments.get("min_deliveries", 3)
        data         = _filter(CUSTOMERS, region_code=region)
        agent_stats  = {}

        for c in data:
            aid = c["agent_id"]
            agent_stats.setdefault(aid, {
                "agent_id": aid, "name": c["agent_name"],
                "region": c["region_name"], "total": 0,
                "delivered": 0, "failed": 0
            })
            agent_stats[aid]["total"] += 1
            if c["delivery_status"] == "delivered":
                agent_stats[aid]["delivered"] += 1
            elif c["delivery_status"] in ("failed", "returned"):
                agent_stats[aid]["failed"] += 1

        ranked = sorted(
            [a for a in agent_stats.values() if a["total"] >= min_del],
            key=lambda x: x["delivered"] / x["total"] if x["total"] else 0,
            reverse=True
        )
        for a in ranked:
            a["success_rate_%"] = round(a["delivered"] / a["total"] * 100, 1) if a["total"] else 0

        result = {
            "agents_ranked": len(ranked),
            "region_filter": REGIONS.get(region, "All regions") if region else "All regions",
            "leaderboard":   ranked
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_devices_in_transit":
        region  = arguments.get("region_code")
        data    = _filter(CUSTOMERS, region_code=region)
        transit = [c for c in data if c["delivery_status"] == "in_transit"]

        result = {
            "in_transit_count": len(transit),
            "region_filter":    REGIONS.get(region, "All regions") if region else "All regions",
            "devices": [{
                "customer_id": c["customer_id"],
                "region":      c["region_name"],
                "agent":       c["agent_name"],
                "product":     c["product_name"],
                "order_date":  c["order_date"],
                "days_in_transit": (datetime.now() -
                    datetime.strptime(c["order_date"], "%Y-%m-%d")).days,
            } for c in transit]
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── COLLECTIONS ──────────────────────────────────────────────────

    elif name == "get_collections_summary":
        region    = arguments.get("region_code")
        delivered = [c for c in CUSTOMERS if c["delivery_status"] == "delivered"]
        data      = _filter(delivered, region_code=region)

        total_outstanding = sum(c["balance_usd"] for c in data)
        total_due         = sum(c["total_due_usd"] for c in data)
        total_collected   = sum(c["total_paid_usd"] for c in data)
        overall_rate      = round(total_collected / total_due * 100, 1) if total_due else 0

        dpd_buckets = {}
        for c in data:
            b = c["collection_status"]
            dpd_buckets.setdefault(b, {"count": 0, "outstanding_usd": 0})
            dpd_buckets[b]["count"] += 1
            dpd_buckets[b]["outstanding_usd"] += c["balance_usd"]
        for b in dpd_buckets:
            dpd_buckets[b]["outstanding_usd"] = round(dpd_buckets[b]["outstanding_usd"], 2)

        at_risk = sum(c["balance_usd"] for c in data if c["days_overdue"] >= 31)

        result = {
            "region_filter":         REGIONS.get(region, "All regions") if region else "All regions",
            "active_accounts":       len(data),
            "total_outstanding_usd": round(total_outstanding, 2),
            "total_collected_usd":   round(total_collected, 2),
            "overall_repayment_rate_%": overall_rate,
            "at_risk_31_plus_usd":   round(at_risk, 2),
            "locked_devices":        sum(1 for c in data if c["device_locked"]),
            "by_dpd_bucket":         dpd_buckets,
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_overdue_accounts":
        dpd_bucket = arguments["dpd_bucket"]
        region     = arguments.get("region_code")
        delivered  = [c for c in CUSTOMERS if c["delivery_status"] == "delivered"]
        data       = _filter(delivered, region_code=region)
        overdue    = [c for c in data if c["collection_status"] == dpd_bucket]

        total_exposure = sum(c["balance_usd"] for c in overdue)
        result = {
            "dpd_bucket":       dpd_bucket,
            "region_filter":    REGIONS.get(region, "All regions") if region else "All regions",
            "account_count":    len(overdue),
            "total_exposure_usd": round(total_exposure, 2),
            "accounts": [{
                "customer_id":      c["customer_id"],
                "region":           c["region_name"],
                "agent":            c["agent_name"],
                "product":          c["product_name"],
                "balance_usd":      c["balance_usd"],
                "days_overdue":     c["days_overdue"],
                "repayment_rate_%": c["repayment_rate_%"],
                "device_locked":    c["device_locked"],
                "action":           "Consider remote lock" if not c["device_locked"] and c["days_overdue"] >= 61
                                    else "Escalate to collections team" if c["days_overdue"] >= 90
                                    else "Call customer — arrange payment plan",
            } for c in sorted(overdue, key=lambda x: x["days_overdue"], reverse=True)]
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_device_lock_candidates":
        region    = arguments.get("region_code")
        delivered = [c for c in CUSTOMERS if c["delivery_status"] == "delivered"]
        data      = _filter(delivered, region_code=region)
        candidates = [c for c in data
                      if c["days_overdue"] >= 61 and not c["device_locked"]]

        total_at_risk = sum(c["balance_usd"] for c in candidates)
        result = {
            "region_filter":    REGIONS.get(region, "All regions") if region else "All regions",
            "lock_candidates":  len(candidates),
            "total_at_risk_usd": round(total_at_risk, 2),
            "devices": [{
                "customer_id":  c["customer_id"],
                "product":      c["product_name"],
                "region":       c["region_name"],
                "balance_usd":  c["balance_usd"],
                "days_overdue": c["days_overdue"],
                "locked":       c["device_locked"],
                "action":       "ELIGIBLE FOR REMOTE LOCK",
            } for c in sorted(candidates, key=lambda x: x["days_overdue"], reverse=True)]
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_agent_collections_performance":
        region     = arguments.get("region_code")
        delivered  = [c for c in CUSTOMERS if c["delivery_status"] == "delivered"]
        data       = _filter(delivered, region_code=region)
        agent_col  = {}

        for c in data:
            aid = c["agent_id"]
            agent_col.setdefault(aid, {
                "agent_id": aid, "name": c["agent_name"],
                "region": c["region_name"], "accounts": 0,
                "total_due": 0, "total_paid": 0, "overdue_count": 0
            })
            agent_col[aid]["accounts"]    += 1
            agent_col[aid]["total_due"]   += c["total_due_usd"]
            agent_col[aid]["total_paid"]  += c["total_paid_usd"]
            if c["days_overdue"] > 0:
                agent_col[aid]["overdue_count"] += 1

        ranked = []
        for a in agent_col.values():
            a["repayment_rate_%"] = round(
                a["total_paid"] / a["total_due"] * 100, 1) if a["total_due"] else 0
            a["outstanding_usd"]  = round(a["total_due"] - a["total_paid"], 2)
            ranked.append(a)

        ranked.sort(key=lambda x: x["repayment_rate_%"], reverse=True)
        result = {
            "region_filter": REGIONS.get(region, "All regions") if region else "All regions",
            "agents_ranked": len(ranked),
            "leaderboard":   ranked
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── COMBINED ─────────────────────────────────────────────────────

    elif name == "get_customer_journey":
        customer_id = arguments["customer_id"].upper()
        match = next((c for c in CUSTOMERS if c["customer_id"] == customer_id), None)

        if not match:
            return [types.TextContent(type="text", text=json.dumps(
                {"error": f"Customer {customer_id} not found"}))]

        result = {
            "customer_id":      match["customer_id"],
            "region":           match["region_name"],
            "assigned_agent":   match["agent_name"],
            "DELIVERY": {
                "product":          match["product_name"],
                "product_value_usd": match["product_value_usd"],
                "order_date":       match["order_date"],
                "status":           match["delivery_status"],
                "delivery_date":    match["delivery_date"],
                "attempts":         match["delivery_attempts"],
                "failure_reason":   match["failure_reason"],
            },
            "COLLECTIONS": {
                "status":           match["collection_status"],
                "total_due_usd":    match["total_due_usd"],
                "total_paid_usd":   match["total_paid_usd"],
                "balance_usd":      match["balance_usd"],
                "repayment_rate_%": match["repayment_rate_%"],
                "days_overdue":     match["days_overdue"],
                "device_locked":    match["device_locked"],
            },
            "RISK_FLAG": (
                "HIGH — device lock eligible" if match["days_overdue"] >= 61 and not match["device_locked"]
                else "CRITICAL — locked and 90+ DPD" if match["device_locked"] and match["days_overdue"] >= 90
                else "WATCH — 30+ DPD" if match["days_overdue"] >= 30
                else "LOW"
            )
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_zero_repayment_report":
        min_days = arguments.get("days_since_delivery", 14)
        region   = arguments.get("region_code")
        today    = datetime.now()
        delivered = [c for c in CUSTOMERS if c["delivery_status"] == "delivered"
                     and c["delivery_date"] is not None]
        data     = _filter(delivered, region_code=region)

        at_risk = []
        for c in data:
            days_since = (today - datetime.strptime(c["delivery_date"], "%Y-%m-%d")).days
            if days_since >= min_days and c["repayment_rate_%"] < 10:
                at_risk.append({
                    "customer_id":      c["customer_id"],
                    "region":           c["region_name"],
                    "agent":            c["agent_name"],
                    "product":          c["product_name"],
                    "product_value_usd": c["product_value_usd"],
                    "delivery_date":    c["delivery_date"],
                    "days_since_delivery": days_since,
                    "repayment_rate_%": c["repayment_rate_%"],
                    "balance_usd":      c["balance_usd"],
                    "action":           "Immediate outreach — early default risk",
                })

        total_exposure = sum(c["balance_usd"] for c in at_risk)
        result = {
            "region_filter":     REGIONS.get(region, "All regions") if region else "All regions",
            "threshold":         f"{min_days}+ days since delivery, <10% repayment",
            "at_risk_count":     len(at_risk),
            "total_exposure_usd": round(total_exposure, 2),
            "customers":         sorted(at_risk, key=lambda x: x["balance_usd"], reverse=True)
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_regional_performance":
        regions_data = {}
        for c in CUSTOMERS:
            r = c["region_name"]
            regions_data.setdefault(r, {
                "region": r, "total_orders": 0, "delivered": 0,
                "active_accounts": 0, "total_due": 0, "total_paid": 0
            })
            regions_data[r]["total_orders"] += 1
            if c["delivery_status"] == "delivered":
                regions_data[r]["delivered"] += 1
            if c["collection_status"] not in ("not_applicable",):
                regions_data[r]["active_accounts"] += 1
                regions_data[r]["total_due"]  += c["total_due_usd"]
                regions_data[r]["total_paid"] += c["total_paid_usd"]

        ranked = []
        for r, d in regions_data.items():
            d["delivery_success_%"]  = round(d["delivered"] / d["total_orders"] * 100, 1) if d["total_orders"] else 0
            d["repayment_rate_%"]    = round(d["total_paid"] / d["total_due"] * 100, 1) if d["total_due"] else 0
            d["outstanding_usd"]     = round(d["total_due"] - d["total_paid"], 2)
            d["insight"] = (
                "Strong delivery, weak collections — prioritise collections training"
                if d["delivery_success_%"] > 70 and d["repayment_rate_%"] < 50
                else "Strong collections, weak delivery — review logistics"
                if d["delivery_success_%"] < 50 and d["repayment_rate_%"] > 70
                else "Both metrics strong — scale operations here"
                if d["delivery_success_%"] > 70 and d["repayment_rate_%"] > 70
                else "Both metrics need attention"
            )
            ranked.append(d)

        ranked.sort(key=lambda x: x["delivery_success_%"], reverse=True)
        result = {
            "regions_compared": len(ranked),
            "regional_scorecard": ranked
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ── ENTRY POINT ──────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
