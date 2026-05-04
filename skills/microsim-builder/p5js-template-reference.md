# p5.js Template Reference

Cheat sheet for the p5.js patterns used inside the templates that need canvas drawing (signal-flow-visualizer, timeline-scrubber). Templates that are pure HTML+CSS+JS (calculator, flashcards, decision-tree, matcher, formula) do not use p5.js; only the canvas-driven templates do.

The skill rarely edits the p5.js code directly. The customize block exposes labels, ranges, and item lists; the p5.js machinery below the customize block reads from those and renders. This file documents the patterns so the skill can debug or extend a template if needed.

## Loading p5.js via CDN

Every p5-using template loads p5.js the same way:

```html
<script src="https://cdn.jsdelivr.net/npm/p5@1.9.0/lib/p5.min.js"></script>
```

This is the single stance: CDN, not bundled. Each MicroSim file stays small (under 350 lines, often well under). The cost is that previewing offline requires a one-time CDN fetch in cache, the same as Mermaid.

## The setup / draw Loop

p5.js calls `setup()` once when the page loads, then `draw()` 60 times per second. State lives in module-level variables.

```javascript
let state;

function setup() {
  createCanvas(600, 400).parent('canvas-container');
  state = { /* initial state */ };
}

function draw() {
  background('#FFFFFF');
  // render the current state
}
```

The `parent('canvas-container')` call attaches the canvas to a div in the page so it sits where the layout expects it. Without that call p5 appends the canvas to `<body>` directly and breaks the layout.

## Mouse Interaction

```javascript
function mousePressed() {
  // mouseX and mouseY are p5 globals scoped to the canvas
  for (const item of state.draggables) {
    if (isInside(mouseX, mouseY, item)) {
      state.dragging = item;
      return;
    }
  }
}

function mouseDragged() {
  if (state.dragging) {
    state.dragging.x = mouseX;
    state.dragging.y = mouseY;
  }
}

function mouseReleased() {
  if (state.dragging) {
    snapToTarget(state.dragging);
    state.dragging = null;
  }
}
```

`mousePressed`, `mouseDragged`, `mouseReleased` are p5.js callbacks. The skill never names these differently; the machinery looks for them by name.

## Rectangles, Circles, Lines

```javascript
fill('#FFFFFF');
stroke('#D6006C');
strokeWeight(2);
rect(x, y, width, height, 6);  // 6 = corner radius

fill('#D6006C');
noStroke();
circle(x, y, diameter);

stroke('#0A0A0A');
strokeWeight(1.5);
line(x1, y1, x2, y2);
```

The brand colors are hardcoded into each template's machinery. The customize block does not let the user override colors; the brand stays consistent.

## Text Inside Shapes

```javascript
fill('#0A0A0A');
noStroke();
textAlign(CENTER, CENTER);
textSize(14);
text(label, x + width / 2, y + height / 2);
```

`textAlign(CENTER, CENTER)` means horizontally and vertically centered around the given coordinates. Pair with shape coordinates that hand back the center point, or do the math as above.

## Animating a Path Light Up

The signal-flow visualizer animates by tracking a `progress` state variable that increments each frame.

```javascript
let progress = 0;

function draw() {
  background('#FFFFFF');
  drawPath();
  if (progress < 1) {
    progress = min(1, progress + 0.02);
  }
  drawTraveler(progress);
}
```

`progress` is 0 to 1 along the path. `drawTraveler(progress)` paints a circle at that fraction of the path. The animation completes in about a second at 60 fps.

## Sliders (HTML, not p5)

Sliders are HTML `<input type="range">` elements outside the canvas. The p5.js code reads their values:

```javascript
let weightSlider;

function setup() {
  weightSlider = select('#weight-slider');
  // ...
}

function draw() {
  const weight = parseFloat(weightSlider.value());
  // use weight in the rendering
}
```

`select('#weight-slider')` is a p5.js helper that wraps the DOM element. Calling `.value()` reads the current slider value. Pure-HTML templates use the same pattern with a plain `document.getElementById` plus an `input` event listener instead.

## Why p5 Only Where It Earns Its Place

p5.js is about 70 KB compressed. Loading it for a flashcard deck (which only needs DOM clicks) is wasteful. The seven templates split:

| Template | Uses p5? |
|----------|----------|
| signal-flow-visualizer | yes (drag and animate on canvas) |
| circuit-load-calculator | no (DOM sliders + computed text) |
| flashcard-deck | no (DOM cards + click handler) |
| decision-tree-explorer | no (DOM nodes + click handler) |
| timeline-scrubber | yes (canvas timeline with scrubber) |
| drag-and-drop-matcher | no (HTML5 drag-and-drop) |
| formula-explorer | yes (canvas plot + sliders) |

Three of seven use p5. The rest stay light.

## Debugging p5 in a MicroSim

Common failures:

- **Canvas appears at the bottom of the page instead of the layout slot.** The `parent('container-id')` call is missing from `setup()`.
- **Canvas is blank.** `setup()` ran but `draw()` is throwing. Open the browser dev tools console.
- **Mouse interaction does nothing.** `mousePressed` etc. are misspelled. p5 looks for the exact names.
- **Sliders work but nothing changes on canvas.** `draw()` is not reading the slider value, or the slider element is not selected by the right id.

When the skill writes a new MicroSim, it does not need to debug these because the machinery is the template. The template was tested once when written; the customize block changes only data, not behavior.
