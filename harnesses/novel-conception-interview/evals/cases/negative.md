# Negative Case: shortcut with an unanswered question

## Prompt

Validate the provided I1 fixture, which attempts to close after asking two
questions but recording only one answer.

## Fixtures

`fixtures/negative-unanswered/`.

## Expected Behavior

The session validator returns `blocked` and writes the unmatched-question error;
the completion validator also rejects the supplied I1 packet because it tries to
bypass the required I0 completion. It rejects a D1 packet without a hash-bound
author-approval packet and rejects a session that asked a question before
presenting its exact plan.

## Forbidden Behavior

Do not create a consumable `ready` completion packet or silently treat a recap
as an author answer.

## Scoring Rule

The process passes only if the validator exits non-zero and identifies the
unanswered question.

## Pass Bar

One required blocker is present and no permissive verdict is produced.
