#!/usr/bin/env python3
"""Scores each A/B pair in a run directory and writes report.md there.

    judge.py <out-dir> [--model claude-sonnet-5-5]

For every <id>.A.json + <id>.B.json pair a headless Claude reads both answers
(never the tool traffic) against a fixed rubric and returns one JSON verdict:
agree / partial / disagree, with the concrete differences. The report is a
table, most-different first, then the per-question detail.
"""
import glob, json, os, subprocess, sys

RUBRIC = """You are judging an A/B test. The same question was answered twice, minutes apart,
by two systems that read the same backend on the same environment:
  A = the reference (the senpi-skills engines on the full MCP server)
  B = the candidate (the new read-only connector tools)
Both are supposed to give the same answer. Decide whether they do.

Rules:
- Compare facts: numbers, wallets/addresses, asset names, labels, rankings, plan names,
  scores, statuses, and the conclusion the user would take away. Ignore wording, order,
  formatting and length.
- Market data moves: treat prices, funding and P&L within ~5% (or a few minutes of drift)
  as agreeing, and a different leader in a close ranking as agreeing when the set is the same.
- A fact present on one side and absent on the other is a "coverage" difference, not a
  contradiction, unless the question explicitly asked for it.
- A side that failed (tool error, empty answer, asked to sign in): set "failure" to that side.
- Never invent a number; quote the sides.
- OG CONTRACT: below the question is the list of sections the original skill (A) delivers by
  default for this kind of question. For each section A actually delivered, check whether B
  delivered it too. A section B lacks that A delivered goes in "contract_gaps" and makes the
  verdict "partial" at best, even when every shared number agrees: a thinner answer is not
  agreement. A section neither side delivered is not a gap.

Return ONLY a JSON object:
{"verdict": "agree"|"partial"|"disagree",
 "numbers_agree": true|false|null, "entities_agree": true|false|null, "conclusion_agrees": true|false|null,
 "differences": ["<one line each, quoting A vs B>"],
 "coverage_gaps": ["<facts only one side gave>"],
 "contract_gaps": ["<an OG section A delivered and B did not>"],
 "failure": null | "A" | "B" | "both",
 "note": "<one sentence>"}"""


# What each OG skill delivers by default (its SKILL.md output contract / mandatory
# closing). The judge scores B against these, so a thinner answer can't pass as
# agreement just because the numbers it does give match.
CONTRACTS = {
    "senpi-market-pulse": ["the day's classification and macro picture", "groups: indices, crypto, commodities/macro with moves",
                           "the last-4-hours leader layer (where the 4h winners' gains sit, momentum events)", "Hyperfeed movers",
                           "a Senpi Signals brief (top reads)", "a 'what next' closing with numbered offers"],
    "senpi-signals": ["tradeable dislocations section", "market news section", "the not-measured / stale warning when the feed has one",
                      "a closing offering strategy routes"],
    "senpi-smart-money": ["headline lean of proven traders", "smart vs crowd divergences", "near-term 4h flow or board confirmation",
                          "bottom line and what to watch"],
    "quant-desk": ["score, verdict and archetype", "protection audit of the live positions", "leaks priced in dollars",
                   "strategy / context / edge / market reads", "closing offers"],
    "senpi-trader-research": ["ranked candidates with track record", "copyability or fit with flags", "a minimum budget to mirror (copy asks)",
                              "recent 4h momentum"],
    "senpi-strategy-discover": ["candidates matching the user's constraints with thesis, risk and minimum budget",
                                "caveats (budget below minimum, configurable, shorting)", "why now: the strategy's markets today"],
    "senpi-portfolio": ["balances", "open positions", "strategies", "wallets", "stop events when asked"],
    "senpi-improve-trades": ["totals: net P&L after fees, win rate", "equity and drawdown", "stop events", "what to fix"],
    "senpi-account-status": ["plan", "credits", "points and rank", "fee"],
    "senpi-why": ["positioning", "proof grounded in data", "one closing offer"],
}
CONTRACTS["senpi-quant-desk"] = CONTRACTS["quant-desk"]


def skills_by_id():
    rows = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.tsv")).read().splitlines()[1:]
    return {r.split("\t")[0]: r.split("\t")[2] for r in rows if r.count("\t") >= 3}


def judge(pair, model, skill=None):
    contract = CONTRACTS.get(skill or "", [])
    prompt = (RUBRIC + "\n\nQUESTION:\n" + pair["A"]["question"] +
              "\n\nOG CONTRACT (" + (skill or "unknown") + "):\n" + ("\n".join("- " + c for c in contract) or "- (none listed)") +
              "\n\n=== ANSWER A ===\n" + (pair["A"]["answer"] or "(empty)") +
              "\n\n=== ANSWER B ===\n" + (pair["B"]["answer"] or "(empty)"))
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--no-session-persistence",
           "--setting-sources", "project", "--max-turns", "1", "--tools", ""]
    if model: cmd += ["--model", model]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        txt = json.loads(r.stdout).get("result", "")
        s, e = txt.find("{"), txt.rfind("}")
        return json.loads(txt[s:e + 1])
    except (ValueError, AttributeError):
        return {"verdict": "error", "differences": [], "coverage_gaps": [], "failure": None,
                "note": "judge did not return JSON: " + (r.stderr or r.stdout)[:200]}


def main():
    out = sys.argv[1]
    model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else None
    pairs, skills = {}, skills_by_id()
    for p in sorted(glob.glob(os.path.join(out, "*.json"))):
        if p.endswith(".verdict.json") or os.path.basename(p) == "report.json": continue
        d = json.load(open(p)); pairs.setdefault(d["id"], {})[d["side"]] = d
    rows = []
    for qid, pair in pairs.items():
        if "A" not in pair or "B" not in pair:
            rows.append((qid, {"verdict": "missing", "note": "only side " + "".join(pair), "differences": [], "coverage_gaps": []}, pair)); continue
        vpath = os.path.join(out, qid + ".verdict.json")
        if not (pair["A"].get("answer") or "").strip():
            v = {"verdict": "void", "failure": "A", "differences": [], "coverage_gaps": [], "contract_gaps": [],
                 "note": "the control (A) gave no answer: rerun before judging"}
        else:
            v = json.load(open(vpath)) if os.path.exists(vpath) else judge(pair, model, skills.get(qid))
        # A failed control can't grade B: the pair is void, not a disagreement.
        if v.get("failure") == "A":
            v["verdict"] = "void"
        json.dump(v, open(vpath, "w"), indent=1)
        rows.append((qid, v, pair)); print(f"{qid:12s} {v.get('verdict','?'):9s} {v.get('note','')[:90]}")
    order = {"disagree": 0, "error": 1, "missing": 1, "partial": 2, "void": 3, "agree": 4}
    rows.sort(key=lambda r: order.get(r[1].get("verdict"), 1))
    counts = {k: sum(1 for r in rows if r[1].get("verdict") == k) for k in ("agree", "partial", "disagree", "void")}
    lines = [f"# A/B report — {os.path.basename(out)}", "",
             f"**{counts['agree']} agree · {counts['partial']} partial · {counts['disagree']} disagree · {counts['void']} void** "
             f"of {len(rows)} questions (void = the control failed; rerun it). "
             "A = senpi-skills on the full MCP (dev), B = senpi-plugin on open-mcp (dev).", "",
             "| question | verdict | A tools / s | B tools / s | note |", "|---|---|---|---|---|"]
    for qid, v, pair in rows:
        a, b = pair.get("A", {}), pair.get("B", {})
        at = ", ".join(sorted({t["tool"].split("__")[-1] for t in a.get("tools", [])})) or "—"
        bt = ", ".join(sorted({t["tool"].split("__")[-1] for t in b.get("tools", [])})) or "—"
        lines.append(f"| {qid} | **{v.get('verdict')}** | {at} / {a.get('seconds','?')}s | {bt} / {b.get('seconds','?')}s | {v.get('note','')} |")
    for qid, v, pair in rows:
        if v.get("verdict") == "agree" and not v.get("coverage_gaps"): continue
        lines += ["", f"## {qid} — {v.get('verdict')}", ""]
        lines += [f"- {d}" for d in v.get("differences", [])]
        if v.get("contract_gaps"): lines += ["", "OG sections B did not deliver:"] + [f"- {g}" for g in v["contract_gaps"]]
        if v.get("coverage_gaps"): lines += ["", "Only one side gave:"] + [f"- {g}" for g in v["coverage_gaps"]]
    open(os.path.join(out, "report.md"), "w").write("\n".join(lines) + "\n")
    print("→", os.path.join(out, "report.md"))


if __name__ == "__main__":
    main()
