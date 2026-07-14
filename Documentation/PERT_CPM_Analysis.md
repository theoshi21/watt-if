# PERT & CPM Analysis — WATT-IF

**Document Version:** 1.0  
**Date:** July 2026  
**Prepared by:** Development Team

---

## 1. Introduction

This document presents the Program Evaluation and Review Technique (PERT) and Critical Path Method (CPM) analysis for the WATT-IF project. It estimates project duration using three-point estimates, identifies task dependencies, determines the critical path, and provides scheduling analysis.

### Methodology

- **PERT** uses three time estimates per task: Optimistic (O), Most Likely (M), and Pessimistic (P)
- **Expected Time (TE)** = (O + 4M + P) / 6
- **Variance (σ²)** = ((P - O) / 6)²
- **CPM** identifies the longest path through the project network (critical path), determining the minimum project duration

### Project Timeline

- **Start Date:** June 9, 2026 (Week 2 of June)
- **End Date:** July 19, 2026 (Week 3 of July)
- **Total Duration:** ~6 weeks

---

## 2. Work Breakdown Structure & Time Estimates

Duration is expressed in **days**. One week = 5 working days.

### Milestone 1: Planning / Documentation

| Task ID | Task | Predecessors | O (days) | M (days) | P (days) | TE (days) | σ² |
|---------|------|--------------|----------|----------|----------|-----------|-----|
| A | Draft the Project Proposal | — | 1 | 2 | 3 | 2.0 | 0.11 |
| B | Submission of Project Proposal | A | 1 | 1 | 2 | 1.2 | 0.03 |
| C | Revision of Project Proposal | B | 1 | 2 | 4 | 2.2 | 0.25 |
| D | Define Functional & Non-Functional Requirements | C | 2 | 3 | 5 | 3.2 | 0.25 |
| E | Define System Infrastructure and Tech Stack | C | 1 | 2 | 3 | 2.0 | 0.11 |
| F | Define Project Timeline and Milestones | D, E | 1 | 1 | 2 | 1.2 | 0.03 |

### Milestone 2: Data Preparation

| Task ID | Task | Predecessors | O (days) | M (days) | P (days) | TE (days) | σ² |
|---------|------|--------------|----------|----------|----------|-----------|-----|
| G | Identify & collect data sources (Meralco API, Weather API, ENSO) | F | 1 | 2 | 3 | 2.0 | 0.11 |
| H | Design database schema | F | 1 | 2 | 3 | 2.0 | 0.11 |
| I | Implement data cleaning and transformation pipeline | G, H | 2 | 3 | 5 | 3.2 | 0.25 |
| J | Implement CSV upload parsing and validation | H | 1 | 2 | 3 | 2.0 | 0.11 |
| K | Build the scrapers (Meralco Rates, Weather Summaries) | G | 2 | 3 | 5 | 3.2 | 0.25 |
| L | Generate and Ingest EDA to ChromaDB | I, K | 1 | 2 | 3 | 2.0 | 0.11 |

### Milestone 3: Model Building

| Task ID | Task | Predecessors | O (days) | M (days) | P (days) | TE (days) | σ² |
|---------|------|--------------|----------|----------|----------|-----------|-----|
| M | Build the pipeline for forecasting model (SARIMAX) | L | 2 | 3 | 5 | 3.2 | 0.25 |
| N | Evaluate the forecasting model | M | 1 | 2 | 3 | 2.0 | 0.11 |
| O | Configure LLM Model (Qwen3 1.7B) | L | 1 | 2 | 4 | 2.2 | 0.25 |
| P | Implement RAG scope and prompt engineering | O | 2 | 3 | 4 | 3.0 | 0.11 |

### Milestone 4: System Development

| Task ID | Task | Predecessors | O (days) | M (days) | P (days) | TE (days) | σ² |
|---------|------|--------------|----------|----------|----------|-----------|-----|
| Q | Design and Develop User Interface | F | 3 | 5 | 8 | 5.2 | 0.69 |
| R | Implement all functional requirements | N, P, Q | 3 | 5 | 8 | 5.2 | 0.69 |

### Milestone 5: Testing

| Task ID | Task | Predecessors | O (days) | M (days) | P (days) | TE (days) | σ² |
|---------|------|--------------|----------|----------|----------|-----------|-----|
| S | Write a Test Plan & Test Cases | R | 1 | 2 | 3 | 2.0 | 0.11 |
| T | Create Selenium Automation Scripts | S | 2 | 3 | 5 | 3.2 | 0.25 |
| U | Execute Automation Scripts | T | 1 | 2 | 3 | 2.0 | 0.11 |
| V | Integration Testing | U | 1 | 2 | 3 | 2.0 | 0.11 |
| W | Bug Fixing | V | 2 | 3 | 5 | 3.2 | 0.25 |
| X | Regression Testing | W | 1 | 2 | 3 | 2.0 | 0.11 |

### Milestone 6: Deployment

| Task ID | Task | Predecessors | O (days) | M (days) | P (days) | TE (days) | σ² |
|---------|------|--------------|----------|----------|----------|-----------|-----|
| Y | Configure production environment | X | 1 | 1 | 2 | 1.2 | 0.03 |
| Z | Verify installation | Y | 1 | 1 | 2 | 1.2 | 0.03 |
| AA | Prepare deployment guide | Z | 1 | 1 | 2 | 1.2 | 0.03 |

### Milestone 7: Review / Documentation

| Task ID | Task | Predecessors | O (days) | M (days) | P (days) | TE (days) | σ² |
|---------|------|--------------|----------|----------|----------|-----------|-----|
| AB | Compile final project documentation | AA | 1 | 2 | 3 | 2.0 | 0.11 |
| AC | Finalize test results & QA report | AA | 1 | 1 | 2 | 1.2 | 0.03 |
| AD | Prepare project presentation | AB, AC | 1 | 2 | 3 | 2.0 | 0.11 |
| AE | Submit final deliverables | AD | 1 | 1 | 1 | 1.0 | 0.00 |

---

## 3. Network Diagram — Task Dependencies

```
START
  │
  ▼
 [A] Draft Proposal
  │
  ▼
 [B] Submit Proposal
  │
  ▼
 [C] Revise Proposal
  │
  ├──────────────────────┐
  ▼                      ▼
 [D] Define Req.        [E] Define Tech Stack
  │                      │
  └──────┬───────────────┘
         ▼
        [F] Define Timeline
         │
         ├──────────────────────────────────┐
         ▼                                  ▼
        [G] Collect Data    [H] DB Schema  [Q] Design UI
         │        │          │      │
         │        ▼          ▼      ▼
         │      [K] Scrapers [I] Data Clean [J] CSV Upload
         │        │          │
         │        └────┬─────┘
         │             ▼
         │           [L] EDA to ChromaDB
         │             │
         │     ┌───────┴───────┐
         │     ▼               ▼
         │   [M] SARIMAX     [O] Config LLM
         │     │               │
         │     ▼               ▼
         │   [N] Evaluate    [P] RAG Prompt
         │     │               │
         │     └───────┬───────┘
         │             │
         │             ▼        ┌── [Q] Design UI
         │            [R] Implement All Functional Req.
         │             │
         │             ▼
         │           [S] Test Plan
         │             │
         │             ▼
         │           [T] Selenium Scripts
         │             │
         │             ▼
         │           [U] Execute Scripts
         │             │
         │             ▼
         │           [V] Integration Testing
         │             │
         │             ▼
         │           [W] Bug Fixing
         │             │
         │             ▼
         │           [X] Regression Testing
         │             │
         │             ▼
         │           [Y] Config Production
         │             │
         │             ▼
         │           [Z] Verify Installation
         │             │
         │             ▼
         │           [AA] Deployment Guide
         │             │
         │     ┌───────┴───────┐
         │     ▼               ▼
         │   [AB] Final Doc  [AC] QA Report
         │     │               │
         │     └───────┬───────┘
         │             ▼
         │           [AD] Presentation
         │             │
         │             ▼
         │           [AE] Submit Deliverables
         │             │
         ▼             ▼
                     END
```

---

## 4. Critical Path Analysis

### Forward Pass (Earliest Start & Finish)

| Task | TE | ES | EF |
|------|----|----|----|
| A | 2.0 | 0 | 2.0 |
| B | 1.2 | 2.0 | 3.2 |
| C | 2.2 | 3.2 | 5.3 |
| D | 3.2 | 5.3 | 8.5 |
| E | 2.0 | 5.3 | 7.3 |
| F | 1.2 | 8.5 | 9.7 |
| G | 2.0 | 9.7 | 11.7 |
| H | 2.0 | 9.7 | 11.7 |
| I | 3.2 | 11.7 | 14.8 |
| J | 2.0 | 11.7 | 13.7 |
| K | 3.2 | 11.7 | 14.8 |
| L | 2.0 | 14.8 | 16.8 |
| M | 3.2 | 16.8 | 20.0 |
| N | 2.0 | 20.0 | 22.0 |
| O | 2.2 | 16.8 | 19.0 |
| P | 3.0 | 19.0 | 22.0 |
| Q | 5.2 | 9.7 | 14.8 |
| R | 5.2 | 22.0 | 27.2 |
| S | 2.0 | 27.2 | 29.2 |
| T | 3.2 | 29.2 | 32.3 |
| U | 2.0 | 32.3 | 34.3 |
| V | 2.0 | 34.3 | 36.3 |
| W | 3.2 | 36.3 | 39.5 |
| X | 2.0 | 39.5 | 41.5 |
| Y | 1.2 | 41.5 | 42.7 |
| Z | 1.2 | 42.7 | 43.8 |
| AA | 1.2 | 43.8 | 45.0 |
| AB | 2.0 | 45.0 | 47.0 |
| AC | 1.2 | 45.0 | 46.2 |
| AD | 2.0 | 47.0 | 49.0 |
| AE | 1.0 | 49.0 | 50.0 |

### Backward Pass (Latest Start & Finish)

| Task | TE | LF | LS | Slack |
|------|----|----|----|-------|
| AE | 1.0 | 50.0 | 49.0 | 0 |
| AD | 2.0 | 49.0 | 47.0 | 0 |
| AB | 2.0 | 47.0 | 45.0 | 0 |
| AC | 1.2 | 47.0 | 45.8 | 0.8 |
| AA | 1.2 | 45.0 | 43.8 | 0 |
| Z | 1.2 | 43.8 | 42.7 | 0 |
| Y | 1.2 | 42.7 | 41.5 | 0 |
| X | 2.0 | 41.5 | 39.5 | 0 |
| W | 3.2 | 39.5 | 36.3 | 0 |
| V | 2.0 | 36.3 | 34.3 | 0 |
| U | 2.0 | 34.3 | 32.3 | 0 |
| T | 3.2 | 32.3 | 29.2 | 0 |
| S | 2.0 | 29.2 | 27.2 | 0 |
| R | 5.2 | 27.2 | 22.0 | 0 |
| Q | 5.2 | 22.0 | 16.8 | 7.2 |
| P | 3.0 | 22.0 | 19.0 | 0 |
| O | 2.2 | 19.0 | 16.8 | 0 |
| N | 2.0 | 22.0 | 20.0 | 0 |
| M | 3.2 | 20.0 | 16.8 | 0 |
| L | 2.0 | 16.8 | 14.8 | 0 |
| K | 3.2 | 14.8 | 11.7 | 0 |
| J | 2.0 | 22.0 | 20.0 | 8.3 |
| I | 3.2 | 14.8 | 11.7 | 0 |
| H | 2.0 | 11.7 | 9.7 | 0 |
| G | 2.0 | 11.7 | 9.7 | 0 |
| F | 1.2 | 9.7 | 8.5 | 0 |
| E | 2.0 | 8.5 | 6.5 | 1.2 |
| D | 3.2 | 8.5 | 5.3 | 0 |
| C | 2.2 | 5.3 | 3.2 | 0 |
| B | 1.2 | 3.2 | 2.0 | 0 |
| A | 2.0 | 2.0 | 0 | 0 |

---

## 5. Critical Path

The **Critical Path** is the longest sequence of dependent tasks that determines the minimum project duration. Any delay on these tasks will delay the entire project.

### Critical Path (Slack = 0):

```
A → B → C → D → F → G → I → L → M → N → R → S → T → U → V → W → X → Y → Z → AA → AB → AD → AE
```

**Also critical (parallel branch merging at R):**
```
... → L → O → P → R → ...
```

### Critical Path Duration

**Total Expected Duration = 50.0 working days ≈ 10 weeks**

> **Note:** The Gantt chart compresses this into ~6 weeks through parallel task execution and team overlap. The CPM duration assumes sequential execution along the critical path; actual duration is shorter due to concurrent work on non-critical paths.

---

## 6. PERT Probability Analysis

### Project Variance

Sum of variances along the critical path:

σ²(project) = 0.11 + 0.03 + 0.25 + 0.25 + 0.03 + 0.11 + 0.25 + 0.11 + 0.25 + 0.11 + 0.69 + 0.11 + 0.25 + 0.11 + 0.11 + 0.25 + 0.11 + 0.03 + 0.03 + 0.03 + 0.11 + 0.11 + 0.00

**σ²(project) = 3.44**  
**σ(project) = √3.44 = 1.85 days**

### Probability of Completion

Using the PERT expected duration of 50.0 days:

| Target Duration | Z-Score | Probability of Completion |
|----------------|---------|--------------------------|
| 46 days | (46 - 50.0) / 1.85 = -2.16 | ~2% |
| 49 days | (49 - 50.0) / 1.85 = -0.54 | ~29% |
| 50 days (10 weeks) | (50 - 50.0) / 1.85 = 0.00 | ~50% |
| 51 days | (51 - 50.0) / 1.85 = 0.54 | ~71% |
| 53 days | (53 - 50.0) / 1.85 = 1.62 | ~95% |

---

## 7. Scheduling Summary

| Metric | Value |
|--------|-------|
| Expected Project Duration (PERT) | 50.0 working days |
| Project Standard Deviation | 1.85 days |
| Critical Path Length | 23 tasks |
| Non-Critical Tasks | E, J, Q, AC |
| Maximum Slack (Task Q — UI Design) | 7.2 days |
| Maximum Slack (Task J — CSV Upload) | 8.3 days |
| Planned Duration (Gantt Chart) | ~30 working days (6 weeks) |

### Key Findings

1. **Critical Path** runs through Planning → Data Preparation → Model Building → System Development → Testing → Deployment → Documentation.
2. **UI Design (Q)** has 7.2 days of float — it can start later without affecting the deadline.
3. **CSV Upload (J)** has 8.3 days of float — lowest priority for scheduling.
4. **Task E (Define Tech Stack)** has 1.2 days of slack — nearly critical.
5. The Gantt chart achieves a 6-week schedule by executing parallel paths simultaneously (e.g., UI development concurrent with model building), which is feasible with the 4-person team.

### Recommendations

- **Monitor critical path tasks closely** — any delay on A→B→C→D→F→G→I→L→M→N→R→S→T→U→V→W→X→Y→Z→AA→AB→AD→AE directly impacts delivery.
- **Allocate buffer to Testing phase** (Tasks S–X) as it contains the highest accumulated risk.
- **Leverage float on UI Design** to allow the frontend developer to assist with other critical tasks during Data Preparation.
- **Bug Fixing (W)** has high variance — plan contingency time around this task.

---

## 8. Appendix — PERT Formula Reference

| Formula | Description |
|---------|-------------|
| TE = (O + 4M + P) / 6 | Expected time for a task |
| σ² = ((P - O) / 6)² | Variance of a task |
| σ²(path) = Σ σ²(tasks on path) | Total variance of a path |
| Z = (D - TE) / σ | Z-score for probability |

Where:
- O = Optimistic duration
- M = Most likely duration
- P = Pessimistic duration
- D = Desired completion time
- TE = Expected time
- σ = Standard deviation
