# Moderation at scale

How the Commons keeps every public contribution safe, accurate and kind as it grows (backlog BL-10, issue #10).
The rules come from [CHARTER.md](../CHARTER.md) and [docs/OPERATING-MODEL.md](OPERATING-MODEL.md); this guide
says how to run them with more people and more traffic. Contact is by form only: no moderator's name or email
address is ever published.

## 1. What gets moderated

| Comes in through | Label | Check before it is public |
|---|---|---|
| Contact form (GitHub issue) | `contact` | Personal data removed or the issue hidden; routed to the right role |
| Shared resources, case studies, events, frameworks | `contribution` | Open licence, working links, plain English, no personal data, source read in full |
| Survey free text | (in the portal) | Suppress anything identifying; counts under 5 are not shown |
| Comments on issues and discussions | any | Code of conduct |

## 2. Service levels

| Kind | First reply | Decision | Escalate if missed |
|---|---|---|---|
| Accessibility problem | 1 working day | 5 working days | Lead maintainer |
| Report a problem with content | 2 working days | 10 working days | Content lead |
| Withdraw my contribution | 2 working days | 5 working days (remove first, then reply) | Lead maintainer |
| Conduct concern | 2 working days | 5 working days | Two moderators who are not involved |
| Everything else | 5 working days | 10 working days | Moderator on rota |

The **Triage** workflow (`.github/workflows/triage.yml`) checks these every working day. It adds
`needs-reply` to any open contact or contribution issue without a maintainer reply after its first-reply time,
and `overdue` after its decision time, so nothing waits unseen. It never closes or deletes anything.

## 3. Rota

- **Size:** one moderator on duty per week for up to 20 new items a week; add one for each extra 20.
- **Hand-over:** at the start of each week the moderator reads the `needs-reply` and `overdue` lists and the weekly
  maintenance issue.
- **Cover:** every moderator has a named back-up for leave. Two moderators review conduct concerns, and neither may be
  involved in the case.
- **Time:** about 1 hour a week at today's volume (operating model, section 3).

## 4. Becoming a moderator

1. Six months of constructive contributions, or nomination by a maintainer.
2. Read the charter, the code of conduct, this guide and the privacy notice.
3. Shadow a rota week.
4. A maintainer gives triage rights on GitHub (the "Triage" role: label, hide comments, close and reopen; no write access to code).
5. Added to `CODEOWNERS` only if they also review content files.

## 5. Decisions

- Publish, ask for changes, or decline, and always say why in plain English.
- Personal data: hide the comment or edit it out at once, then reply. Never repeat the personal data in the reply.
- Spam or abuse: hide, lock the conversation if needed, and record the action in the issue.
- Disagreements with a decision go to a second moderator, then the lead maintainer. The decision and the reason are
  recorded on the issue.

## 6. Growing further

When volume passes about 100 items a month: add a second rota, split by label (content and contact); consider
GitHub Discussions for questions so issues stay for work; publish monthly moderation numbers (items, median time to
first reply, overdue count) on the operating model page. The weekly maintenance task reports these numbers.
