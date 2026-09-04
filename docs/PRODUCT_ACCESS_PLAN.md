# Product and Access Plan

**Status:** Approved direction; not implemented  
**Date:** 2026-09-04

## Product boundary

OI is local-first rather than permanently disconnected. Core inference,
retrieval, citation verification, history settings, and the user's local vault
remain usable without a network connection. A future optional control plane may
provide identity, entitlements, signed update discovery, connector authorization,
role verification, and parish administration. It must not become a hidden remote
inference path or a default collector of conversations and documents.

Four records remain distinct:

1. identity - who signed in;
2. entitlement - what product capability is licensed;
3. permission - which local or external resource may be used for this action;
4. verified role - what named organization attested to a ministry role.

Possession of one never implies another. In particular, signing in through a
Google account does not authorize Gmail access.

## Intended access

The end product is an installed application on supported phones and computers.
The useful free core should permit a guest to evaluate the product without
creating an account. An account becomes necessary for paid entitlements,
cross-device services, connectors, ministry verification, or parish membership.

The first identity implementation should use a managed, standards-based service
rather than a project-owned password database. Exact providers, retention, account
deletion, recovery, and offline entitlement behavior remain open implementation
decisions requiring privacy and threat review.

## Capability tiers

| Tier | Intended capability | Boundary that does not change |
|---|---|---|
| OI Explorer | Free local source navigation, citations, brief explanations, and basic assistance | No personal pastoral or sacramental authority |
| OI Personal | Deeper synthesis, device-appropriate model package, local memory and documents, projects, and opt-in connectors | Evidence, quotation, identity, and safety requirements |
| OI Ministry | Verified-role research, drafting, calendar, catechetical, and parish-workflow tools | Verification does not make model output ecclesially authoritative |
| OI Parish | Seats, organization SSO, parish-managed resources, roles, policies, and support | Parish administrators do not receive private member conversations by default |

Sources and citation integrity are not premium features. Payment may expand
capacity, synthesis, workflow, integrations, update service, and organizational
controls; it does not purchase a more truthful answer or greater spiritual
authority.

## Connector rule

External applications are optional tools, not ambient access. A connector must:

1. request the smallest useful permission separately from account sign-in;
2. treat messages, files, and retrieved pages as untrusted data;
3. expose a typed proposed action to a deterministic permission broker;
4. show the user the consequential action before execution;
5. require confirmation for sending, posting, editing, purchasing, or deleting;
6. store credentials in platform-protected storage; and
7. provide a visible way to inspect and revoke access.

Local files, user-selected documents, calendars, and reminders should precede
broad email or cloud-storage access. No connector work begins until its data flow,
scope, retention, prompt-injection exposure, and failure behavior are recorded.

## Subscription and offline use

A subscription cannot be continuously checked by a device that never connects.
The preferred policy for study is that a legitimately installed local version
continues to run after an entitlement lapses, while future premium updates,
connectors, synchronization, and support require a current entitlement. Final
grace periods, store rules, and perpetual-license options remain open.

Model and corpus packages are versioned, signed, and never silently replaced.
Downloadable weights cannot be assumed to be unextractable; the product's durable
value is continuing curation, tested updates, integrations, and support rather
than an unenforceable promise of perfect local DRM.

## General usefulness

The first product is openly Orthodox-informed and broadly useful. Ordinary work
does not need unsolicited religious commentary. A later general edition may
reuse application infrastructure, but a switch cannot truthfully erase values
trained into weights. A separately disclosed substrate or model package would be
required before describing such an edition as differently governed.

