# Simulation Types Reference

Catalog of the seven templates with screenshots-in-prose, the customize block fields each one expects, and worked examples for two different course subjects.

## signal-flow-visualizer

What the student sees: a canvas with three input chips on the left and three output slots on the right, connected by a dim gray path. Drag an input chip to a slot; the path between them lights up in brand magenta and a label appears showing what the input becomes when it reaches the output.

Customize fields:

```javascript
const CONFIG = {
  title: "Audio Signal Flow",
  intro: "Drag a source to an output to see the signal path.",
  inputs: [
    { id: "mic", label: "Mic" },
    { id: "wireless", label: "Wireless pack" },
    { id: "playback", label: "Playback" },
  ],
  outputs: [
    { id: "mains", label: "Mains" },
    { id: "monitors", label: "Monitor wedges" },
    { id: "broadcast", label: "Broadcast feed" },
  ],
  // result[input.id][output.id] = "what the student sees when this pairing connects"
  results: {
    mic: { mains: "Vocal in the room.", monitors: "Vocal in the wedge.", broadcast: "Live to broadcast." },
    wireless: { mains: "Wireless vocal in the room.", monitors: "Wireless in the wedge.", broadcast: "Wireless to broadcast." },
    playback: { mains: "Walk-in music.", monitors: "Click track to performer.", broadcast: "Bumper music." },
  },
};
```

Worked example, live event tech course: title "Audio Signal Flow," inputs are mic / wireless / playback, outputs are mains / monitors / broadcast. The result text uses the test course's working-tech voice.

Worked example, sample coffee course: not a great fit. Coffee does not have a "signal" with branching paths.

## circuit-load-calculator

What the student sees: two sliders ("How many fixtures?" and "Watts per fixture"), a computed total ("Total watts: 1,920 W") and a status badge ("Under capacity" or "Over capacity"). The threshold and the labels come from the customize block.

Customize fields:

```javascript
const CONFIG = {
  title: "20A Circuit Load Calculator",
  intro: "Slide to see how many fixtures a 20A circuit can carry.",
  inputs: [
    { id: "count", label: "Fixture count", min: 1, max: 30, step: 1, defaultValue: 10, unit: "" },
    { id: "watts", label: "Watts per fixture", min: 50, max: 1000, step: 50, defaultValue: 200, unit: " W" },
  ],
  output: {
    label: "Total load",
    formula: (vals) => vals.count * vals.watts,
    unit: " W",
  },
  thresholdLabel: "20A circuit at 120V tops out around 1,920 W safe",
  threshold: 1920,
  underMessage: "Under capacity. Plug in.",
  overMessage: "Over capacity. Drop a fixture or move to a second circuit.",
};
```

Worked example, live event tech course: as shown.

Worked example, sample coffee course: title "Brew Strength Calculator," sliders are "Bean weight (g)" and "Water weight (g)," output is the brew ratio, threshold is 1:16. Same template, different customize block.

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

What the student sees: a horizontal timeline with stage markers (Load-In, Sound Check, Doors, Show, Strike). A scrubber knob the student drags. Below the timeline, a state panel shows what is happening at the scrubbed-to moment ("Forklifts moving through the loading dock" / "Crowd entering" / etc.).

Customize fields:

```javascript
const CONFIG = {
  title: "Show Day Timeline",
  intro: "Drag the scrubber to see what is happening on the floor.",
  stages: [
    { id: "load-in", label: "Load-In", durationMin: 180,
      state: "Forklifts in the dock. Eyes up. Stop at corners." },
    { id: "sound-check", label: "Sound Check", durationMin: 90,
      state: "Mains live. Hearing protection in. Stay out of monitor world." },
    { id: "doors", label: "Doors", durationMin: 30,
      state: "House lights up. Crowd entering. Phone in pocket." },
    { id: "show", label: "Show", durationMin: 120,
      state: "Stage hot. Backstage corridors are working corridors only." },
    { id: "strike", label: "Strike", durationMin: 90,
      state: "Lights down. Cases out. Riggers in fall zones." },
  ],
};
```

Worked example, live event tech course: as shown.

Worked example, sample coffee course: title "From Bean to Cup," stages are Roasted / Rested / Ground / Brewed, state text describes the bean at each stage.

## drag-and-drop-matcher

What the student sees: two columns. Left column has cards with terms; right column has slots labeled with definitions. Drag a card from the left, drop it in a slot. Correct matches turn brand magenta and lock; wrong matches snap back. After all matches are made, a score summary shows up.

Customize fields:

```javascript
const CONFIG = {
  title: "Match the Connector to the Job",
  intro: "Drag each connector to where it belongs on the show floor.",
  pairs: [
    { term: "XLR", definition: "Microphone signal." },
    { term: "NL4 (speakON)", definition: "Speaker signal." },
    { term: "TRS 1/4 inch", definition: "Stereo or balanced line signal." },
    { term: "powerCON", definition: "Mains power into a fixture." },
  ],
  doneMessage: "All matched. Wrong tries: {misses}.",
};
```

Worked example, live event tech course: as shown.

Worked example, sample coffee course: title "Match the Method to the Morning," pairs are pour-over / espresso / drip / French press matched to morning scenarios.

## formula-explorer

What the student sees: a small canvas plot at the top, sliders below for each variable, a numeric output panel showing the result of the formula at the current slider values, and an annotation in prose ("Output rises with X, falls with Y").

Customize fields:

```javascript
const CONFIG = {
  title: "Voltage Drop Explorer",
  intro: "See how cable length and gauge change voltage drop on a feeder run.",
  variables: [
    { id: "length", label: "Cable length (ft)", min: 10, max: 200, step: 10, defaultValue: 100 },
    { id: "current", label: "Current (A)", min: 1, max: 40, step: 1, defaultValue: 20 },
    { id: "gauge", label: "Wire gauge (AWG)", min: 6, max: 18, step: 2, defaultValue: 12 },
  ],
  output: {
    label: "Voltage drop",
    formula: (v) => {
      // Simplified V_drop = 2 * I * R; R per 1000 ft from gauge
      const ohmsPer1000ft = { 6: 0.395, 8: 0.628, 10: 0.999, 12: 1.588, 14: 2.525, 16: 4.016, 18: 6.385 };
      const R = (ohmsPer1000ft[v.gauge] || 1.588) * (v.length / 1000);
      return Math.round(2 * v.current * R * 100) / 100;
    },
    unit: " V",
  },
  annotation: "Heavier wire (lower AWG number) means less drop. Doubling the run doubles the drop.",
  plot: {
    xVar: "length",
    yLabel: "V drop",
  },
};
```

Worked example, live event tech course: as shown.

Worked example, sample coffee course: title "Brew Ratio Explorer," variables are bean weight and water weight, output is the ratio (1:N), plot shows ratio vs. water at fixed bean.

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
