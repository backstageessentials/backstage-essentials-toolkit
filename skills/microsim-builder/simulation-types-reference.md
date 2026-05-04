# Simulation Types Reference

Catalog of the seven templates with screenshots-in-prose, the customize block fields each one expects, and worked examples for two different course subjects.

## signal-flow-visualizer

What the student sees: a canvas with three input chips on the left and three output slots on the right, connected by a dim gray path. Drag an input chip to a slot; the path between them lights up in brand magenta and a label appears showing what the input becomes when it reaches the output.

Canonical Customize fields (subject neutral):

```javascript
const CONFIG = {
  title: "Path Selector",
  intro: "Drag a source to a target to see what happens at the connection.",
  inputs: [
    { id: "input_a", label: "Source A" },
    { id: "input_b", label: "Source B" },
    { id: "input_c", label: "Source C" },
  ],
  outputs: [
    { id: "output_x", label: "Target X" },
    { id: "output_y", label: "Target Y" },
    { id: "output_z", label: "Target Z" },
  ],
  // result[input.id][output.id] = "what the student sees when this pairing connects"
  results: {
    input_a: { output_x: "Result text for A to X.", output_y: "Result text for A to Y.", output_z: "Result text for A to Z." },
    input_b: { output_x: "Result text for B to X.", output_y: "Result text for B to Y.", output_z: "Result text for B to Z." },
    input_c: { output_x: "Result text for C to X.", output_y: "Result text for C to Y.", output_z: "Result text for C to Z." },
  },
};
```

Worked example, live event tech course: title "Audio Signal Flow," inputs are mic / wireless / playback, outputs are mains / monitors / broadcast.

Worked example, biology course: title "Neural Pathways," inputs are sensory neuron / interneuron / motor neuron, outputs are reflex arc / brain stem / spinal cord. Same template, different domain.

Worked example, civics course: title "How a Bill Becomes a Law," inputs are House bill / Senate bill / joint resolution, outputs are committee / floor vote / president's desk.

## circuit-load-calculator

The template name reflects its first worked example, but the shape is general: two or more sliders feed a formula, the output number updates live, and a status badge flips when the result crosses a threshold.

What the student sees: sliders for each input, a computed total, and a status badge ("Under capacity" or "Over capacity," or whatever pair of states fits the lesson). The threshold and the labels come from the customize block.

Canonical Customize fields (subject neutral):

```javascript
const CONFIG = {
  title: "Threshold Calculator",
  intro: "Slide each input. The output and the status update live.",
  inputs: [
    { id: "input_a", label: "Input A", min: 1, max: 30, step: 1, defaultValue: 10, unit: "" },
    { id: "input_b", label: "Input B", min: 50, max: 1000, step: 50, defaultValue: 200, unit: "" },
  ],
  output: {
    label: "Total",
    formula: (vals) => vals.input_a * vals.input_b,
    unit: "",
  },
  thresholdLabel: "Safe limit shown below",
  threshold: 1920,
  underMessage: "Under the limit.",
  overMessage: "Over the limit. Adjust an input.",
};
```

Worked example, live event tech course: title "20A Circuit Load Calculator," inputs are fixture count and watts per fixture, threshold is 1,920 W.

Worked example, sample coffee course: title "Brew Strength Calculator," inputs are bean weight and water weight, threshold is the 16-to-1 brew ratio.

Worked example, history course: title "How Many Soldiers Can a Colony Field?", inputs are colony population and willingness rate, threshold is the army size needed for a regional campaign.

## flashcard-deck

What the student sees: a card with a term on the front. Click the card; it flips to show the definition. Two buttons appear ("Got it" and "Missed"). Click one and the next card slides in. After the deck is done, a score summary shows up.

Customize fields:

```javascript
const CONFIG = {
  title: "Method Flashcards",
  intro: "Click a card to see the method that fits the morning.",
  cards: [
    { front: "Pour-over", back: "5 minutes, clean cup, one piece of gear." },
    { front: "Espresso", back: "Strong, small volume, requires a real machine." },
    { front: "Drip", back: "Walk away while it brews; needs the machine on the counter." },
    { front: "French press", back: "Body, 4 minute steep, OK if you do not mind grit." },
  ],
  doneMessage: "You went through them all. Re-run any time.",
};
```

Worked example, sample coffee course: as shown.

Worked example, live event tech course: title "Connector Flashcards," cards for XLR, TS, TRS, NL4, EtherCON, etc. Front is the name, back is the use case.

## decision-tree-explorer

What the student sees: a card showing one question with multiple-choice answers. Click an answer; the next card appears. After the final answer, a terminal card shows the outcome. A "Start over" button resets.

Customize fields:

```javascript
const CONFIG = {
  title: "Should I Lift This?",
  intro: "Answer the questions to find out the right move.",
  start: "q-wheels",
  nodes: {
    "q-wheels": {
      type: "question",
      question: "Has wheels?",
      choices: [
        { label: "Yes", next: "r-roll" },
        { label: "No", next: "q-weight" },
      ],
    },
    "q-weight": {
      type: "question",
      question: "Over 50 lbs or awkward?",
      choices: [
        { label: "No", next: "r-solo" },
        { label: "Yes", next: "r-team" },
      ],
    },
    "r-roll": { type: "result", title: "Roll it.", body: "Save your back. Most road cases roll." },
    "r-solo": { type: "result", title: "Lift solo.", body: "Hinge at hips, plan the path before you grip." },
    "r-team": { type: "result", title: "Call a team lift.", body: "'Need a hand on this one.' Lift on count." },
  },
};
```

Worked example, live event tech course: as shown.

Worked example, sample coffee course: title "Pick a Method," nodes for time-available / strength-wanted / walk-away questions, results for each method.

## timeline-scrubber

What the student sees: a horizontal timeline with stage markers, a scrubber knob the student drags, and a state panel below the timeline showing what is happening at the scrubbed-to moment.

Canonical Customize fields (subject neutral):

```javascript
const CONFIG = {
  title: "Process Timeline",
  intro: "Drag the scrubber or click a stage to see what is happening at each phase.",
  stages: [
    { id: "stage_1", label: "Stage 1", durationMin: 60,
      state: "What is happening during stage 1." },
    { id: "stage_2", label: "Stage 2", durationMin: 60,
      state: "What is happening during stage 2." },
    { id: "stage_3", label: "Stage 3", durationMin: 60,
      state: "What is happening during stage 3." },
  ],
};
```

Worked example, history course: title "The War for Independence (1775 to 1783)," stages are Lexington / Saratoga / Valley Forge / Yorktown / Treaty of Paris, state text describes what is happening on each front and why each turning point matters.

Worked example, live event tech course: title "Show Day Timeline," stages are Load-In / Sound Check / Doors / Show / Strike, state text describes the floor.

Worked example, biology course: title "Photosynthesis Across the Day," stages are dawn / morning / midday / evening, state text describes what the leaf is doing.

Worked example, sample coffee course: title "From Bean to Cup," stages are Roasted / Rested / Ground / Brewed.

## drag-and-drop-matcher

What the student sees: two columns. Left column has cards with terms; right column has slots labeled with definitions. Drag a card from the left, drop it in a slot. Correct matches lock and turn brand magenta; wrong matches snap back. After all matches are made, a score summary shows up.

Canonical Customize fields (subject neutral):

```javascript
const CONFIG = {
  title: "Match Term to Definition",
  intro: "Drag each term on the left to its matching definition on the right.",
  pairs: [
    { term: "Term A", definition: "Definition that pairs with term A." },
    { term: "Term B", definition: "Definition that pairs with term B." },
    { term: "Term C", definition: "Definition that pairs with term C." },
    { term: "Term D", definition: "Definition that pairs with term D." },
  ],
  doneMessage: "All matched. Wrong tries: {misses}.",
};
```

Worked example, history course: title "Match the Founder to the Idea," pairs are Jefferson / Adams / Hamilton / Madison matched to authorship of key documents and arguments.

Worked example, biology course: title "Organelle to Function," pairs are nucleus / mitochondrion / ribosome / endoplasmic reticulum matched to their cellular roles.

Worked example, live event tech course: title "Match the Connector to the Job," pairs are XLR / NL4 / TRS / powerCON matched to their signal types.

Worked example, literature course: title "Literary Device to Definition," pairs are simile / metaphor / hyperbole / personification matched to definitions and short examples.

## formula-explorer

What the student sees: a small canvas plot at the top, sliders below for each variable, a numeric output panel showing the result of the formula at the current slider values, and an annotation in prose ("Output rises with X, falls with Y").

Canonical Customize fields (subject neutral):

```javascript
const CONFIG = {
  title: "Formula Explorer",
  intro: "Move the sliders. The output and the curve update live.",
  variables: [
    { id: "x", label: "X", min: 0, max: 100, step: 1, defaultValue: 50 },
    { id: "k", label: "K", min: 1, max: 10, step: 1, defaultValue: 2 },
  ],
  output: {
    label: "Output",
    formula: (v) => v.x * v.k,
    unit: "",
    decimals: 0,
  },
  annotation: "Output rises with X and rises faster as K rises.",
  plot: {
    xVar: "x",
    yLabel: "y",
  },
};
```

Worked example, history course: title "How Many Soldiers Can a Colony Field?", variables are colony population and willingness rate, output is the number of available soldiers, plot shows soldiers vs. population at the current willingness rate.

Worked example, physics course: title "F = ma Explorer," variables are mass and acceleration, output is force in newtons.

Worked example, finance course: title "Compound Interest Explorer," variables are principal, rate, and years, output is the final balance.

Worked example, live event tech course: title "Voltage Drop Explorer," variables are cable length, current, and wire gauge, output is voltage drop in volts.

Worked example, sample coffee course: title "Brew Ratio Explorer," variables are bean weight and water weight, output is the brew ratio.

## Picking Between Calculator and Formula

The two look similar. The difference:

- **calculator** is for the student who wants the answer. Inputs go in, an answer comes out. The status badge ("Under capacity" / "Over capacity") gives a quick judgment.
- **formula** is for the student who wants to understand the *shape* of the function. The plot is the differentiator. The student moves a slider and watches the curve shift.

A lesson that says "use this formula to compute X" wants calculator. A lesson that says "you need to understand how X depends on Y" wants formula.

## Picking Between Flashcards and Matcher

- **flashcards** is one-at-a-time recall. Front shows a prompt, back shows the answer. Linear.
- **matcher** is set-relationship practice. The student sees all the terms and all the definitions at once and has to pair them. Builds the relationship structure, not just individual recall.

If the lesson teaches "memorize these N items," flashcards wins. If it teaches "understand how these N items relate to these other N items," matcher wins.

## Picking Between Timeline and Decision-Tree

- **timeline** is one process unfolding over time. The student sees what is happening at each moment.
- **decision-tree** is one decision the student walks down. The student picks a branch at each node.

Timeline is observation. Decision-tree is choice.

## Picking Between Signal-Flow and Timeline

- **signal-flow** is one signal moving through stages. The stages are spatial; the student picks where the signal goes.
- **timeline** is one stage moving through time. The stages are temporal; the student picks when to look.

If the lesson is about a path through gear, signal-flow. If the lesson is about phases of a process, timeline.
