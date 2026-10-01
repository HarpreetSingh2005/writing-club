# LinkedIn Post

---

I stopped building AI agents as "agents."

I was deep into LangGraph — states, routing, structured handoffs, human-in-the-loop interrupts — and it hit me that every example I'd seen modelled the same thing: a set of generic workers. Researcher. Writer. Reviewer.

Useful. But not interesting.

The interesting question was one I couldn't shake:

**What if the agents weren't just "agents"?**

What if each one was a *person* in an actual organization? A department. A role with its own area of expertise, its own standard, and its own accountability?

And what if, instead of asking one model to solve everything, I built a small organization where every part has a narrow job and has to hand its work to someone else?

So I built one.

**Writing Club** — a multi-agent editorial organization on LangGraph.

A publication house, modelled as a 15-node state machine across five departments:

🎙️ **Intake** — Transcriber, Summarizer
🔭 **Planning** — Perspective Discovery, Department Librarian, Style Librarian
🔬 **Research** — Expert Research (one report per department lens)
✍️ **Editorial** — Insight Curator, Flow Architect, Article Writer, Feedback Router
🛡️ **Verification** — Draft Completeness Check, Auto Critics, Final Review

A rambling 4-minute voice memo goes in. A finished, voice-matched article comes out.

Three things I care more about than the output:

**1. Nobody finishes their own work.**
The Flow Architect doesn't approve its own outline. A critic screens it, then a human does. The Writer doesn't ship — a critic hunts for AI tells and clichés, then a human signs off. When something gets rejected, a Feedback Router reads the critique and decides *which department* is responsible for fixing it. "Make it better" becomes an addressable routing decision instead of a shrug.

**2. I drew a hard line at self-improvement.**
Critics can send work back for revision. The system will **never** rewrite its own prompts, code, graph, or state based on feedback. Self-modifying prompt pipelines are great demos and bad engineering — they drift silently and you lose the ability to explain why the output changed. Bounded, auditable correction is the honest version of the idea. The workflow criticises itself; it just isn't allowed to quietly rewrite its own job description.

**3. It can't die.**
Every task routes by intent — fast models for intake, stronger ones for prose. Keys fail over to the next one, then the next model, and finally a local Ollama model. A total cloud outage degrades quality but never halts the run.

The real goal was never "generate an article."

It was to **replicate how I actually think when I write** — as an executable system. The departments, the critique loops, the escalation paths, the persistent "Library Room" that remembers my voice across runs.

That's the part I've found genuinely fascinating: it's less a chatbot pipeline and more a **model of a workplace.**

Repo is public. Go argue with my routing logic — I'd love that.

`#LangGraph` `#AIEngineering` `#MultiAgentSystems` `#LLM` `#Python` `#GenerativeAI` `#AgentArchitecture`

---

## Shorter variant (if the above is too long)

---

I stopped building AI agents as "agents."

Every LangGraph example I'd seen modelled the same thing: generic workers. Researcher. Writer. Reviewer. Useful, but not interesting.

So I asked a different question — what if each agent was a **person** in a real organization? A department with its own expertise, standard, and accountability?

**Writing Club**: a publication house modelled as a 15-node LangGraph state machine.

A voice memo goes in. A finished, voice-matched article comes out.

What I care about isn't the output — it's the structure:

→ **Nobody finishes their own work.** Critics reject peers' drafts; a feedback router decides *which department* must fix it.
→ **A hard line at self-improvement.** The system critiques itself but will never rewrite its own prompts, code, or graph. Bounded and auditable beats clever and drifting.
→ **Human in the loop, twice.** It can't finish without asking a person.
→ **It can't die.** Multi-provider failover down to a local model.

The goal was never to generate an article.

It was to **replicate how I think when I write** — as a running system.

Repo's public. Tell me what I'd route differently.

`#LangGraph` `#MultiAgentSystems` `#AIEngineering` `#LLM` `#Python`

---

## One-liner / short post

---

I stopped building AI agents as "agents."

What if each one was a person in a real organization — a department with its own expertise, standard, and accountability?

I built **Writing Club**: a publication house as a 15-node LangGraph state machine. Voice memo in, finished article out.

Critics reject peers' drafts. A router decides who must fix it. It critiques itself but can't rewrite its own code.

The goal was never to generate an article — it was to replicate how I think when I write.

`#LangGraph` `#AIEngineering` `#MultiAgentSystems` `#LLM`
