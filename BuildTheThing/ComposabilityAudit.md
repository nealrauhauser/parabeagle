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
