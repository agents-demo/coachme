# Ball: Shot-Type Classification & Pace

**Status:** not started — stub
**Phase:** C1 — Analysis depth
**Effort:** L
**Depends on:** existing ball tracker
**Competitor ref:** SwingVision
**Go/no-go gate:** accuracy must clear stated threshold on labelled set; else descope and keep heuristic

## Goal

Classify shot type (forehand / backhand / serve) and estimate pace per
contact using the ball track and pose; drive rally segmentation from contacts.

## Acceptance

- Shot labels on a labelled test set with stated accuracy.
- Graceful fallback when classification is uncertain.

---
*Full spec to be written. See [00_priorities.md](00_priorities.md) §7 item C1.*
