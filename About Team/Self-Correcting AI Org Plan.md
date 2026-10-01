# Self-Correcting AI Organization Plan

> ⚠️ **SUPERSEDED — NOT IMPLEMENTED**
>
> Writing Club does not implement the system-level self-improvement described in
> this plan. The current architecture keeps **current-run editorial critique and
> adaptive current-run routing** (AI critics evaluate each stage and route the
> current article back for revision within the run). All system-level learning
> loops were removed: no automatic prompt rewrites, no code/State/graph changes,
> no cross-article learning index, and no expectation-alignment auditor. This
> document is retained only as a historical design record.

This is a discussion plan, not an implementation spec for the current version.

## Core Idea

After an article is finished and approved, add a learning node that compares four things:

1. What the user originally supplied: idea, transcript, audio transcript, tone, and target word count.
2. What the AI organization understood: cleaned summary, style profile, proposed flow, critic notes, and revisions.
3. What the user corrected during review: human feedback on flow or draft.
4. What finally got approved: final article plus final review notes.

The node should not directly rewrite the app or secretly change prompts. Its job should be to produce a clear diagnosis:

- where the AI misunderstood the user
- which prompt or agent likely caused the mismatch
- what small change would make the next run closer
- whether the change should be a prompt tweak, style-memory update, checklist rule, test case, or actual code change

Before the system treats this diagnosis as true, it must ask the user:

```text
This is what I think happened:
1. You wanted X.
2. The AI gave Y.
3. The final article became Z.
4. The likely improvement is A.

Am I thinking about this correctly?
```

Only after the user confirms or edits that understanding should the system store the learning.

## Proposed New Node

Name: `Expectation Alignment Auditor`

Runs after final article approval.

Inputs:

- `transcript`
- `summary`
- `requested_tone`
- `article_length`
- `proposed_flow`
- `draft`
- `user_feedback`
- `final_review`
- `pipeline_log`

Outputs:

- `alignment_report`
- `recommended_changes`
- `prompt_patch_suggestions`
- `style_memory_updates`
- `test_case_suggestions`
- `requires_human_approval`

## How It Should Behave

The auditor should ask:

- What did the user actually seem to want?
- What did the system produce before feedback?
- What did the user change or reject?
- Did the final article differ from the first draft in a repeatable way?
- Which instruction would have prevented the miss?
- Is the fix general enough to help future articles, or too specific to this one?

It should classify issues into buckets:

- `summary_loss`: summarizer dropped key points.
- `tone_mismatch`: writer understood content but wrong voice.
- `flow_mismatch`: outline structure did not match expected article shape.
- `generic_drift`: draft became broad advice instead of the user's specific idea.
- `length_mismatch`: too short, padded, or wrong depth.
- `style_memory_gap`: system failed to remember a recurring preference.
- `code_gap`: UI/state/workflow made it hard to express the user's intent.

## Human Approval Loop

The auditor should present changes to the user before anything is applied.

Example:

```text
I found one likely recurring issue:
The summarizer compressed the transcript too aggressively and lost the speaker's final metaphor.

Suggested change:
Add a summarizer rule: "Preserve unusual metaphors and final realizations even if they sound messy."

Apply this to future runs? [yes/no/edit]
```

The user should be able to:

- approve the change
- reject it
- edit the wording
- mark it as only relevant to this project
- correct the AI's diagnosis before the system stores any learning

## Can An AI Agent Change Code By Itself?

Yes, technically it can, but it should not be fully autonomous in this project.

An AI coding agent can modify code or prompt files if it has filesystem access, but that creates risk:

- it may overfit one article's feedback into a permanent rule
- it may break the pipeline
- it may edit the wrong prompt
- it may create silent behavior changes the user does not understand
- it may make the system harder to debug

The safer pattern is controlled self-improvement:

1. The auditor proposes the change.
2. The user approves or edits the change.
3. A code/prompt update agent applies only that approved change.
4. Tests or smoke checks run.
5. The change is logged with before/after reasoning.

So the AI can help change code, but it should do it through an approval gate.

## What To Attempt First

Start with low-risk self-correction:

- save alignment reports after approved articles
- save a draft/review packet before final approval so the user can review the article with the AI's assumptions visible
- save user-approved style rules to the writing style library
- suggest prompt tweaks instead of auto-applying them
- create regression examples from failed runs
- add a small dashboard/message showing "what the system learned"

Good first version:

- no automatic code edits
- no automatic prompt rewrites
- no global memory update without approval
- only structured recommendations

## What To Avoid

Avoid fully autonomous self-modifying behavior:

- do not let the auditor edit Python files by itself
- do not let one article permanently rewrite global prompts without approval
- do not store every user complaint as a universal rule
- do not optimize only for critic scores
- do not hide changes from the user
- do not create a complex multi-agent loop before the current pipeline is stable

Also avoid vague recommendations like:

- "make it more human"
- "improve tone"
- "write better"

Every recommendation should name the exact agent, exact failure, and exact proposed instruction.

## Better Architecture

Use three layers of learning:

1. **Project Memory**
   Notes that apply only to one article/project.

2. **User Style Memory**
   Stable user preferences, approved by the user, such as "keep my casual metaphors" or "do not turn my ideas into motivational speeches."

3. **System Prompt Improvements**
   Rare changes to prompts or code, only after the same issue appears multiple times or the user explicitly approves it.

This prevents one messy run from damaging the whole organization.

## When To Create V2

V2 should not happen just because one run had a complaint. The system should suggest V2 when it sees a strong improvement signal.

Good V2 signals:

- the same failure appears in 3 or more approved article reports
- the user repeatedly corrects the same thing, such as "you made it too generic again"
- the auditor marks multiple runs as `strong` for `v2_signal`
- a problem cannot be solved cleanly by style memory or a prompt note
- the workflow itself is limiting the user, such as missing inputs, wrong approval timing, or poor review visibility

Weak signals should stay as project memory or user style memory. Strong repeated signals can become a proposed V2 change.

The AI should tell the user:

```text
I am seeing the same issue across multiple articles.
This looks like a V2-level improvement, not just a one-article preference.
Here is the exact change I recommend, the files it would touch, and the risk.
Do you want me to prepare it?
```

## How AI Can Do The Work Without Dumping It On The User

The user should not have to manually edit prompts, move files, or decide implementation details.

The AI can handle the work through a controlled loop:

1. Detect a repeated or strong issue.
2. Explain its diagnosis and ask, "Am I thinking right?"
3. Convert the confirmed diagnosis into a small change proposal.
4. Ask approval for that proposal.
5. Apply the approved prompt/code/style/test change.
6. Run checks.
7. Save an improvement report showing exactly what changed.

The user only approves, rejects, or corrects the direction. The AI does the boring execution.

## Suggested V2 Flow

1. User provides source material, tone, and word count.
2. Pipeline writes article.
3. User reviews flow and draft.
4. User approves final article.
5. Final review archivist stores normal review.
6. Expectation Alignment Auditor compares original intent, AI output, user corrections, and final article.
7. Auditor proposes learning changes.
8. User approves/rejects/edits.
9. Approved prompt/style/test updates are saved.
10. Next run uses those approved learnings.

## Implementation Recommendation

Do this in phases:

Phase 1:
Add `alignment_report` generation only. No files are changed automatically.

Phase 2:
Allow user-approved style memory updates.

Phase 3:
Allow user-approved prompt patch suggestions to be written to a pending file, not directly to live prompts.

Phase 4:
Add a code-change agent only for explicitly approved changes, with tests and a change log.

That gives the organization self-correction without making it unpredictable.

## Keeping The Organization From Breaking

To avoid terminating or damaging the whole organization:

- keep every suggested change small and reversible
- store proposed prompt/code patches as pending before applying
- run a smoke test after each applied change
- keep previous prompt versions or change logs
- cap automatic revision loops
- never allow the learning node to rewrite the graph while an article is mid-run
- only apply architecture changes between runs
- if a change fails tests, rollback that change and keep the previous working pipeline
