# FieldOps MCP Server
### Last-Mile Delivery + Asset Finance Collections — Africa Fintech

**Author:** Purity Wanjiru | [github.com/Purity-Creatives](https://github.com/Purity-Creatives)  
**Protocol:** [Model Context Protocol (MCP)](https://modelcontextprotocol.io) — Anthropic  
**Stack:** Python, MCP SDK  
**Market:** Kenya · Uganda · Nigeria · Ghana · Tanzania  
**Status:** v0.1.0 — active development  

---

## What This Is

A Model Context Protocol server that gives Claude conversational access to last-mile delivery tracking and asset finance collections data — built for the operational reality of pay-as-you-go device financing across Africa.

The model: a customer orders a solar panel, smartphone, or appliance. A field agent delivers it. The customer repays in daily or weekly instalments via mobile money. If they stop paying, the device gets remotely locked.

This MCP server lets operations teams ask Claude natural language questions about that entire journey.

---

## Example Conversations

**Delivery operations:**
```
"Show me all failed deliveries in Nairobi today"
→ Lists 7 failed deliveries with customer IDs, agents, failure reasons, and action needed

"Which agents have the lowest delivery success rate this week?"
→ Ranks all agents — worst performers flagged for coaching

"How many devices are still in transit across Uganda?"
→ Returns count, agent assignments, and days in transit per order
```

**Collections:**
```
"List all customers who are 30 to 60 days overdue in Lagos"
→ Returns accounts, balances, repayment rates, and recommended actions

"Which devices are eligible for remote lock right now?"
→ Flags 61+ DPD accounts not yet locked, sorted by balance at risk

"What is our total collections exposure in Accra this month?"
→ Full portfolio summary with DPD bucket breakdown
```

**Combined field ops:**
```
"Show me the full journey for customer C-00045"
→ Order date → delivery status → repayment history → risk flag — all in one response

"How many delivered devices have made zero repayments after 14 days?"
→ Early default detection — highest-risk segment identified immediately

"Which regions have strong delivery but weak collections?"
→ Regional scorecard comparing both metrics — surface where to focus
```

---

## Tools

### Delivery Tools

| Tool | Description |
|------|-------------|
| `get_delivery_summary` | Orders by status, success rate, regional breakdown |
| `get_failed_deliveries` | Failed and pending-reschedule orders with failure reasons |
| `get_agent_delivery_performance` | Agent leaderboard by delivery success rate |
| `get_devices_in_transit` | All devices currently undelivered, with days in transit |

### Collections Tools

| Tool | Description |
|------|-------------|
| `get_collections_summary` | Portfolio overview — outstanding balance, repayment rate, DPD buckets |
| `get_overdue_accounts` | Accounts by DPD bucket (1-30, 31-60, 61-90, 90+) |
| `get_device_lock_candidates` | Devices eligible for remote lock (61+ DPD, not yet locked) |
| `get_agent_collections_performance` | Agent leaderboard by repayment recovery rate |

### Combined Tools

| Tool | Description |
|------|-------------|
| `get_customer_journey` | Full delivery + collections history for one customer |
| `get_zero_repayment_report` | Delivered devices with <10% repayment after N days — early default detection |
| `get_regional_performance` | Delivery success vs collections rate side by side — all regions |

---

## Quick Start

### Install

```bash
pip install mcp
```

### Run

```bash
python fieldops_mcp_server.py
```

### Connect to Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fieldops": {
      "command": "python",
      "args": ["/path/to/fieldops_mcp_server.py"]
    }
  }
}
```

Config file location:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

---

## Data Model

The server simulates a realistic African asset finance portfolio:

| Entity | Count | Details |
|--------|-------|---------|
| Customers | 120 | Across 9 regions in 5 countries |
| Field Agents | 20 | With regional assignments |
| Products | 7 | Solar, Smartphone, Appliance categories |
| Regions | 9 | Nairobi, Mombasa, Kisumu, Nakuru, Eldoret, Kampala, Lagos, Accra, Dar es Salaam |

**Delivery statuses:** delivered, in_transit, failed, pending_reschedule, returned  
**Collection buckets:** current, 1-30 DPD, 31-60 DPD, 61-90 DPD, 90+ DPD  
**Failure reasons:** customer_absent, wrong_address, customer_refused, access_issue, agent_no_show

---

## Production Integration

To connect to a real database, replace the synthetic data generation in `fieldops_mcp_server.py` with your database queries:

```python
# Replace synthetic CUSTOMERS list with:
import psycopg2

def _load_customers():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur  = conn.cursor()
    cur.execute("""
        SELECT c.customer_id, c.region, d.status AS delivery_status,
               d.delivery_date, col.days_overdue, col.balance_usd
        FROM customers c
        JOIN deliveries d ON c.customer_id = d.customer_id
        LEFT JOIN collections col ON c.customer_id = col.customer_id
    """)
    return cur.fetchall()
```

---

## Monetisation

This MCP server is the foundation for a commercial **Field Ops AI layer** that any African asset finance or last-mile logistics company can plug Claude into:

- **SaaS API** — expose as a hosted MCP endpoint, charge per seat
- **White-label** — deploy under client branding for enterprise contracts
- **Vertical expansion** — extend to insurance, microfinance, agri-input distribution

Target customers: M-KOPA, d.light, PAYG distributors, solar home system companies, motorcycle finance lenders, last-mile logistics operators.

---

## Related Projects

- [IFRS 9 ECL Model — Kenya Asset Finance](https://github.com/Purity-Creatives/ifrs9-ecl-model-kenya) — Credit risk modelling for asset finance portfolios (AUC-ROC: 0.860)
- [FMCG Demand Forecasting — Kenya](https://github.com/Purity-Creatives/fmcg-demand-forecasting-kenya) — Prophet forecasting (96.4% accuracy), promotion ROI analysis

---

## Contact

**Purity Wanjiru** | CPA(K) | MBA  
purwan707@gmail.com | Nairobi, Kenya  
[github.com/Purity-Creatives](https://github.com/Purity-Creatives)  
*Building AI tools for African fintech operations.*
