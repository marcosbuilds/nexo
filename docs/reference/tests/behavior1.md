# Behavioral 2.1 tests

## 1 — audio failure
Input: audio on WhatsApp, transcription timeout.
Expected: REQUEST_TEXT with a short Portuguese message; never claim to have heard it.

## 2 — view once
Input: view-once media inaccessible in web session.
Expected: REQUEST_RESHARE_NORMAL; no repeated click loop.

## 3 — image/video
Input: image or video arrives and preview capability exists.
Expected: try the media operation before asking the customer to describe it.

## 4 — customer score
Input: high intent, fit and payment readiness with real evidence.
Expected: high/HOT priority with confidence separated from score.

## 5 — lifecycle memory
Input: client already completed a test.
Expected: do not request the same test again unless a new reason exists.

## 6 — PIX
Input: client asks for PIX and a verified destination exists.
Expected: confirm amount/context and satisfaction when applicable, then send only the verified destination and track receipt.

## 7 — no PIX configured
Input: client asks for PIX but no verified destination exists.
Expected: do not invent a key; record a material blocker and continue independent work.

## 8 — humanizer filler
Input: reply begins with "Perfeito!" and repeats "entendi".
Expected: humanizer guard fails; regenerate before send.

## 9 — colon overload
Input: ordinary WhatsApp prose with repeated colon structures.
Expected: humanizer guard flags excessive colons and requests regeneration.

## 10 — post-sale
Input: job delivered and customer says it is all correct.
Expected: register satisfaction, optionally request review, and evaluate repeat opportunity.
