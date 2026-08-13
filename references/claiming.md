# Claiming Handshake / Project Dynamo tasks programmatically

A runbook for an agent operating a logged-in Chrome session on
`ai.joinhandshake.com`. Everything below runs as page JavaScript in a tab that
is already authenticated. No credentials are read, moved or stored - the browser
attaches the session cookie itself.

---

## 1. The headline finding

**Claiming is route-based, not an API mutation.**

    GET /annotations/fellow/task/<TASK_ID>/claim

That is the whole mechanism. It targets a SPECIFIC task id and it works even
while you already hold other tasks in progress.

This is not obvious, and the obvious paths are all wrong:

| what you might try | what actually happens |
|---|---|
| `task.claimNextTask` (tRPC) | returns a task you ALREADY hold, with HTTP 200 and `"status":"claimed"`. Useless. |
| The "Start task" button | calls `claimNextTask` and navigates. Same failure, plus it destroys any in-page script you had running. |
| Searching the tRPC router for a claim procedure | there isn't one. `claimNextTask` is the only claim mutation in the whole router. |

We burned 37 `claimNextTask` calls with 0 claims before finding this. The lead
was an identifier called `buildTaskClaimRoute` in the JS bundle - a route
BUILDER, not a mutation - which is what pointed at a URL rather than an API.

---

## 2. Your project id

Read it from your own tasks-page URL:

    https://ai.joinhandshake.com/fellow/<ANNOTATION_PROJECT_ID>/tasks

Everything below calls that value `PROJ`. Do not copy someone else's.

---

## 3. The three calls

### See what is on the board

    GET /api/trpc/task.getAllClaimableTasksForFellow?batch=1&input=<urlencoded>

with input:

```json
{"0":{"json":{
  "annotationProjectId":"<PROJ>",
  "pipelineStageId":null,"attempters":null,"search":null,
  "sortBy":"default","sortOrder":"desc","limit":25,"offset":0,
  "categories":null,"priorityLevel":null},
 "meta":{"values":{"pipelineStageId":["undefined"],"attempters":["undefined"],
  "search":["undefined"],"categories":["undefined"],"priorityLevel":["undefined"]},"v":1}}}
```

Results are at `j[0].result.data.json`. **Omitting the `meta` block returns 400**
- superjson needs the nulls declared as undefined.

### Check whether anything is claimable by you

    GET /api/trpc/task.hasClaimableTaskForFellow?batch=1&input=
        {"0":{"json":{"annotationProjectId":"<PROJ>"}}}

Returns `{json:true|false}`. Note this asks a DIFFERENT question from the call
above: the board can show tasks while this returns false.

### Confirm what you actually hold

    GET /api/trpc/task.listClaimedTasksForFellow?batch=1&input=
        {"0":{"json":{"annotationProjectId":"<PROJ>"}}}

Returns `{json:{activeTasks:[...], pastTasks:[...], availableCategoryValues:{...}}}`.

**Use the MINIMAL payload here** - just `annotationProjectId`. The long
filter/sort payload that the board call needs returns 400 on this one.

---

## 4. Verify every claim. Never trust the response.

The claim route is fetched with `redirect:'manual'`, which yields
`status: 0` and `type: "opaqueredirect"`. That tells you **nothing** about
whether the claim succeeded.

The only proof is that the task id appears in `activeTasks`. Check it. We
recorded two "successful" claims that had claimed nothing at all because we
believed an HTTP 200.

---

## 5. Hidden tabs get FROZEN - this breaks everything else

**Chrome freezes hidden background tabs.** A frozen tab has all JS suspended -
the worker's timers, its fetches, and `postMessage` delivery all stop dead.
This is the single biggest operational problem with the whole approach, and no
amount of care in the script works around it.

An earlier version of this section said a Web Worker "is not throttled that
way". That is **wrong** and it cost us a poll window - we trusted a dead worker
because the advice here told us to. Timer throttling is real (a hidden tab's
`setInterval` drops to roughly one fire per minute, escalating after ~5 minutes
hidden), and moving the poll into a Worker does help with it. But throttling is
the lesser problem. Freezing is the one that kills you, and a Worker does not
escape it, because the freeze belongs to the owning page.

The tell is unmistakable once you have seen it: driving the tab from CDP fails
with

    Runtime.evaluate timed out ... The renderer may be frozen or unresponsive.

Measured, `document.hidden === true` in all four cases:

| worker armed | outcome |
|---|---|
| 12s after a page load | stopped after 18 passes (~5 min) |
| 12s after a page load | ran the full 45 min, clean 15-17s cadence |
| on a page loaded 51 min earlier | stopped after 7 passes (~1m45s) |
| 10s after a deliberate reload | stopped after 3 passes (~50s) |

**Reloading before arming does NOT fix this** - row 4 was a reload and it died
fastest of all. Row 2 is the anomaly, not the norm, and it is not reproducible
on demand. Do not build on it.

The only reliable fix is to **keep the tab visible** - the selected tab in some
window, so `document.hidden` is false. Chrome does not freeze a visible tab.
Everything else is mitigation:

- Driving the tab from CDP on your own schedule sometimes works and sometimes
  hits the same 45s timeout - once the tab is frozen hard, an external poker
  does NOT reliably wake it. Measured: two consecutive sweep attempts on a
  frozen tab both timed out. Do not treat this as a fallback you can rely on.
- A recovery navigate does un-freeze a wedged tab, at the cost of the worker.
  That is a repair, not a poll strategy.

Treat liveness as something you measure, never something you assume.

Three gotchas:

1. A worker created from a Blob URL has **no page base URL**, so relative
   paths throw `Failed to parse URL`. Pass `location.origin` in and prefix
   every fetch with it.
2. Pass `credentials:'include'` so the session cookie is attached.
3. `window.__w` stays truthy long after the loop has stopped. A live worker
   OBJECT is not a running loop - see 5a.

### 5a. Stalled worker vs throttled message channel

`postMessage` from worker to page can itself be delivered late, so "no new log
entries" has two very different causes that look identical from the page:

```js
Math.round((Date.now() - Date.parse(window.__log.at(-1).at)) / 1000)   // lagSec
```

Anything past ~2x your poll interval means it has stopped logging. To find out
which failure it is, check whether the tab is still making tRPC requests. If
requests are still flowing, the worker is fine and only its messages are stuck.
If they have stopped, the loop is dead and you must re-arm.

Note that network-inspection tools generally only record from the moment they
are first attached, so a stall you are already inside of will show an empty
history. Attach early, or accept that the first diagnosis costs one interval.

---

## 6. Working script

Paste into the console of a tab sitting on the tasks page. Set `PROJ` and
`BASE` first.

Three properties are deliberate and you should not casually remove them:

- **One-shot.** It stops after ONE verified claim. The old version of this
  script defaulted to `TARGET = 10`, which contradicted this runbook's own
  advice two sections down. A pile of open claims pays nothing (section 7).
- **Self-halting.** `DEADLINE` is a hard stop measured from arming. Without it,
  a script you forget about is a script running unattended - which is exactly
  what section 7 tells you not to do.
- **Board first, cheaply.** An idle pass costs exactly ONE request, because
  `held()` is only fetched when the board actually has something on it. At the
  default 60s that is 60 requests/hour. The older held-then-board ordering at
  15s was ~480/hour for identical results.

```js
const PROJ     = "<YOUR_ANNOTATION_PROJECT_ID>";
const BASE     = 1;            // how many you already hold; stop above this
const EVERY    = 60000;        // ms between passes - see section 7
const MAXWAIT  = 600000;       // ceiling for the error backoff
const DEADLINE = 45*60*1000;   // hard self-halt

const src = `
const PROJ   = ${JSON.stringify(PROJ)};
const O      = ${JSON.stringify(location.origin)};
const BASE   = ${BASE};
const EVERY  = ${EVERY};
const MAXWAIT = ${MAXWAIT};
const END    = Date.now() + ${DEADLINE};
const IN = (o) => encodeURIComponent(JSON.stringify(o));
let passes = 0, reqs = 0;

async function trpc(url) {
  reqs++;
  const r = await fetch(url, {credentials:'include'});
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const j = await r.json();
  const dd = j[0] && j[0].result && j[0].result.data;
  return dd && (dd.json !== undefined ? dd.json : dd);
}

async function board() {
  const p = {"0":{"json":{annotationProjectId:PROJ,pipelineStageId:null,attempters:null,
    search:null,sortBy:"default",sortOrder:"desc",limit:25,offset:0,
    categories:null,priorityLevel:null},
    "meta":{"values":{pipelineStageId:["undefined"],attempters:["undefined"],
    search:["undefined"],categories:["undefined"],priorityLevel:["undefined"]},"v":1}}};
  const a = await trpc(O + '/api/trpc/task.getAllClaimableTasksForFellow?batch=1&input=' + IN(p));
  return Array.isArray(a) ? a : ((a && (a.tasks || a.items)) || []);
}

async function held() {
  const d = await trpc(O + '/api/trpc/task.listClaimedTasksForFellow?batch=1&input=' +
    IN({"0":{"json":{annotationProjectId:PROJ}}}));
  return (d && d.activeTasks) || [];
}

// Returns the post-claim activeTasks list, or null if the id never appeared in it.
async function claim(id) {
  reqs++;
  await fetch(O + '/annotations/fellow/task/' + id + '/claim',
              {method:'GET', redirect:'manual', credentials:'include'});
  const now = await held();                 // the ONLY proof
  return now.some(t => t.id === id) ? now : null;
}

// returns true when the loop should stop for good
async function sweep() {
  passes++;
  const b = await board();                  // board FIRST
  if (!b.length) {                          // the usual case - this pass cost 1 request
    postMessage({t:'tick', pass:passes, boardSize:0, reqs:reqs,
                 leftMin: Math.round((END-Date.now())/60000)});
    return false;
  }

  const h = await held();
  if (h.length > BASE) {                    // something else claimed for us - do not pile up
    postMessage({t:'stop', held:h.length,
                 tasks:h.map(t=>({id:t.id, slug:t.data&&t.data.slug}))});
    return true;
  }

  let missed = 0;
  for (const it of b) {
    const after = await claim(it.id);
    if (after) {
      postMessage({t:'CLAIMED', id:it.id, slug: it.data && it.data.slug, held:after.length,
                   tasks:after.map(t=>({id:t.id, slug:t.data&&t.data.slug, status:t.status}))});
      return true;                          // ONE-SHOT: stop after one verified claim
    }
    missed++;
    postMessage({t:'missed', id:it.id, slug: it.data && it.data.slug});
    if (missed >= 3) {                      // board is stale, or the claim route changed
      postMessage({t:'abort', note:'3 consecutive claims did not verify'});
      return true;
    }
  }
  postMessage({t:'tick', pass:passes, boardSize:b.length, reqs:reqs,
               leftMin: Math.round((END-Date.now())/60000)});
  return false;
}

let wait = EVERY;

(async function loop() {
  if (Date.now() >= END) {                  // hard self-halt
    postMessage({t:'expired', passes:passes, reqs:reqs});
    return;
  }
  let done = false;
  try {
    done = await sweep();
    wait = EVERY;                           // healthy - back to the normal cadence
  } catch (e) {
    wait = Math.min(wait * 2, MAXWAIT);
    postMessage({t:'err', e:String(e).slice(0,150), retryIn:wait});
  }
  if (!done) setTimeout(loop, wait);        // re-arm only after this pass has finished
  else postMessage({t:'halted'});
})();
`;

window.__done = null;
window.__log  = [];
window.__w = new Worker(URL.createObjectURL(new Blob([src], {type:'application/javascript'})));
window.__w.onmessage = (ev) => {
  window.__log.push({at:new Date().toISOString(), ...ev.data});
  if (window.__log.length > 200) window.__log.shift();
  if (['CLAIMED','stop','expired','abort'].includes(ev.data.t)) window.__done = ev.data;
  document.title = window.__done ? ('DONE: ' + window.__done.t)
                                 : ('watching ' + window.__log.length);
};
```

Read progress with `JSON.stringify(window.__log.slice(-10), null, 2)`.
Stop it with `window.__w.terminate()`.

Message types in the log: `CLAIMED` (verified - the loop has stopped), `missed`
(the claim route returned but the id never appeared in `activeTasks`), `abort`
(three misses in a row), `stop` (holdings exceeded `BASE` by some other route),
`expired` (the deadline elapsed), `tick` (pass finished), `err` (a request
failed; carries the backoff `retryIn`).

---

## 7. Operating notes

### Read this before you automate anything

The program's own instructions (Project Instructions -> Workflow -> "1 · Claim
a task", at `project-dynamo.learn.joinhandshake.com/workflow/step-1`) settle
several questions this runbook previously answered by inference. Their wording,
not ours:

> **One active claim at a time.** "Keep your queue clean - finish or release the
> task you've claimed before picking up another. Parallel claims slow the whole
> pipeline down. This is about claiming a new build task from the queue - it
> doesn't restrict working on rework for a task you already own. If you're
> waiting on a rework PR's checks, claiming one new build task is fine; just
> don't stack multiple fresh claims."

So a multi-slot claimer is not merely unwise, it is against the documented
rule. The only sanctioned parallelism is one new build claim while an owned
task sits on rework checks. `BASE` in section 6 exists to enforce this: set it
to what you currently hold, and the run halts rather than stacking.

Two more from the same page:

- **"Only claim a task you fully intend to work on."** And if it turns out not
  to fit, there is an explicit **Release (or Abandon)** action - "don't sit on
  it."
- **"The platform records the claim timestamp, which starts your working
  window."** Claiming starts a clock. An unworked slot is not free; it is
  spending the window you would need to actually build the thing.

### There is no drop schedule - it is a release-fed queue

We looked for one. The instructions describe claiming as pulling from a queue
and make releasing explicit, which means tasks re-enter the pool whenever a
fellow opens one and decides it is not a fit. The API record confirms the
shape: a task sighted 2026-08-06 had `createdAt` of 2026-07-28 and an
`updatedAt` two seconds before we saw it. It was not newly dropped - its
`status` flipped back to `task_unclaimed` after nine days parked somewhere.

Practical consequence: **there is no window to camp on.** Sightings arrive at
whatever times other fellows happen to stop working. Five sightings we captured
landed at 19:43, 09:48, 09:49, 10:07 and 20:30 across three days - and the two
a minute apart are far more likely one person releasing two tasks than a
morning drop. Do not build a schedule out of that.

### The rest

- **Keep the tab VISIBLE.** This is the whole ballgame (section 5). A hidden
  tab gets frozen by Chrome and the worker stops, usually within minutes. Give
  it its own window, or park it as the active tab on a second monitor. Nothing
  else you do to the script matters more than this.
- **It dies on reload or navigation.** Everything lives in page memory. Arm it
  once, then leave that DEDICATED tab alone. Watch the tab title; if it stops
  updating, it is dead - but confirm with the lag check in 5a rather than
  trusting the title alone.
- **The first pass runs immediately**, not after one interval. The loop re-arms
  only once a pass has fully finished, so two passes can never overlap and race
  on the same task id - which the old `setInterval` version did whenever a board
  sweep ran longer than the interval.
- **An idle pass costs ONE request.** `held()` is fetched only when the board is
  non-empty, and the post-claim verification fetch is load-bearing (section 4)
  so it stays. Earlier versions fetched `held()` unconditionally every pass, and
  the version before that re-fetched it for every board item - ~50 requests per
  pass on a full board, telling you nothing.
- **Failed requests back off** by doubling up to `MAXWAIT`, resetting on the
  first clean pass. Without it, an outage or a 429 gets hammered at the full
  poll rate.
- **Be reasonable about the poll interval, and know what it buys you.** An
  earlier note here claimed "tasks stayed on the board for minutes, not
  seconds". **That is not what we measured.** In ~2 hours of polling across one
  evening, exactly ONE task appeared, and a 15-second poller lost it anyway -
  the claim came back unverified, so it went to someone else within a single
  poll interval. Two conclusions, and the second matters more than the first:
  - Sub-minute polling is not obviously worth it. 60s costs 60 requests/hour
    against 15s's ~480, for a difference in catch probability we could not
    measure.
  - The whole approach may not be worth it. One task per two hours, lost, is
    the actual observed yield. Check the board yourself a few times a day
    before building anything on this.
- **The terms permit less than you might assume, but more than we first
  guessed.** We read them (2026-08-04). The automation clauses target *account
  creation* by script and *bulk scraping* of marketplace data - neither
  describes claiming one task on your own authenticated session, and there is
  no provision anywhere about how tasks must be obtained. What does exist:
  "You must not attempt to restrict another user from using or enjoying the
  Service", and an unconditional "We reserve the right to refuse access to the
  Service to anyone for any reason at any time." So being clause-clean is not
  protection. **But the public ToS was never the binding document that
  mattered** - the Project Instructions carry the one-claim rule quoted at the
  top of this section, and that is program guidance you are actually operating
  under. A shared task pool means your claiming rate affects other contributors,
  not only you.
- **Claiming commits you to work.** Each claim takes a slot, starts that task's
  working-window clock, and hides the task from everyone else's queue. Do not
  set `BASE` higher than you intend to build. The program's guidance is to
  revise sent-back tasks before claiming new ones, and the hourly base is paid
  on submission with the bonus only at RTD - so a pile of open claims pays
  nothing and pulls time away from the work closest to the bonus.
- **There is a per-row `Claim` control**, distinct from the "Start task" button
  in section 1's table. The instructions say "Hit Claim on the row." We have
  never inspected what that control calls - it may well be the `/claim` route
  this runbook uses, but that is untested. If the route breaks, look here before
  digging through the bundle.
- **`task.claimNextTask` is untested at zero held.** Section 1 dismisses it on
  the strength of 37 failed calls - but every one of those was made while
  already holding tasks, which is exactly the condition under which "returns a
  task you already hold" is the expected result. Its behaviour when you hold
  nothing has never been measured. If you ever want to know, try it on a
  sighting while under your `BASE`, and cap the attempts - it is a mutation.
- Repos are `404` until a proposal is approved. Claiming gets you the task, not
  a repository.
- The task router has no claim-by-id mutation, so if the `/claim` route ever
  changes, look for `buildTaskClaimRoute` in the bundle again rather than
  searching the tRPC procedures.
