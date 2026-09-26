---
tags:
  - career/pipeline-sankey
  - career/dashboard
updated: "2026-09-10 20:59"
---

# 📊 Job Search Pipeline & Funnel (Sankey View)

> **Real-Time Job Funnel Telemetry** &bull; 1-Click Interactive HTML Visualization:  
> 🔗 **[Open Interactive Sankey Dashboard in Browser](file://C:/Users/jstnp/Projects/adaptive-resume-ai/analytics/Job_Search_Sankey.html)**

---

## 📈 Pipeline Snapshot & Conversion KPIs

| 📝 Total Tracked | 📤 Applications Sent | 🎯 1st Interviews / Screen | 🏆 2nd / Technical | 🎉 Offers | 📊 Screen Conversion |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **1** | **0** | **0** | **0** | **0.0%** |

---

## 🌊 Application Flow (SankeyMATIC Compliant)

You can copy and paste the block below directly into [SankeyMATIC.com](https://sankeymatic.com/build/) to reproduce the exact diagram:

```text
// Application Funnel
Applications [1] No Answer
```

---

## 🧭 Visual Flow Diagram

```mermaid
graph LR
    classDef app fill:#e066a3,stroke:#fff,stroke-width:1px,color:#fff;
    classDef screen fill:#38bdf8,stroke:#fff,stroke-width:1px,color:#fff;
    classDef tech fill:#fb923c,stroke:#fff,stroke-width:1px,color:#fff;
    classDef offer fill:#34d399,stroke:#fff,stroke-width:1px,color:#fff;
    classDef rej fill:#eab308,stroke:#fff,stroke-width:1px,color:#fff;
    classDef wait fill:#2dd4bf,stroke:#fff,stroke-width:1px,color:#fff;
    classDef queue fill:#f59e0b,stroke:#fff,stroke-width:1px,color:#fff;

    Queue["📥 Ready to Apply (0)"]:::queue
    Apps["📝 Applications (1)"]:::app

    Apps -->|"Screen (0)"| Screen["🎯 1st Interviews (0)"]:::screen
    Apps -->|"No Answer (1)"| Wait["⏳ No Answer (1)"]:::wait
    Apps -->|"Rejected (0)"| Rej["❌ Rejected (0)"]:::rej

    Screen -->|"Advanced (0)"| Tech["💼 2nd Interviews (0)"]:::tech
    Tech -->|"Offers (0)"| Offers["🏆 Offers (0)"]:::offer
```

---

## ⚡ 1-Click Actions
- **Open Interactive Browser Sankey:** [Job_Search_Sankey.html](file://C:/Users/jstnp/Projects/adaptive-resume-ai/analytics/Job_Search_Sankey.html)
- **Desktop Shortcut:** Double click `Job Pipeline Sankey` on your Desktop to regenerate and open instantly!
