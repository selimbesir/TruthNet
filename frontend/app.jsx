// TruthNet — Main App

const { useCallback } = React;

// =========================================================================
// THEME TOGGLE
// =========================================================================
function ThemeToggle({ theme, onToggle }) {
  return (
    <button
      onClick={onToggle}
      aria-label="Toggle color theme"
      className="relative transition-colors"
      style={{
        display: "inline-flex", alignItems: "center", gap: 8,
        padding: "5px 10px 5px 8px",
        background: "transparent",
        border: `1px solid ${TN.border}`,
        color: TN.ink2,
        fontFamily: "Inter, sans-serif", fontSize: 11,
        letterSpacing: "0.08em",
      }}
      onMouseEnter={(e)=> e.currentTarget.style.background = TN.surfaceSoft}
      onMouseLeave={(e)=> e.currentTarget.style.background = "transparent"}
    >
      <span style={{ display: "inline-grid", placeItems: "center", width: 16, height: 16 }}>
        {theme === "dark" ? (
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="3.2" stroke="currentColor" strokeWidth="1.2"/>
            {[0,45,90,135,180,225,270,315].map((a) => {
              const r1 = 5.4, r2 = 7;
              const rad = (a*Math.PI)/180;
              return <line key={a} x1={8+r1*Math.cos(rad)} y1={8+r1*Math.sin(rad)}
                            x2={8+r2*Math.cos(rad)} y2={8+r2*Math.sin(rad)}
                            stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>;
            })}
          </svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M11.5 9.5 A 5 5 0 0 1 6.5 4.5 A 5 5 0 1 0 11.5 9.5 Z"
                  stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinejoin="round"/>
          </svg>
        )}
      </span>
      <span>{theme === "dark" ? "LIGHT" : "DARK"}</span>
    </button>
  );
}

// =========================================================================
// ANIMATED DIAGRAM — intro graphic explaining the 4-agent pipeline
// =========================================================================
function TruthNetDiagram() {
  return (
    <div className="tn-diagram w-full">
      <svg viewBox="0 0 720 300" className="w-full h-auto block" preserveAspectRatio="xMidYMid meet">
        <defs>
          <marker id="tn-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L10,5 L0,10" fill="none" stroke="var(--border)" strokeWidth="1.2" strokeLinejoin="round" strokeLinecap="round"/>
          </marker>
        </defs>

        {/* Connections */}
        <path className="flow" markerEnd="url(#tn-arrow)" d="M 120 150 H 178" />
        <path className="flow" markerEnd="url(#tn-arrow)" d="M 280 150 C 305 150, 305 75, 338 75" />
        <path className="flow" markerEnd="url(#tn-arrow)" d="M 280 150 C 305 150, 305 225, 338 225" />
        <path className="flow" markerEnd="url(#tn-arrow)" d="M 480 75  C 505 75, 505 150, 538 150" />
        <path className="flow" markerEnd="url(#tn-arrow)" d="M 480 225 C 505 225, 505 150, 538 150" />
        <path className="flow" markerEnd="url(#tn-arrow)" d="M 620 150 H 638" />

        {/* CLAIM */}
        <g className="node-claim">
          <rect className="node-bg" x="20" y="118" width="100" height="64" rx="2"/>
          <text className="node-label" x="70" y="138" textAnchor="middle">Input</text>
          <text className="node-name"  x="70" y="160" textAnchor="middle">Claim</text>
          <text x="70" y="175" textAnchor="middle"
                style={{ fill: "var(--muted)", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}>
            user text
          </text>
        </g>

        {/* Agent A */}
        <g className="node-a">
          <rect className="node-bg" x="178" y="118" width="102" height="64" rx="2"/>
          <text className="node-label" x="229" y="138" textAnchor="middle">§1 · Agent A</text>
          <text className="node-name"  x="229" y="160" textAnchor="middle">Extract</text>
          <text x="229" y="175" textAnchor="middle"
                style={{ fill: "var(--muted)", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}>
            atomic claims
          </text>
        </g>

        {/* Agent B — Prosecution */}
        <g className="node-b">
          <rect className="node-bg" x="338" y="42" width="142" height="66" rx="2"/>
          <text className="node-label" x="409" y="62" textAnchor="middle" style={{ fill: "var(--v-false-fg)" }}>§2 · Agent B</text>
          <text className="node-name"  x="409" y="84" textAnchor="middle">Prosecution</text>
          <text x="409" y="99" textAnchor="middle"
                style={{ fill: "var(--muted)", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}>
            argues FALSE
          </text>
        </g>

        {/* Agent C — Defense */}
        <g className="node-c">
          <rect className="node-bg" x="338" y="192" width="142" height="66" rx="2"/>
          <text className="node-label" x="409" y="212" textAnchor="middle" style={{ fill: "var(--v-true-fg)" }}>§3 · Agent C</text>
          <text className="node-name"  x="409" y="234" textAnchor="middle">Defense</text>
          <text x="409" y="249" textAnchor="middle"
                style={{ fill: "var(--muted)", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}>
            argues TRUE
          </text>
        </g>

        {/* Agent D */}
        <g className="node-d">
          <rect className="node-bg" x="538" y="118" width="82" height="64" rx="2"/>
          <text className="node-label" x="579" y="138" textAnchor="middle">§4 · D</text>
          <text className="node-name-sm" x="579" y="160" textAnchor="middle">Judge</text>
          <text x="579" y="175" textAnchor="middle"
                style={{ fill: "var(--muted)", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}>
            weigh both
          </text>
        </g>

        {/* VERDICT */}
        <g className="node-verdict">
          <rect className="node-bg" x="638" y="118" width="72" height="64" rx="2"/>
          <text className="node-label" x="674" y="138" textAnchor="middle">Output</text>
          <text className="verdict-text-idle"
                x="674" y="162" textAnchor="middle"
                style={{ fill: "var(--ink)", fontFamily: "Lora, serif", fontSize: 14, fontWeight: 700 }}>
            Verdict
          </text>
          <text className="verdict-text-final"
                x="674" y="162" textAnchor="middle"
                style={{ fill: "var(--v-false-fg)", fontFamily: "Lora, serif", fontSize: 14, fontWeight: 700, letterSpacing: "0.05em" }}>
            FALSE
          </text>
          <text x="674" y="176" textAnchor="middle"
                style={{ fill: "var(--muted)", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}>
            stamped
          </text>
        </g>

        {/* small caption helpers */}
        <text x="10" y="20"
              style={{ fill: "var(--muted)", fontFamily: "Inter, sans-serif", fontSize: 9, letterSpacing: "0.18em", textTransform: "uppercase", fontWeight: 600 }}>
          Judgment Pipeline · 4 Agents
        </text>
        <text x="710" y="20" textAnchor="end"
              style={{ fill: "var(--muted)", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}>
          fig. 1
        </text>

        {/* axis-like baseline between B and C to emphasize "vs" */}
        <line x1="409" y1="120" x2="409" y2="180" stroke="var(--border-soft)" strokeWidth="1" strokeDasharray="2 3"/>
        <text x="409" y="156" textAnchor="middle"
              style={{ fill: "var(--muted)", fontFamily: "Lora, serif", fontStyle: "italic", fontSize: 11 }}>
          vs.
        </text>
      </svg>
    </div>
  );
}

// =========================================================================
// MASTHEAD
// =========================================================================
function Masthead({ theme, onToggleTheme }) {
  return (
    <header style={{ borderBottom: `1px solid ${TN.border}`, background: TN.bg }}>
      <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between gap-6">
        <div className="flex items-center gap-3">
          <svg width="28" height="34" viewBox="0 0 28 34" fill="none">
            <path d="M14 1 L26 6 V18 C26 25 20 30 14 33 C8 30 2 25 2 18 V6 L14 1 Z"
                  stroke={TN.ink} strokeWidth="1.2" fill={TN.surfaceSoft} />
            <text x="14" y="20" textAnchor="middle"
                  fontFamily="Lora, serif" fontSize="11" fontWeight="700" fill={TN.ink}>TN</text>
          </svg>
          <div>
            <div style={{ fontFamily: "Lora, serif", fontWeight: 700, fontSize: 26, letterSpacing: "-0.01em", color: TN.ink, lineHeight: 1 }}>
              TruthNet
            </div>
            <div style={{ fontFamily: "Inter, sans-serif", fontSize: 11, color: TN.muted, letterSpacing: "0.15em", textTransform: "uppercase", marginTop: 4 }}>
              A Journal of Adversarial Fact-Checking
            </div>
          </div>
        </div>
        <div className="flex items-center gap-5">
          <div className="hidden md:flex flex-col items-end gap-1" style={{ fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 10.5, color: TN.muted }}>
            <span>Vol. 1 · Issue 04 · ISSN 0000–0000</span>
            <span>{new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</span>
          </div>
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
      </div>
    </header>
  );
}

// =========================================================================
// LEFT TOC
// =========================================================================
function LeftTOC({ status }) {
  const items = [
    { id: "verdict", label: "Verdict",           num: "1" },
    { id: "detail",  label: "Detailed Analysis", num: "2" },
  ];
  const [active, setActive] = useState("verdict");
  useEffect(() => {
    if (status !== "done") return;
    const onScroll = () => {
      let cur = "verdict";
      for (const it of items) {
        const el = document.getElementById(it.id);
        if (el && el.getBoundingClientRect().top < 120) cur = it.id;
      }
      setActive(cur);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, [status]);

  return (
    <nav className="hidden lg:block sticky" style={{ top: 24, alignSelf: "start" }}>
      <SectionLabel className="mb-4">Contents</SectionLabel>
      <ol className="relative flex flex-col">
        <div className="absolute left-[7px] top-2 bottom-2 w-px"
             style={{ background: `repeating-linear-gradient(to bottom, ${TN.border} 0 3px, transparent 3px 6px)` }} />
        {items.map((it) => {
          const isActive = active === it.id;
          return (
            <li key={it.id} className="relative pl-6 py-1.5">
              <span style={{
                position: "absolute", left: 4, top: 12,
                width: 7, height: 7, borderRadius: 999,
                background: isActive ? TN.ink : TN.bg,
                border: `1px solid ${isActive ? TN.ink : TN.border}`,
              }} />
              <a href={`#${it.id}`} style={{
                display: "block", fontFamily: "Inter, sans-serif", fontSize: 12.5,
                color: isActive ? TN.ink : TN.ink2, textDecoration: "none",
                fontWeight: isActive ? 600 : 400,
              }}>
                <span style={{ color: TN.muted, marginRight: 6, fontFamily: "JetBrains Mono, monospace", fontSize: 10 }}>§{it.num}</span>
                {it.label}
              </a>
            </li>
          );
        })}
      </ol>
      <div className="mt-6 pt-4" style={{ borderTop: `1px solid ${TN.borderSoft}` }}>
        <SectionLabel className="mb-2">Status</SectionLabel>
        <div style={{ fontFamily: "Inter, sans-serif", fontSize: 12, color: TN.ink2 }}>
          {status === "idle" && "Awaiting submission"}
          {status === "loading" && "Judgment in progress…"}
          {status === "done" && "Verdict published"}
          {status === "error" && "Processing error"}
        </div>
      </div>
    </nav>
  );
}

// =========================================================================
// IDLE INTRO — animated graphic instead of an explanatory paragraph
// =========================================================================
function IdleIntro() {
  return (
    <section id="abstract">
      <SectionLabel>Abstract</SectionLabel>
      <h1 className="mt-3" style={{
        fontFamily: "Lora, serif", fontWeight: 700, fontSize: 44, lineHeight: 1.1,
        letterSpacing: "-0.015em", color: TN.ink,
      }}>
        Truth, on trial.
      </h1>

      <div className="mt-10 tn-fade-up" style={{
        background: TN.surfaceSoft, border: `1px solid ${TN.borderSoft}`,
        padding: "22px 22px 14px",
      }}>
        <TruthNetDiagram />
      </div>

      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 items-center"
           style={{ fontFamily: "Inter, sans-serif", fontSize: 12, color: TN.muted }}>
        <span>· Median judgment time: 16.4s</span>
        <span>· Source corpus: web + curated archives</span>
        <span>· 4 independent agents per claim</span>
      </div>
    </section>
  );
}

function ClaimEcho({ text }) {
  return (
    <section id="claims" className="scroll-mt-8">
      <H2 num="2">Submitted Claim</H2>
      <div className="mt-5" style={{
        background: TN.surface, border: `1px solid ${TN.border}`,
        padding: "20px 22px", borderLeft: `3px solid ${TN.accent}`,
      }}>
        <SectionLabel className="mb-2">Claim under review</SectionLabel>
        <p style={{ fontFamily: "Lora, serif", fontStyle: "italic", fontSize: 18, lineHeight: 1.55, color: TN.ink }}>
          “{text}”
        </p>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1"
             style={{ fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 11, color: TN.muted }}>
          <span>received: {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}</span>
          <span>tokens: ~{Math.ceil(text.length / 4)}</span>
        </div>
      </div>
    </section>
  );
}

function ErrorState({ onRetry, message }) {
  return (
    <div className="my-12" style={{
      background: "var(--v-false-bg)",
      border: `1px solid color-mix(in srgb, var(--v-false-fg) 35%, transparent)`,
      padding: "20px 22px",
    }}>
      <SectionLabel className="mb-2">Processing Error</SectionLabel>
      <div style={{ fontFamily: "Lora, serif", fontSize: 17, color: "var(--v-false-fg)", marginBottom: 8 }}>
        The agent panel could not complete the judgment.
      </div>
      <p style={{ fontFamily: "Inter, sans-serif", fontSize: 13, color: TN.ink2 }}>
        {message || "The backend stream returned an error before all four agents reported. Try again after confirming the backend is running."}
      </p>
      <button onClick={onRetry} className="mt-4 px-3 py-1.5"
              style={{ fontFamily: "Inter, sans-serif", fontSize: 12, background: TN.ink, color: TN.bg }}>
        Retry submission →
      </button>
    </div>
  );
}

// =========================================================================
// DETAILED ANALYSIS — collapsible wrapper, closed by default
// =========================================================================
function DetailedAnalysis({ result, inputText }) {
  const [open, setOpen] = useState(false);
  return (
    <section id="detail" className="scroll-mt-8">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-4 py-4 text-left transition-colors"
        style={{
          borderTop: `1px solid ${TN.border}`,
          borderBottom: open ? `1px solid ${TN.border}` : `1px solid ${TN.borderSoft}`,
          background: "transparent",
        }}
        onMouseEnter={(e)=> e.currentTarget.style.background = TN.surfaceSoft}
        onMouseLeave={(e)=> e.currentTarget.style.background = "transparent"}
      >
        <span style={{
          width: 28, height: 28, display: "grid", placeItems: "center",
          border: `1px solid ${TN.border}`,
          fontFamily: "JetBrains Mono, monospace", fontSize: 15,
          transition: "background 0.2s, color 0.2s",
          background: open ? TN.ink : "transparent",
          color: open ? TN.bg : TN.ink,
        }}>{open ? "−" : "+"}</span>
        <div className="flex-1">
          <SectionLabel>§2 · Detailed Analysis</SectionLabel>
          <div style={{ fontFamily: "Lora, serif", fontSize: 20, fontWeight: 600, color: TN.ink, marginTop: 2, lineHeight: 1.2 }}>
            {open ? "Methodology, briefs, appendices & references" : "Expand the full judgment record"}
          </div>
        </div>
        <span style={{ fontFamily: "Inter, sans-serif", fontSize: 11, color: TN.muted, letterSpacing: "0.08em", textTransform: "uppercase" }}>
          {open ? "Collapse" : "Expand"}
        </span>
      </button>

      {open && (
        <div className="tn-fade-up">
          <div className="mt-10">
            <ClaimEcho text={inputText || MOCK_CLAIM} />
          </div>

          <Rule />
          <ProsecutionDefense result={result} />

          <Rule />
          <DetailedExplanation result={result} />

          <Rule />
          <EvidencePanel result={result} />

          <Rule />
          <SourceList sources={result.top_sources} />
        </div>
      )}
    </section>
  );
}

// =========================================================================
// APP
// =========================================================================
function App() {
  const [inputText, setInputText] = useState("");
  const [status, setStatus] = useState("idle");
  const [step, setStep] = useState(0);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem("truthnet-theme") || "light"; }
    catch { return "light"; }
  });
  const timersRef = useRef([]);
  const requestRef = useRef(null);
  const briefsRef = useRef({});
  const backendLabel = window.location.protocol === "file:"
    ? "127.0.0.1:8000"
    : window.location.host;

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("truthnet-theme", theme); } catch {}
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(t => (t === "dark" ? "light" : "dark"));
  }, []);

  const clearTimers = () => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  };

  const abortCurrentRequest = () => {
    if (requestRef.current) {
      requestRef.current.abort();
      requestRef.current = null;
    }
  };

  const apiUrl = () => {
    if (window.TRUTHNET_API_URL) return window.TRUTHNET_API_URL;
    if (window.location.protocol === "http:" || window.location.protocol === "https:") {
      return `${window.location.origin}/fact-check`;
    }
    return "http://127.0.0.1:8000/fact-check";
  };

  const applyStreamEvent = (event) => {
    if (event.status === "agent_a_running") setStep(0);
    if (event.status === "agent_a_done") setStep(1);
    if (event.status === "agents_bc_running") setStep(2);
    if (event.status === "agents_bc_done") {
      setStep(2);
      briefsRef.current = { agent_b: event.data?.agent_b, agent_c: event.data?.agent_c };
    }
    if (event.status === "agent_d_running") setStep(3);
    if (event.status === "agent_d_done") setStep(3);

    if (event.status === "error") {
      throw new Error(event.message || "Backend stream failed.");
    }

    if (event.result) {
      setResult({ ...briefsRef.current, ...event.result });
      setStep(4);
      setStatus("done");
    }
  };

  const parseSseBlock = (block) => {
    const dataLine = block
      .split("\n")
      .find((line) => line.startsWith("data: "));
    if (!dataLine) return null;
    return JSON.parse(dataLine.slice(6));
  };

  const submit = useCallback(async () => {
    const claim = inputText.trim();
    if (!claim) return;
    clearTimers();
    abortCurrentRequest();
    setStatus("loading");
    setStep(0);
    setResult(null);
    briefsRef.current = {};
    setErrorMessage("");

    const controller = new AbortController();
    requestRef.current = controller;

    try {
      const response = await fetch(apiUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: claim }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Backend returned ${response.status}: ${detail || response.statusText}`);
      }
      if (!response.body) {
        throw new Error("This browser did not expose a readable response stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() || "";

        for (const block of blocks) {
          const event = parseSseBlock(block.trim());
          if (event) applyStreamEvent(event);
        }

        if (done) break;
      }

      const finalEvent = parseSseBlock(buffer.trim());
      if (finalEvent) applyStreamEvent(finalEvent);
    } catch (error) {
      if (error.name === "AbortError") return;
      setErrorMessage(error.message || "Could not connect to the TruthNet backend.");
      setStatus("error");
    } finally {
      if (requestRef.current === controller) requestRef.current = null;
    }
  }, [inputText]);

  const loadDemo = () => {
    clearTimers();
    abortCurrentRequest();
    setInputText(MOCK_CLAIM);
    setResult(null);
    setErrorMessage("");
    setStep(0);
    setStatus("idle");
    setTimeout(() => window.scrollTo({ top: 0, behavior: "smooth" }), 50);
  };

  const reset = () => {
    clearTimers();
    abortCurrentRequest();
    setStatus("idle");
    setStep(0);
    setResult(null);
    setErrorMessage("");
    setTimeout(() => window.scrollTo({ top: 0, behavior: "smooth" }), 50);
  };

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [submit]);

  useEffect(() => () => {
    clearTimers();
    abortCurrentRequest();
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: TN.bg, color: TN.ink }}>
      <Masthead theme={theme} onToggleTheme={toggleTheme} />

      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="grid gap-10 grid-cols-1 lg:grid-cols-[180px_1fr]">
          <LeftTOC status={status} />

          <div className="min-w-0">
            {status === "idle" && <IdleIntro />}
            <div className={status === "idle" ? "mt-10" : ""}>
              <ChatInput
                value={inputText}
                onChange={setInputText}
                onSubmit={submit}
                onLoadDemo={loadDemo}
                status={status}
              />
            </div>

            {(status === "loading" || status === "done") && (
              <div className="mt-8">
                <PipelineStatus step={step} />
              </div>
            )}

            {status === "error" && <ErrorState onRetry={submit} message={errorMessage} />}

            {status === "done" && result && (
              <>
                <Rule />
                {/* Verdict + manipulation alert sit in a 2-col grid on xl screens.
                    On smaller screens the alert stacks beneath. */}
                <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-8 items-start">
                  <VerdictCard result={result} />
                  <ManipulationAlert techniques={result.manipulation_techniques_detected} />
                </div>

                <div className="mt-12">
                  <DetailedAnalysis result={result} inputText={inputText} />
                </div>

                <div className="mt-12 mb-8 flex items-center justify-between gap-4 flex-wrap"
                     style={{ borderTop: `1px solid ${TN.border}`, paddingTop: 18 }}>
                  <div style={{ fontFamily: "Inter, sans-serif", fontSize: 11, color: TN.muted, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                    — End of judgment —
                  </div>
                  <button onClick={reset} className="px-3 py-1.5"
                          style={{ fontFamily: "Inter, sans-serif", fontSize: 12, background: "transparent",
                                   border: `1px solid ${TN.border}`, color: TN.ink2 }}>
                    Submit another claim →
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </main>

      <footer style={{ borderTop: `1px solid ${TN.border}`, background: TN.surfaceSoft }}>
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-wrap items-center justify-between gap-3"
             style={{ fontFamily: "Inter, sans-serif", fontSize: 11, color: TN.muted }}>
          <span>© TruthNet · An open judgment protocol</span>
          <span style={{ fontFamily: "JetBrains Mono, monospace" }}>v0.4.1 · {backendLabel}</span>
          <span>Made for clear thinking.</span>
        </div>
      </footer>
    </div>
  );
}

// =========================================================================
// PROSECUTION & DEFENSE
// =========================================================================
function ProsecutionDefense({ result }) {
  return (
    <section className="scroll-mt-8">
      <H2 num="3">Prosecution & Defense — Agent Briefs</H2>
      <p className="mt-3" style={{ fontFamily: "Inter, sans-serif", fontSize: 13, color: TN.ink2, lineHeight: 1.55 }}>
        Agents B and C operate in parallel from opposing stances. Their findings — summarized
        below — are passed to Agent D for judgment.
      </p>
      <div className="mt-6 grid md:grid-cols-2 gap-px" style={{ background: TN.border }}>
        <Brief
          who="Agent B" role="Prosecution"
          tone="var(--v-false-fg)" tint="var(--v-false-bg)"
          posture="Argues the claim is false or misleading"
          brief={result?.agent_b}
          fallbackFindings={result?.what_is_false ?? []}
          glyph="✗"
        />
        <Brief
          who="Agent C" role="Defense"
          tone="var(--v-true-fg)" tint="var(--v-true-bg)"
          posture="Argues the claim has supportable elements"
          brief={result?.agent_c}
          fallbackFindings={result?.what_is_true ?? []}
          glyph="✓"
        />
      </div>
    </section>
  );
}

function briefSource(source) {
  const text = String(source || "").trim();
  if (!/^https?:\/\//i.test(text)) return { label: text, href: null };
  try {
    return { label: new URL(text).hostname.replace(/^www\./, ""), href: text };
  } catch (error) {
    return { label: text, href: null };
  }
}

function Brief({ who, role, tone, tint, posture, brief, fallbackFindings, glyph }) {
  // The agent's own brief arrives with the stream; older payloads only carry the Judge's lists.
  const evidence = Array.isArray(brief?.key_evidence) ? brief.key_evidence.filter((e) => e?.point) : [];
  const caveats = Array.isArray(brief?.missing_context) ? brief.missing_context.filter(Boolean) : [];
  const findings = brief ? [] : fallbackFindings;
  const isEmpty = !brief?.summary && evidence.length === 0 && caveats.length === 0 && findings.length === 0;
  const stance = brief?.stance ? String(brief.stance).replace(/_/g, " ") : "";
  const confidence = typeof brief?.confidence === "number" ? `${Math.round(brief.confidence * 100)}% confidence` : "";
  const itemStyle = { fontFamily: "Lora, serif", fontSize: 15, lineHeight: 1.5, color: TN.ink };
  const metaStyle = { fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: TN.muted, overflowWrap: "anywhere" };

  return (
    <div style={{ background: TN.surface, padding: "20px 22px" }}>
      <div className="flex items-center justify-between">
        <div style={{
          fontFamily: "Inter, sans-serif", fontSize: 10, letterSpacing: "0.2em",
          textTransform: "uppercase", color: tone,
          padding: "3px 8px", background: tint,
          border: `1px solid color-mix(in srgb, ${tone} 30%, transparent)`,
        }}>{role}</div>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: TN.muted }}>{who}</span>
      </div>
      <div className="mt-3" style={{ fontFamily: "Lora, serif", fontStyle: "italic", fontSize: 14.5, color: TN.ink2 }}>
        {posture}
      </div>
      {(stance || confidence) && (
        <div className="mt-3" style={{ ...metaStyle, letterSpacing: "0.06em", textTransform: "uppercase" }}>
          {[stance && `Stance: ${stance}`, confidence].filter(Boolean).join(" · ")}
        </div>
      )}
      {brief?.summary && (
        <p className="mt-3" style={itemStyle}>{brief.summary}</p>
      )}
      <ul className="mt-4 flex flex-col gap-2.5">
        {isEmpty && (
          <li style={{ fontFamily: "Lora, serif", fontStyle: "italic", color: TN.muted, fontSize: 14 }}>
            No findings of this kind were returned.
          </li>
        )}
        {evidence.map((e, i) => {
          const source = briefSource(e.source);
          return (
            <li key={`e${i}`} className="flex gap-2.5" style={itemStyle}>
              <span style={{ color: tone, fontWeight: 700, fontSize: 15 }}>{glyph}</span>
              <span>
                {e.point}
                {source.label && (
                  <span style={{ ...metaStyle, display: "block", marginTop: 2 }}>
                    {source.href
                      ? <a href={source.href} target="_blank" rel="noopener noreferrer" style={{ color: TN.muted }}>{source.label}</a>
                      : source.label}
                    {e.year ? ` · ${e.year}` : ""}
                  </span>
                )}
              </span>
            </li>
          );
        })}
        {caveats.map((c, i) => (
          <li key={`c${i}`} className="flex gap-2.5" style={itemStyle}>
            <span style={{ color: TN.muted, fontWeight: 700, fontSize: 15 }}>?</span>
            <span>{c}</span>
          </li>
        ))}
        {findings.map((f, i) => (
          <li key={i} className="flex gap-2.5" style={itemStyle}>
            <span style={{ color: tone, fontWeight: 700, fontSize: 15 }}>{glyph}</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

window.App = App;
