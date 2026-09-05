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

## Source choice and optional Web evidence

The chat surface offers two understandable source choices:

- **Local only** uses the installed Plithos library and never makes an outbound
  search request.
- **Automatic** tries the local library first and may search the Web only when
  the local evidence does not adequately cover the question and a provider has
  been explicitly configured.

The current provisional provider is Brave LLM Context. It supplies source chunks
and metadata only; Sofiia still generates the answer on the user's device, and
Uvaha applies the same evidence-reference and quotation checks. Uvaha does not
use a remote answer-generation service. The server does not cache the provider
bundle or add it to Plithos, training, or evaluation. Before an answer is
retained in a browser chat, Web-origin source cards are filtered from the local
transcript. The saved answer may carry a note that its Web sources were
transient, but not their result bodies or source metadata.

Automatic sourcing is not an offline feature. Its bounded search terms leave the
device, and the standard provider service may retain queries for billing and
troubleshooting. It requires a provider account and API key and may incur usage
charges. Before distribution, Uvaha needs an approved choice between bring-your-
own credentials and a managed service, a plain-language first-use notice,
credential storage appropriate to the platform, provider terms/privacy review,
and a usable Local only path that requires none of them.

## Conversation sessions

The browser prototype already presents separate chat sessions that the user can
create, switch between, archive, restore, and delete. Context from one session
must not silently enter another. Archive is a reversible organization action;
delete is a distinct, confirmed removal action with clearly documented backup
limits.

Sessions remain on the device by default, are excluded from model training and
analytics, and do not require an account in this prototype. They are serialized
to the browser's `localStorage`, which is not encrypted by Uvaha and may be
visible to other software or users with access to that browser profile. Browser
clearing, storage quotas, private browsing, backups, and extensions can affect
retention. Cloud synchronization, cross-device history, sharing, or voluntary
contribution each require a separate opt-in data flow; deletion cannot promise
erasure from copies outside the browser's stored session state.

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

