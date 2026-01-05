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
