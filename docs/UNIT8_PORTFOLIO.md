# CMSC 495 Unit 8 — Final Project Portfolio (Team Planning & Evidence)

**Team:** Nonvignon Oussou — Lead Architect; Dylan Albert — Interface Designer; Lo Morton — Integration Lead. Confirm actual authorship and individual work before submitting.

## Part 1 — Integrated repository (team)

Repository: https://github.com/Cyrilleoc/CMSC495-G2-Alpha

- [x] Customer conversation, approved FAQ chatbot, escalation, agent replies, feedback.
- [x] Three scripted end-to-end API scenarios; automated tests.
- [x] Approved synthetic FAQ source IDs and safe escalation fallback.
- [x] Current README plus architecture, API and user documentation.
- [x] Pull-request review evidence (PR #1 and #3).
- [ ] Unit 8 pull request reviewed and merged by team after checks.
- [ ] Capture new CI coverage artifact and Docker smoke-test job screenshot.
- [ ] Record actual stable local live demonstration (video, not just test output).
- [ ] Confirm final deadline and submit accessible repository URL.
- [ ] Validate a real external model only if approved credentials and privacy controls exist; otherwise label it unverified.

The **local FAQ retrieval** is a real bounded AI-assisted feature, but it is not a trained ML model. The hosted model is optional and should not be represented as proven without evidence.

## Part 2 — Technical stakeholder video (team; 10–15 minutes)

Proposed 12-minute outline:
1. Team and stakeholder objective (0:45)
2. Problem, users and quality criteria (0:55)
3. System architecture and tradeoffs (1:10)
4. Customer creates conversation (0:55)
5. Supported FAQ and source ID (1:05)
6. Unsupported question and escalation (1:05)
7. Agent queue, claim, reply, feedback (1:10)
8. AI routing and provider failure (1:05)
9. CI pipeline, 51 tests, coverage (1:10)
10. FAQ benchmark, limitations (1:00)
11. Privacy, security and production gaps (1:05)
12. Stakeholder value, priorities and closing (0:45)

Record team member participation accurately. The live demo should be performed on the actual local app. Pause/re-record rather than show fabricated workflow outcomes. Captions and accessible contrast are recommended.

## Part 3 — Individual 1,300-word position paper

Nonvignon writes **his own** evidence-based position paper: 400 words on integration and delivery; 450 on methodology and performance; 450 on professional development roadmap. The paper must be submitted separately as PDF, with academic references and truthful contribution accounting.

## Collaboration & release workflow

- Nonvignon: integration architecture, final evidence matrix, system demo and technical review.
- Dylan: API/interface usability, accessibility walkthrough, 401/403/429 behavior; confirm with Dylan before assigning final tasks.
- Lo: AI retrieval tests, confidence/fairness limitations and explanation of provider failure; confirm with Lo.
- All: PR comments, slide rehearsal, permissions to record and final review.

## Early submission gates

1. Complete draft documentation and video outline before recording.
2. Obtain genuine teammate review and green PR workflow.
3. Merge; verify `main` CI, coverage and ephemeral deployment smoke checks.
4. Record a 10–15 minute MP4, including an actual live app demonstration.
5. Run final paper word count and proofread.
6. Submit once all three parts are present; retain working files for possible resubmission.

**Deadline:** Not specified in the provided assignment text; confirm exact date/time in UMGC. Do not assume an extension or resubmission window.

## Evidence links

- [Main repository](https://github.com/Cyrilleoc/CMSC495-G2-Alpha)
- [Unit 5 reviewed PR](https://github.com/Cyrilleoc/CMSC495-G2-Alpha/pull/3)
- [Unit 5 passing main CI](https://github.com/Cyrilleoc/CMSC495-G2-Alpha/actions/runs/44923611561)
- [Quality Report](QUALITY_REPORT.md)
- [API Reference](API_REFERENCE.md)
- [User Guide](USER_GUIDE.md)
- [Install / Local Deployment](INSTALL_AND_DEPLOY.md)
