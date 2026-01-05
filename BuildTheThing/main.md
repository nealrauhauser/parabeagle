# The “Build The Thing” Front-End Shift Prompt Kit

## Quick Reference: Which Prompt When

| You are a... | You want to... | Use this prompt |
| --- | --- | --- |
| Builder | Clarify an idea before building | Builder's Brief |
| Builder | Hand off a prototype to engineering | Prototype Handoff |
| Engineer | Assess team readiness | Composability Audit |
| Engineer | Define rules for a component/pattern | UI Contract Definition |
| Engineering Manager | Justify headcount reallocation | Composability Audit → 90-day roadmap |
| PM who prototypes | Both clarify AND hand off | Builder's Brief → build → Prototype Handoff |

## FOR BUILDERS

### 1. The Builder's Brief

**Use this when:** You have an idea for something to build but haven't started yet. This prompt forces the clarity that separates useful prototypes from abandoned experiments.

**What it produces:** A one-page brief you can reference while building, share with stakeholders, or hand to engineers later.

```jsx
I want to build something, but I need to think it through before I start. Help me create a clear brief for my prototype.

If you don't have enough information to generate useful outputs, ask me questions until you have enough information.

---

## WHAT I'M THINKING ABOUT BUILDING

[Describe your idea in whatever state it's in—messy is fine]

---

## BRIEF OUTPUT

### The Problem
What specific problem does this solve? Be concrete—not "helps with productivity" but "I waste 2 hours every week manually copying data from X to Y."

### Who It's For
- Primary user: [specific person or role]
- Their current workaround: [how they solve this today]
- Why the workaround isn't good enough: [the pain point]

### The Simplest Version
If this prototype could only do ONE thing, what would it be? Strip away every feature until you hit the core. This is what you build first.

### Success Criteria
How will you know if this works? Not "people like it" but specific signals:
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
- [ ] [Measurable outcome 3]

### Must-Haves vs. Nice-to-Haves

**Must-haves (prototype is useless without these):**
- 
- 
- 

**Nice-to-haves (add if time permits):**
- 
- 
- 

**Explicitly out of scope (don't even start these):**
- 
- 

### Reality Check

Given current no-code tool limitations, this prototype:
- [ ] CAN realistically be built (single user, simple data, no complex integrations)
- [ ] CANNOT be built as described—here's what needs to change: [adjustments]

### The Build Plan

1. **First session (1-2 hours):** Build [core feature only]
2. **Second session (if needed):** Add [next priority feature]
3. **Stop when:** [specific completion criteria]

### One Sentence

This prototype lets [specific user] do [specific thing] instead of [current painful alternative].
```

---

### 2. Prototype-to-Production Handoff

**Use this when:** You built something in Lovable/Webflow that's ready to become a real product. This creates the documentation engineers need to build it properly—not copy your code, but understand your intent.

**What it produces:** A handoff document that captures decisions, constraints, and open questions so the production build starts from understanding, not guessing.

```jsx
I built a working prototype and now it needs to become production software. Help me document what I built so engineers can build it properly.

If you don't have enough information to generate useful outputs, ask me questions until you have enough information.

---

## THE PROTOTYPE

Link/access: [URL or how to access it]
Built in: [Lovable/Webflow/other]
Time invested: [rough hours]

### What It Does

Walk through the prototype like you're demoing it:

1. User arrives and sees...
2. They can do...
3. When they [action], the system...
4. The result is...

---

## HANDOFF DOCUMENTATION

### Core Functionality
What does this prototype actually do? List every feature, even small ones.

| Feature | What It Does | How Critical? |
|---------|--------------|---------------|
| | | Must-have / Nice-to-have / Cut it |

### Decisions I Made
Every prototype embeds decisions. Surface them so engineers don't have to guess.

| Decision | What I Chose | Why | Open to Change? |
|----------|--------------|-----|-----------------|
| [e.g., form has 3 fields] | Name, email, message | Kept it simple for v1 | Yes—might need more |
| [e.g., no user accounts] | Anonymous submissions | Faster to build | No—want to keep it simple |

### What's Intentional vs. Accidental
Some things in prototypes are deliberate. Some are just "that's how the tool did it."

**Intentional (preserve these):**
- [Design choice that matters]
- [Interaction that tested well]
- [Constraint that's actually a feature]

**Accidental (feel free to change):**
- [Default styling I didn't customize]
- [Limitation of the tool I worked around]
- [Thing that's there because I ran out of time]

### What's Missing
What would this need to be production-ready?

| Gap | Why It Matters | Priority |
|-----|----------------|----------|
| [e.g., error handling] | Users see broken states | High |
| [e.g., mobile optimization] | 60% of users on mobile | High |
| [e.g., analytics] | Can't measure success | Medium |

### User Feedback (If Any)
Did anyone use this prototype? What did you learn?

- [Feedback point 1]
- [Feedback point 2]
- [Unexpected behavior or request]

### Questions for Engineering

Things I don't know how to answer:
- [Technical question about scaling]
- [Question about integration with existing systems]
- [Security/compliance question]

### What Success Looks Like

The production version succeeds if:
- [ ] [Specific measurable outcome]
- [ ] [Specific measurable outcome]
- [ ] [Specific measurable outcome]

### One Thing to Preserve

If you only keep one thing from this prototype exactly as-is, it should be: [the core interaction/flow/feeling that makes it work]
```

---

## FOR ENGINEERS

### 3. Composability Readiness Audit

**Use this when:** You're assessing your team's readiness for a world where AI and non-engineers compose UI. Run quarterly, during reorgs, or when you're feeling the pain of inconsistency.

**What it produces:** A scored assessment across the four capabilities with specific gaps identified and a 90-day roadmap.

```jsx
Audit my front-end team's composability readiness. I want to understand where we are on each capability and what to prioritize.

If you don't have enough information to generate useful outputs, ask me questions until you have enough information.

---

## CURRENT STATE

### Team Structure
- Total front-end engineers: [number]
- Engineers doing implementation work: [number]
- Engineers doing composability/platform work: [number]
- Who owns your design system/component library: [name/role or "no one"]

### Existing Infrastructure
- Component library: [name, or "custom," or "none"]
- Design system documentation: [where it lives, or "scattered," or "none"]
- UI generation: [do you use any AI/automated UI generation? where?]

---

## CAPABILITY ASSESSMENT

### 1. Schema Definition
*Can you articulate what UI variations are allowed vs. forbidden?*

Current state:
- [ ] No documented variation rules—decisions happen ad hoc
- [ ] Style guide exists but isn't enforced programmatically
- [ ] Some components have typed props that constrain variations
- [ ] Comprehensive schema that generators can consume

Evidence: [describe what actually exists]

Gaps: [what's missing]

Score: [ ] 1-None [ ] 2-Emerging [ ] 3-Functional [ ] 4-Mature

### 2. Brand Consistency at Scale
*Do composed/generated UIs feel like one product?*

Current state:
- [ ] Screens built by different teams feel like different products
- [ ] Core elements (spacing, color, type) are consistent; details vary
- [ ] Strong consistency with documented exceptions
- [ ] Programmatic enforcement—inconsistency is hard to ship

Evidence: [describe what actually exists]

Gaps: [what's missing]

Score: [ ] 1-None [ ] 2-Emerging [ ] 3-Functional [ ] 4-Mature

### 3. Agent Auditability
*Can you track what AI/automated systems see and do in your UI?*

Current state:
- [ ] No tracking of agent interactions
- [ ] Basic session replay that doesn't distinguish agents from humans
- [ ] Agent actions logged but not tied to UI state
- [ ] Full audit trail: agent identity, permissions, UI state, actions taken

Evidence: [describe what actually exists]

Gaps: [what's missing]

Score: [ ] 1-None [ ] 2-Emerging [ ] 3-Functional [ ] 4-Mature

### 4. Generation Guardrails
*Do you have explicit rules about where AI can and can't modify UI?*

Current state:
- [ ] No AI generation, or AI can touch anything
- [ ] Informal understanding of "safe" vs. "sensitive" surfaces
- [ ] Documented boundaries but not enforced
- [ ] Programmatic guardrails that prevent generation in restricted areas

Evidence: [describe what actually exists]

Gaps: [what's missing]

Score: [ ] 1-None [ ] 2-Emerging [ ] 3-Functional [ ] 4-Mature

---

## AUDIT OUTPUT

### Overall Readiness Score
[Sum of four scores, out of 16]

- 4-6: Not ready. Composability is an aspiration, not a capability.
- 7-10: Emerging. Foundation exists but gaps create risk.
- 11-14: Functional. Core capabilities in place; optimize and extend.
- 15-16: Mature. Ready for scaled AI generation and distributed building.

### Priority Gaps
Rank the gaps by impact. What's hurting most right now?

1. [Gap]: Impact: [what breaks without this]
2. [Gap]: Impact: [what breaks without this]
3. [Gap]: Impact: [what breaks without this]

### 90-Day Roadmap

**Days 1-30: Foundation**
- [ ] [Specific action addressing highest-priority gap]
- [ ] [Specific action]
- [ ] Owner: [who]

**Days 31-60: Build**
- [ ] [Specific action]
- [ ] [Specific action]
- [ ] Owner: [who]

**Days 61-90: Extend**
- [ ] [Specific action]
- [ ] [Specific action]
- [ ] Owner: [who]

### Team Structure Recommendation

Current ratio (implementation : composability): [X:Y]

Recommended ratio for your maturity level: [A:B]

If rebalancing: [specific suggestion—who moves, what role changes, whether to hire]

### What to Stop Doing

Composability work often requires stopping something to make room:
- Stop: [activity that's low-value given the shift]
- Stop: [review/process that doesn't catch what matters anymore]
- Stop: [work that tools now handle adequately]
```

---

### 4. UI Contract Definition

**Use this when:** You're defining or revising the rules for a specific component, pattern, or interaction. Use it for new components, when inconsistency emerges, or when you're preparing a surface for AI generation.

**What it produces:** A machine-readable-ish contract that specifies what can vary, what's locked, and what's forbidden.

```jsx
Help me define a UI contract for a specific component or pattern. I want explicit rules about variation boundaries that both humans and AI can follow.

If you don't have enough information to generate useful outputs, ask me questions until you have enough information.

---

## THE COMPONENT/PATTERN

Name: [e.g., "Button," "Data Table," "Filter Bar," "Form Validation"]
Scope: [Is this one component, a pattern across components, or a full workflow?]
Current state: [Does this exist already? How inconsistent is it?]

---

## CONTRACT OUTPUT

### 1. Purpose Statement
What is this component/pattern FOR? One sentence that captures the job it does.

### 2. Allowed Variants

| Variant Name | When to Use | Visual/Behavioral Difference |
|--------------|-------------|------------------------------|
| [e.g., Primary] | [Main action on a page] | [Filled, brand color] |
| [e.g., Secondary] | [Supporting actions] | [Outlined, neutral] |
| [e.g., Ghost] | [Tertiary/cancel actions] | [Text only, no background] |

**Maximum variants:** [number]—if someone wants a new variant, they must justify why existing ones don't work.

### 3. Locked Properties
These CANNOT vary across instances. They're what make this recognizable as part of your product.

| Property | Locked Value | Rationale |
|----------|--------------|-----------|
| [e.g., Border radius] | [4px] | [Brand consistency] |
| [e.g., Font family] | [Inter] | [Typography system] |
| [e.g., Hover behavior] | [Opacity fade] | [Interaction consistency] |

### 4. Flexible Properties
These CAN vary within defined bounds.

| Property | Allowed Range | Default |
|----------|---------------|---------|
| [e.g., Width] | [Auto, fixed, full] | [Auto] |
| [e.g., Icon position] | [Left, right, none] | [Left] |
| [e.g., Size] | [sm, md, lg] | [md] |

### 5. Forbidden Combinations
Things that are technically possible but not allowed.

- [ ] [e.g., Ghost variant + destructive action—too subtle for dangerous operations]
- [ ] [e.g., Icon-only without aria-label—accessibility violation]
- [ ] [e.g., Custom colors outside palette—brand violation]

### 6. Interaction Contract
How does this behave? What's consistent across all instances?

| Interaction | Required Behavior |
|-------------|-------------------|
| [Hover] | [Specific response] |
| [Focus] | [Specific response] |
| [Active/Pressed] | [Specific response] |
| [Disabled] | [Specific response] |
| [Loading] | [Specific response, if applicable] |
| [Keyboard] | [Specific keys and behaviors] |

### 7. Accessibility Requirements
Non-negotiable accessibility properties.

- [ ] [e.g., Minimum contrast ratio: 4.5:1]
- [ ] [e.g., Focus indicator visible]
- [ ] [e.g., Touch target minimum: 44x44px]
- [ ] [e.g., Screen reader announcement: (specific pattern)]

### 8. Context Rules
Where can this appear? Where can't it?

**Allowed contexts:**
- [e.g., Forms, modals, page actions]

**Forbidden contexts:**
- [e.g., Inside other buttons, as table row actions (use icon buttons)]

### 9. Generation Rules
If AI is generating UI that includes this component:

**AI CAN:**
- [e.g., Select from allowed variants based on context]
- [e.g., Adjust flexible properties within bounds]

**AI CANNOT:**
- [e.g., Create new variants]
- [e.g., Override locked properties]
- [e.g., Use in forbidden contexts]

**AI MUST:**
- [e.g., Include loading state for async actions]
- [e.g., Pair destructive actions with confirmation]

### 10. Versioning
- Contract version: [e.g., 1.0]
- Last updated: [date]
- Owner: [who approves changes]
- Change process: [how do modifications get proposed and approved]
```
