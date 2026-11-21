# Unit 8 Technical Stakeholder Video — Demonstration Storyboard

**Target duration:** 12 minutes; acceptable assignment window 10–15 minutes. Slides should guide the live demonstration, not replace it.

| Slide | Segment | Target | Recommended narrator |
|---|---|---|---|
| 1 | Project & team | 0:45 | Nonvignon |
| 2 | Customer service problem | 0:55 | Dylan |
| 3 | System architecture | 1:10 | Nonvignon |
| 4 | Start a customer conversation | 0:55 | Dylan |
| 5 | Supported FAQ with source ID | 1:05 | Lo |
| 6 | Unsupported question creates ticket | 1:05 | Lo |
| 7 | Agent ticket claim and reply, feedback | 1:10 | Dylan |
| 8 | AI provider fallback, simulated outage | 1:05 | Lo |
| 9 | CI, coverage and container smoke checks | 1:10 | Nonvignon |
| 10 | Retrieval benchmark and scope | 1:00 | Lo |
| 11 | Security, privacy and tradeoffs | 1:05 | Nonvignon |
| 12 | Business benefit and roadmap | 0:45 | All |

## Live demo sequence (show screen)
1. From Ubuntu WSL, run the application on localhost.
2. Open customer UI; start a new conversation.
3. Enter the actual supported FAQ question and show the answer/source.
4. Ask an unsupported question. Show the resulting queued ticket.
5. In agent UI, claim and reply. Refresh customer history.
6. Record helpful/not-helpful feedback.
7. Open terminal with `python scripts/demo_flow.py` for three end-to-end test paths including **simulated** provider failure.
8. Show GitHub Actions workflow and coverage results.

**Do not show a simulated provider outage as a live external API test.** Do not present demo identity headers as production authentication, or CI container smoke checks as deployed public hosting.

## Recording

Capture actual terminal/browser screen with a screen recorder and narration from the true presenter(s). Verify microphone volume, screen visibility, names, 10–15 min duration, MP4 playback, and whether a hosted video must be unlisted. Provide a backup copy in the group workspace.
