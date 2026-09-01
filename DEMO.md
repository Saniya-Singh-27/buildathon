# Demo and pitch guide

Everything needed to run the five-minute demo without improvising.

---

## Before you present

```bash
cd app
streamlit run main.py
```

Checklist:

- [ ] `.env` has a working `GEMINI_API_KEY` — without it the commentary falls back to
      hand-written lines. Still works, just less impressive.
- [ ] Home screen shows "599 transactions loaded". If not, run
      `python3 data/generate_data.py` from the repo root.
- [ ] Have a product screenshot ready on your desktop (any shopping app cart or
      product page). Take one on your phone beforehand and AirDrop/email it over.
- [ ] Judge two or three things before you present so the dashboard isn't empty,
      and click "buy anyway" on at least one DON'T BUY so "times you ignored me"
      has something in it.
- [ ] Delete `data/should_i_buy.db` if you want a completely clean slate.

**Inputs that give each verdict** (verified against the committed dataset):

| Want | Type this |
|---|---|
| BUY | Zomato order, 250, food delivery |
| WAIT | Black blazer, 3499, clothing |
| DON'T BUY | Sony headphones, 29999, electronics |

---

## The five-minute flow

### 0:00 – 0:30 — The problem

> "Every budgeting app tells you what you did wrong last month. That's the one moment
> you can't do anything about it. The moment that actually matters is the ten seconds
> before you hit checkout — and nothing is there."

Have the app already open on the landing screen.

### 0:30 – 1:15 — The good case

Type **Zomato order, 250, food delivery**. Hit JUDGE ME.

Green BUY. Read the commentary out loud — it's short and it's funny.

> "It's not a nag. If the purchase is fine, it says so."

This matters. Show it first, or the whole thing reads as an app that just says no.

### 1:15 – 2:30 — The screenshot, and the real verdict

Upload your screenshot. Click Analyze Screenshot. The fields fill themselves in.

> "It read the product and the price straight off the image."

Now change the price to something expensive, or just type **Sony headphones, 29999,
electronics**. Hit JUDGE ME.

Red DON'T BUY. Point at the reasons:

> "This would swallow 88% of my remaining fun budget, and it's 11.7 times what I
> normally spend on electronics. Those aren't vibes — the app calculated both of
> those numbers before the AI ever saw them."

This is the centrepiece. Don't rush it.

### 2:30 – 3:15 — Ignoring it anyway

Click **BUY ANYWAY**.

> "Obviously people ignore advice. So we let them, and we keep the receipt."

Pick the **failure card** first — show the decline and the retry. Then the success
card. Point out the TEST MODE badge.

> "Razorpay test flow. Simulated, no real money, and there's deliberately no field
> to type a real card number into."

### 3:15 – 4:15 — The dashboard

Click **My dashboard**.

- The KPI row: spent this month, fun budget left
- Where the money goes, by category
- What the app has been telling them — the verdict split
- **Times you ignored me** — with the running total

> "This is the part people actually come back for. It's not judging you, it's just
> keeping score."

### 4:15 – 5:00 — The technical point, and close

> "The important bit is what the AI does *not* do. It never decides whether you can
> afford something. That's plain Python over your transaction history — a handful of
> checks, each worth points, each producing the exact sentence you see on screen.
> The AI only reads screenshots and does the voice. Every number it says out loud is
> a number we handed it. It can't invent a figure and it can't overturn a verdict,
> because by the time it's called the verdict already exists."

Close:

> "A budgeting app tells you what you already did. This one gets there ten seconds
> earlier, when it can still change something."

---

## Pitch structure

If you get a slot rather than a live demo, this is the order:

1. **The problem, in one line.** Budgeting apps are retrospective. The decision
   happens before checkout, and nothing is there.
2. **The insight.** You don't need a better spreadsheet. You need a friend who knows
   your spending, at the moment of temptation, who is honest but not mean.
3. **The demo.** BUY, then DON'T BUY, then ignoring it and paying anyway.
4. **Why it's technically credible.** The deterministic core: data → analysis →
   decision → AI. The LLM sits on the edges, never on the path to the verdict.
5. **What's real and what isn't.** Synthetic data, real calculations, mock payments.
   Say this before anyone asks — volunteering it reads as confidence.
6. **What's next.** Real transaction import, and asking "did you regret it?" a week
   later to tune the thresholds from actual outcomes.

---

## Questions judges will probably ask

**"How is this different from Mint / Walnut / any budgeting app?"**
Those are retrospective dashboards. This is a single interruption at the point of
decision. Different product, not a better version of the same one.

**"What stops the AI hallucinating a number?"**
It never has the chance. The AI is handed a finished decision plus the exact figures
and told to narrate them. It has no access to the transaction data, no ability to
compute, and no ability to change the verdict. Worst case it phrases something
awkwardly — it cannot invent a budget.

**"Is this real financial data?"**
No, and deliberately so. 599 synthetic transactions generated with realistic patterns
— recurring subscriptions, weekend spikes, late-night food orders, occasional
splurges. No bank connection, nothing personal.

**"Did you really integrate Razorpay?"**
It's a mock of Razorpay's test flow — same order/payment id shapes, same
captured/failed statuses, both paths recorded. Swapping in the live SDK is replacing
two functions. We built the mock deliberately so there's no field a real card number
could ever go into.

**"How did you pick the thresholds?"**
By hand, for interpretability rather than accuracy — that's the honest answer. We
optimised for every verdict being explainable in one sentence. The next step is
tuning them from real feedback rather than intuition.

**"What broke while building it?"**
A good one to have ready, because it shows the work was real:

- Historical baselines were being computed from the whole dataset, so a decision
  "today" was partly informed by transactions that hadn't happened yet.
- The burst detector compared a spending spree against an average that *included*
  the spree, which made every spree look normal by definition.
- The app told you not to buy groceries because you'd overspent on clothes — the
  fun-money budget was being applied to essential categories.
