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
