const fs = await import("node:fs/promises");
const path = await import("node:path");
const {
  Presentation,
  PresentationFile,
  column,
  row,
  grid,
  panel: rawPanel,
  text,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  grow,
  fr,
  auto,
} = await import("@oai/artifact-tool");
const { Canvas } = await import("../node_modules/@oai/artifact-tool/node_modules/skia-canvas/lib/index.js");
const { drawSlideToCtx } = await import("@oai/artifact-tool");

const W = 1920;
const H = 1080;
const OUT = "output/output.pptx";
const PREVIEWS = "scratch/previews";
const NOTES = "scratch/speaker-notes.md";

const C = {
  ink: "#13201C",
  muted: "#61736B",
  pale: "#F4F7F3",
  canvas: "#FBFCF8",
  line: "#CBD8D0",
  green: "#1E7A5A",
  greenDark: "#0F5D44",
  blue: "#2666A3",
  amber: "#D98C24",
  red: "#C84B3A",
  codeBg: "#111A1F",
  codeText: "#D9FBEA",
};

const font = "Aptos";
const mono = "Aptos Mono";

const presentation = Presentation.create({ slideSize: { width: W, height: H } });

function t(value, opts = {}) {
  return text(value, {
    width: opts.width ?? fill,
    height: opts.height ?? hug,
    name: opts.name,
    columnSpan: opts.columnSpan,
    rowSpan: opts.rowSpan,
    style: {
      fontFace: opts.fontFace ?? font,
      fontSize: opts.size ?? 28,
      color: opts.color ?? C.ink,
      bold: opts.bold ?? false,
      italic: opts.italic ?? false,
      alignment: opts.alignment,
      lineSpacingMultiple: opts.lineSpacingMultiple ?? 1.06,
    },
  });
}

function panel(opts = {}, childOrChildren = []) {
  const child = Array.isArray(childOrChildren)
    ? childOrChildren.length === 1
      ? childOrChildren[0]
      : column(
        {
          name: opts.name ? `${opts.name}-content` : undefined,
          width: fill,
          height: opts.height === fill ? fill : hug,
          gap: opts.childGap ?? 0,
        },
        childOrChildren,
      )
    : childOrChildren;
  return rawPanel(opts, child);
}

function code(value, opts = {}) {
  return text(value, {
    width: opts.width ?? fill,
    height: hug,
    name: opts.name,
    style: {
      fontFace: mono,
      fontSize: opts.size ?? 23,
      color: opts.color ?? C.codeText,
      lineSpacingMultiple: 1.12,
    },
  });
}

function slideRoot(slide, children, opts = {}) {
  slide.compose(
    panel(
      {
        name: opts.name ?? "slide-root",
        width: fill,
        height: fill,
        fill: opts.fill ?? C.canvas,
        padding: opts.padding ?? { x: 92, y: 72 },
      },
      children,
    ),
    { frame: { left: 0, top: 0, width: W, height: H }, baseUnit: 8 },
  );
}

function addTitle(slide, title, subtitle, bodyChildren, opts = {}) {
  slideRoot(slide, [
    column({ name: "content", width: fill, height: fill, gap: 42 }, [
      column({ name: "title-stack", width: fill, height: hug, gap: 14 }, [
        t(title, { name: "slide-title", size: opts.titleSize ?? 58, bold: true, width: wrap(opts.titleWidth ?? 1480) }),
        subtitle ? t(subtitle, { name: "slide-subtitle", size: 25, color: C.muted, width: wrap(1320) }) : null,
      ].filter(Boolean)),
      ...bodyChildren,
      footer(opts.footer),
    ]),
  ]);
}

function footer(label = "MCP Engineering Assistant Demo") {
  return row({ name: "footer", width: fill, height: hug, justify: "between", align: "end" }, [
    t(label, { name: "footer-label", size: 13, color: C.muted, width: wrap(680) }),
    t("Prepared for Elek discussion", { name: "footer-context", size: 13, color: C.muted, width: wrap(420), alignment: "right" }),
  ]);
}

function badge(label, color = C.green) {
  return row({ name: `badge-${label}`, width: hug, height: hug, gap: 10, align: "center" }, [
    panel({ name: `dot-${label}`, width: fixed(12), height: fixed(12), fill: color, borderRadius: "rounded-full" }),
    t(label, { size: 19, color: C.muted, width: hug }),
  ]);
}

function bullet(label, body, color = C.green) {
  return row({ name: `bullet-${label}`, width: fill, height: hug, gap: 18, align: "start" }, [
    panel({ name: `mark-${label}`, width: fixed(9), height: fixed(38), fill: color, borderRadius: "rounded-full" }),
    column({ name: `copy-${label}`, width: fill, height: hug, gap: 8 }, [
      t(label, { size: 30, bold: true }),
      t(body, { size: 23, color: C.muted, width: wrap(880) }),
    ]),
  ]);
}

function toolNode(name, desc, color) {
  return panel({ name: `tool-${name}`, width: fill, height: fixed(126), fill: "#FFFFFF", line: { color: C.line, width: 1 }, borderRadius: 18, padding: { x: 24, y: 20 } }, [
    column({ width: fill, height: fill, gap: 8 }, [
      t(name, { size: 26, bold: true, color }),
      t(desc, { size: 19, color: C.muted }),
    ]),
  ]);
}

function addCover() {
  const slide = presentation.slides.add();
  slideRoot(slide, [
    grid({ name: "cover-grid", width: fill, height: fill, columns: [fr(1.15), fr(0.85)], columnGap: 64 }, [
      column({ name: "cover-type", width: fill, height: fill, justify: "center", gap: 30 }, [
        badge("Prepared for Elek AI Software Engineer discussion", C.green),
        t("MCP Engineering\nAssistant Demo", { name: "cover-title", size: 86, bold: true, width: wrap(900), lineSpacingMultiple: 0.95 }),
        t("Multiple MCP tool servers for an LLM-powered engineering workflow.", { name: "cover-subtitle", size: 31, color: C.muted, width: wrap(800) }),
        rule({ name: "cover-rule", width: fixed(340), stroke: C.green, weight: 5 }),
        t("Sheng Chen", { name: "cover-name", size: 23, color: C.muted, width: hug }),
      ]),
      column({ name: "cover-system", width: fill, height: fill, justify: "center", gap: 18 }, [
        toolNode("docs_server", "retrieves sourceable engineering assumptions", C.blue),
        toolNode("calc_server", "runs deterministic voltage-drop calculation", C.green),
        toolNode("report_server", "generates structured Markdown reports", C.amber),
      ]),
    ]),
  ], { fill: C.pale });
}

function addSlide2() {
  const slide = presentation.slides.add();
  addTitle(slide, "Built around the exact request", "The goal was not a chatbot. It was tool architecture for an LLM agent.", [
    grid({ name: "quote-grid", width: fill, height: grow(1), columns: [fr(1.05), fr(0.95)], columnGap: 70 }, [
      column({ width: fill, height: fill, justify: "center", gap: 26 }, [
        t("“Build and document multiple MCP servers as tools for an LLM agent.”", { name: "ceo-quote", size: 52, bold: true, width: wrap(760), lineSpacingMultiple: 1.0 }),
        t("My response: a focused engineering assistant sample that separates language reasoning from reliable backend tools.", { size: 27, color: C.muted, width: wrap(760) }),
      ]),
      column({ width: fill, height: fill, justify: "center", gap: 34 }, [
        bullet("Learn MCP quickly", "Use the official Python MCP SDK and real stdio server/client calls.", C.blue),
        bullet("Keep calculations testable", "Put engineering logic behind typed, deterministic Python functions.", C.green),
        bullet("Document trade-offs", "Make scope, safety limitations, and extension paths explicit.", C.amber),
      ]),
    ]),
  ]);
}

function addSlide3() {
  const slide = presentation.slides.add();
  addTitle(slide, "Architecture: the host plans, MCP servers execute", "The servers stay independent; orchestration lives in the host/client layer.", [
    grid({ name: "architecture", width: fill, height: grow(1), columns: [fr(0.8), fr(0.2), fr(1.2)], columnGap: 34 }, [
      column({ width: fill, height: fill, justify: "center", gap: 26 }, [
        panel({ width: fill, height: fixed(128), fill: "#FFFFFF", line: { color: C.line, width: 1 }, borderRadius: 18, padding: { x: 28, y: 22 } }, [
          column({ width: fill, gap: 8 }, [
            t("User query", { size: 26, bold: true }),
            t("Natural-language engineering request", { size: 20, color: C.muted }),
          ]),
        ]),
        panel({ width: fill, height: fixed(168), fill: "#EAF4EF", line: { color: "#9CC8B8", width: 1 }, borderRadius: 18, padding: { x: 28, y: 22 } }, [
          column({ width: fill, gap: 8 }, [
            t("LLM host / deterministic host", { size: 26, bold: true, color: C.greenDark }),
            t("Chooses tools, tracks state, enforces workflow", { size: 20, color: C.muted }),
          ]),
        ]),
      ]),
      column({ width: fill, height: fill, justify: "center", gap: 46, align: "center" }, [
        t("→", { size: 64, color: C.green, alignment: "center" }),
        t("→", { size: 64, color: C.green, alignment: "center" }),
      ]),
      column({ width: fill, height: fill, justify: "center", gap: 18 }, [
        toolNode("docs_server", "search_docs · get_doc_section", C.blue),
        toolNode("calc_server", "calculate_voltage_drop", C.green),
        toolNode("report_server", "generate_engineering_report", C.amber),
        t("Key idea: LLM handles interpretation; MCP tools handle retrieval, calculations, and report formatting.", { size: 24, color: C.muted, width: wrap(760) }),
      ]),
    ]),
  ]);
}

function addSlide4() {
  const slide = presentation.slides.add();
  addTitle(slide, "Demo flow: retrieval → calculation → report", "The important point is where the result comes from: a deterministic MCP calculation tool.", [
    grid({ name: "demo-flow", width: fill, height: grow(1), columns: [fr(1.05), fr(0.95)], columnGap: 70 }, [
      column({ width: fill, height: fill, justify: "center", gap: 26 }, [
        t("Input", { size: 23, color: C.muted, bold: true }),
        t("50 m · 80 A · 415 V", { size: 66, bold: true, color: C.ink }),
        rule({ width: fixed(420), stroke: C.line, weight: 2 }),
        t("Tool result", { size: 23, color: C.muted, bold: true }),
        t("3.3778 V", { size: 72, bold: true, color: C.greenDark }),
        t("0.8139% voltage drop · within 5% demo threshold", { size: 28, color: C.muted, width: wrap(720) }),
      ]),
      column({ width: fill, height: fill, justify: "center", gap: 18 }, [
        panel({ width: fill, height: hug, fill: C.codeBg, borderRadius: 16, padding: { x: 26, y: 24 } }, [
          column({ width: fill, gap: 14 }, [
            code(".venv/bin/python examples/run_mcp_demo.py", { size: 24 }),
            code(".venv/bin/python examples/run_llm_agent.py --trace", { size: 24, color: "#A7F3D0" }),
          ]),
        ]),
        t("Simplified equation used", { size: 28, bold: true }),
        panel({ width: fill, height: hug, fill: "#FFFFFF", line: { color: C.line, width: 1 }, borderRadius: 14, padding: { x: 24, y: 20 } }, [
          column({ width: fill, gap: 10 }, [
            code("V_drop = sqrt(3) * I * L_km * (R cos(phi) + X sin(phi))", { size: 21, color: C.greenDark }),
            t("Demo-only formula, not a standards-compliance claim.", { size: 20, color: C.muted, width: wrap(680) }),
          ]),
        ]),
        t("Live-demo moment", { size: 30, bold: true }),
        t("Show the deterministic MCP path first; then show the LLM host trace if API/network is stable.", { size: 24, color: C.muted, width: wrap(690) }),
      ]),
    ]),
  ]);
}

function addSlide5() {
  const slide = presentation.slides.add();
  addTitle(slide, "Reliability is designed into the tool boundary", "The sample is small, but the engineering posture is the point.", [
    grid({ name: "reliability", width: fill, height: grow(1), columns: [fr(1), fr(1)], rows: [fr(1), fr(1)], columnGap: 52, rowGap: 38 }, [
      bullet("Typed inputs", "Pydantic validates current, length, voltage, impedance, power factor, and threshold.", C.green),
      bullet("Deterministic calculations", "The LLM does not estimate voltage drop; calc_server does.", C.blue),
      bullet("Source traceability", "Retrieved evidence includes filenames, section IDs, snippets, and scores.", C.amber),
      bullet("Explicit limitations", "Every generated report says this is not certified electrical design software.", C.red),
    ]),
  ]);
}

function addSlide6() {
  const slide = presentation.slides.add();
  addTitle(slide, "Tool calls are not orchestration", "The final artifact still needs host-owned structure and traceability.", [
    grid({ name: "bug-fix", width: fill, height: grow(1), columns: [fr(1), fr(1)], columnGap: 62 }, [
      column({ width: fill, height: fill, justify: "center", gap: 28 }, [
        t("What broke", { size: 38, bold: true, color: C.red }),
        t("The calculation was correct, but the LLM-host report could vary in wording, evidence choice, inputs, limitations, and tool trace.", { size: 28, color: C.ink, width: wrap(760) }),
        panel({ width: fill, height: hug, fill: "#FFF4EE", line: { color: "#F1B4A6", width: 1 }, borderRadius: 14, padding: { x: 22, y: 20 } }, [
          code("same calculation result\nbut inconsistent report artifact", { size: 22, color: "#7A251A" }),
        ]),
      ]),
      column({ width: fill, height: fill, justify: "center", gap: 28 }, [
        t("How I fixed it", { size: 38, bold: true, color: C.greenDark }),
        t("The host now owns the canonical report payload. The model can request the report tool, but the host supplies inputs, assumptions, limitations, evidence, and trace from MCP outputs.", { size: 27, color: C.ink, width: wrap(760) }),
        panel({ width: fill, height: hug, fill: C.codeBg, borderRadius: 14, padding: { x: 22, y: 20 } }, [
          code("host: fetch formula section if skipped\nreport args = canonical MCP outputs\nsaved artifact = report_server markdown", { size: 22 }),
        ]),
      ]),
    ]),
  ]);
}

function addSlide7() {
  const slide = presentation.slides.add();
  addTitle(slide, "Why this maps to Elek-style engineering software", "The electrical calculation is simplified. The software architecture is the signal.", [
    grid({ name: "mapping", width: fill, height: grow(1), columns: [fr(0.9), fr(1.1)], columnGap: 70 }, [
      column({ width: fill, height: fill, justify: "center", gap: 22 }, [
        t("My relevant bridge", { size: 34, bold: true, color: C.greenDark }),
        t("I have built scientific engineering software with validated inputs, deterministic calculations, scenario workflows, and structured reports.", { size: 31, width: wrap(720), lineSpacingMultiple: 1.08 }),
        t("This MCP demo uses the same pattern in a smaller AI-native engineering workflow.", { size: 25, color: C.muted, width: wrap(700) }),
      ]),
      column({ width: fill, height: fill, justify: "center", gap: 28 }, [
        bullet("Domain tools", "Add richer electrical calculations and standards-aware checks behind typed MCP tools.", C.green),
        bullet("Document intelligence", "Upgrade deterministic search to hybrid retrieval with versioned engineering evidence.", C.blue),
        bullet("Deployment path", "Wrap calculation services for AWS Lambda/API Gateway or hosted internal services.", C.amber),
        bullet("Operational trust", "Add logging, test coverage, audit trails, and human review gates.", C.red),
      ]),
    ]),
  ]);
}

addCover();
addSlide2();
addSlide3();
addSlide4();
addSlide5();
addSlide6();
addSlide7();

await fs.rm("output", { recursive: true, force: true });
await fs.mkdir("output", { recursive: true });
await fs.mkdir(PREVIEWS, { recursive: true });
const pptxBlob = await PresentationFile.exportPptx(presentation);
await pptxBlob.save(OUT);

const imported = await PresentationFile.importPptx((await fs.readFile(OUT)).buffer);
for (let i = 0; i < imported.slides.items.length; i += 1) {
  const canvas = new Canvas(W, H);
  const ctx = canvas.getContext("2d");
  await drawSlideToCtx(imported.slides.items[i], imported, ctx);
  await canvas.toFile(path.join(PREVIEWS, `slide-${String(i + 1).padStart(2, "0")}.png`), { format: "png" });
}

const notes = `# Speaker Notes: MCP Engineering Assistant Demo

## 1. Opening
I built this sample in response to the request to build and document multiple MCP servers as tools for an LLM agent. The goal is to show the architecture and engineering judgment, not to claim production electrical design capability.

## 2. Screening Request
The key phrase I optimized for was "multiple MCP servers as tools for an LLM agent." I treated that as a tool-boundary and orchestration problem, not just a chatbot prompt.

## 3. Architecture
The host interprets intent and coordinates the workflow. The MCP servers stay independent: retrieval, calculation, and report generation are separate responsibilities.

## 4. Demo
Run the deterministic demo first. Explain the simplified voltage-drop equation on the slide, then show that the numeric result comes from calc_server, not from the model. If the API/network is stable, run the LLM host with --trace.

## 5. Reliability
The design separates probabilistic language behavior from deterministic engineering functions. That makes validation, tests, traceability, and limitations much easier to reason about.

## 6. Bug/Fix
The LLM host initially exposed tools correctly, but the saved report could still vary because the model influenced report fields. I fixed that by making the host own the canonical report payload: inputs, assumptions, limitations, evidence, and tool trace come from prior MCP outputs.

## 7. Elek Fit
Although the demo calculation is simplified, the pattern maps to engineering software: validated inputs, deterministic calculations, source evidence, structured outputs, and reviewable limitations. My RO/scientific software background used similar engineering workflow ideas.
`;
await fs.writeFile(NOTES, notes, "utf8");

console.log(JSON.stringify({
  pptx: path.resolve(OUT),
  previews: path.resolve(PREVIEWS),
  notes: path.resolve(NOTES),
  slides: presentation.slides.items.length,
}, null, 2));
