"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ClipboardList,
  Clock3,
  FileCheck2,
  FileText,
  FolderOpen,
  LayoutDashboard,
  LoaderCircle,
  LockKeyhole,
  LogOut,
  Menu,
  Plus,
  Search,
  Send,
  Server,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
  TriangleAlert,
  Wallet,
  Workflow,
} from "lucide-react";
import {
  api,
  post,
  nodeTrust,
  trustNode,
  uploadFile,
  submitCommand,
  decryptResult,
  downloadArtifact,
  type Json,
} from "../lib/client";

const SERVICES = [
  {
    id: "A_COMPLIANCE",
    letter: "A",
    title: "Bid compliance",
    bn: "দরপত্র যাচাই",
    description: "Requirements, evidence and a clear view of the gaps.",
    icon: FileCheck2,
  },
  {
    id: "B_CV_FIT",
    letter: "B",
    title: "CV & role fit",
    bn: "যোগ্যতা মূল্যায়ন",
    description: "Compare candidate evidence against the role criteria.",
    icon: ClipboardList,
  },
  {
    id: "C_MANAGED_CV",
    letter: "C",
    title: "Managed CV",
    bn: "বিশেষজ্ঞের সহায়তায় CV",
    description: "Request an evidence-grounded CV from the internal team.",
    icon: BookOpen,
  },
  {
    id: "D_PROPOSAL",
    letter: "D",
    title: "Managed proposal",
    bn: "প্রস্তাবনা প্রস্তুতি",
    description: "Technical and financial drafting with human review.",
    icon: Workflow,
  },
];
const array = (value: any): Json[] => (Array.isArray(value) ? value : []);
const label = (value: any) => String(value ?? "—").replaceAll("_", " ");
const date = (value: any) =>
  value
    ? `${new Date(value).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Dhaka" })} BDT`
    : "—";
const state = (job: Json) => job.state || job.status;
const activeJob = (job: Json) =>
  ["QUEUED", "LEASED", "RUNNING"].includes(state(job));
function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
function Empty({
  title,
  detail,
  icon: Icon = FolderOpen,
}: {
  title: string;
  detail: string;
  icon?: typeof FolderOpen;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Icon size={25} />
      </div>
      <h3>{title}</h3>
      <p>{detail}</p>
    </div>
  );
}
function Field({
  label: caption,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="field">
      <span>{caption}</span>
      {children}
    </label>
  );
}
function JsonDetails({
  value,
  title = "Details",
}: {
  value: any;
  title?: string;
}) {
  return (
    value && (
      <details className="json-details">
        <summary>{title}</summary>
        <pre>
          {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
        </pre>
      </details>
    )
  );
}

export default function Home() {
  const [boot, setBoot] = useState<Json | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState("overview");
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Json | null>(null);
  const [tab, setTab] = useState("overview");
  const [result, setResult] = useState<Json | null>(null);
  const [resultJob, setResultJob] = useState<Json | null>(null);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [search, setSearch] = useState("");
  const [mobile, setMobile] = useState(false);
  const [trust, setTrust] = useState<{
    fingerprint: string;
    trusted: boolean;
  } | null>(null);
  const [trustError, setTrustError] = useState("");
  const [operations, setOperations] = useState<Json | null>(null);
  const [consent, setConsent] = useState(false);
  const [candidateConsent, setCandidateConsent] = useState(false);
  const [category, setCategory] = useState("TENDER");
  const [authMode, setAuthMode] = useState("login");
  const [review, setReview] = useState<Json>({
    finding_status: "UNCLEAR",
    assurance: "SOURCE_LOCATED",
    evidence_page: 1,
  });
  const [coverageReviewed, setCoverageReviewed] = useState(false);
  const [cvAssignments, setCvAssignments] = useState([{ start: "", end: "" }]);
  const [draftInstructions, setDraftInstructions] = useState("");
  const [researchQuestion, setResearchQuestion] = useState("");
  const [researchNotes, setResearchNotes] = useState("");
  const [lines, setLines] = useState([
    { label: "Professional services", quantity: "1", rate: "0" },
  ]);
  const [currency, setCurrency] = useState("BDT");
  const [tax, setTax] = useState("0");
  const [message, setMessage] = useState("");
  const [deleteReason, setDeleteReason] = useState("");
  const [orderNote, setOrderNote] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const decrypted = useRef(new Set<string>());
  const selectedRef = useRef<string | null>(null);
  const user = boot?.user;
  const node = boot?.node || {};
  const project = detail?.project;
  const projects = array(boot?.projects);
  const jobs = array(detail?.jobs);
  const internal = ["OWNER", "STAFF"].includes(user?.role);
  const isCandidate = ["B_CV_FIT", "C_MANAGED_CV"].includes(
    project?.service_id,
  );
  const service = SERVICES.find((s) => s.id === project?.service_id);
  const canProcess = Boolean(
    consent &&
    (!isCandidate || candidateConsent) &&
    trust?.trusted &&
    node.public_key,
  );
  const refresh = useCallback(async () => {
    const data = await api("/bootstrap");
    setBoot(data);
    return data;
  }, []);
  const refreshCase = useCallback(async (id: string) => {
    const data = await api(`/projects/${id}`);
    if (selectedRef.current === id) setDetail(data);
    return data;
  }, []);
  useEffect(() => {
    refresh()
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [refresh]);
  useEffect(() => {
    if (!showNew) return;
    const previous = document.activeElement as HTMLElement | null;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setShowNew(false);
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = Array.from(
        document.querySelectorAll<HTMLElement>(
          '[role="dialog"] button:not(:disabled),[role="dialog"] input:not(:disabled),[role="dialog"] select:not(:disabled),[role="dialog"] textarea:not(:disabled)',
        ),
      );
      const first = focusable[0],
        last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previous?.focus();
    };
  }, [showNew]);
  useEffect(() => {
    if (!node.public_key) {
      setTrust(null);
      return;
    }
    nodeTrust(node)
      .then((v) => {
        setTrust(v);
        setTrustError("");
      })
      .catch((e) => {
        setTrust(null);
        setTrustError(e.message);
      });
  }, [node.public_key, node.fingerprint]);
  useEffect(() => {
    if (!user) return;
    const timer = setInterval(() => {
      void refresh().catch(() => {});
      if (selectedRef.current)
        void refreshCase(selectedRef.current).catch(() => {});
    }, 4000);
    return () => clearInterval(timer);
  }, [user?.id, refresh, refreshCase]);
  useEffect(() => {
    if (!user || !selected || detail?.project?.id !== selected) return;
    const completed = jobs
      .filter((j) =>
        ["COMPLETED", "NEEDS_INPUT", "INCONCLUSIVE", "SYSTEM_ERROR"].includes(
          state(j),
        ),
      )
      .sort((a, b) =>
        String(b.created_at || "").localeCompare(String(a.created_at || "")),
      );
    const latest = completed[0];
    if (!latest || decrypted.current.has(latest.id)) return;
    decrypted.current.add(latest.id);
    void api(`/jobs/${latest.id}`)
      .then(async (full) => {
        if (!full.result_envelope) return;
        const data = await decryptResult(
          full,
          user,
          selected,
          detail?.project?.tenant_id,
        );
        if (selectedRef.current === selected) {
          setResult(data);
          setResultJob(full);
        }
      })
      .catch((e) => {
        if (selectedRef.current === selected)
          setError(
            `Encrypted result: ${e.message} Use the same account and browser profile that uploaded the case sources. Private delegation between staff or profiles is not available in this pilot.`,
          );
      });
  }, [detail, user?.id, selected]);
  async function run(key: string, work: () => Promise<any>, success?: string) {
    setBusy(key);
    setError("");
    setNotice("");
    try {
      await work();
      if (success) setNotice(success);
    } catch (e: any) {
      setError(e.message || "The action could not be completed.");
    } finally {
      setBusy("");
    }
  }
  function openCase(id: string) {
    selectedRef.current = id;
    setSelected(id);
    setDetail(null);
    setResult(null);
    setResultJob(null);
    decrypted.current.clear();
    setConsent(false);
    setCandidateConsent(false);
    setReview({
      finding_status: "UNCLEAR",
      assurance: "SOURCE_LOCATED",
      evidence_page: 1,
    });
    setCoverageReviewed(false);
    setCvAssignments([{ start: "", end: "" }]);
    setDraftInstructions("");
    setResearchQuestion("");
    setResearchNotes("");
    setLines([{ label: "Professional services", quantity: "1", rate: "0" }]);
    setCurrency("BDT");
    setTax("0");
    setOrderNote("");
    setNotice("");
    setView("case");
    setTab("overview");
    setMobile(false);
    setError("");
    void run("open", () => refreshCase(id));
  }
  function navigate(next: string) {
    setView(next);
    setMobile(false);
    if (next === "operations")
      void run("operations", async () =>
        setOperations(await api("/operations")),
      );
  }
  async function command(action: string, body: Json = {}) {
    if (!canProcess)
      throw new Error(
        "Confirm processing permission and the local key before continuing.",
      );
    const intervals = cvAssignments.filter((item) => item.start || item.end);
    if (
      ["ANALYZE", "REVIEW"].includes(action) &&
      isCandidate &&
      internal &&
      intervals.length
    ) {
      if (
        intervals.some(
          (item) =>
            !/^\d{4}-\d{2}$/.test(item.start) ||
            !/^\d{4}-\d{2}$/.test(item.end) ||
            item.start > item.end,
        )
      )
        throw new Error(
          "Complete every entered CV interval with a valid start and end month; end must be at or after start.",
        );
      body = { ...body, cv_assignments: intervals };
    }
    await submitCommand(project, user, node, action, {
      ...body,
      processing_consent: consent,
      candidate_consent: candidateConsent,
    });
    await refreshCase(project.id);
    await refresh();
    setTab("overview");
  }
  async function loadExamples() {
    if (
      !canProcess ||
      !["A_COMPLIANCE", "B_CV_FIT"].includes(project.service_id) ||
      array(detail?.assets).length
    )
      throw new Error(
        "Use an empty A/B case, confirm local processing consent and trust the local key first.",
      );
    const examples = [
      { name: "demo-tender.txt", category: "TENDER" },
      {
        name:
          project.service_id === "B_CV_FIT" ? "demo-cv.txt" : "demo-bidder.txt",
        category: project.service_id === "B_CV_FIT" ? "CV" : "BIDDER",
      },
    ];
    try {
      for (const example of examples) {
        const response = await fetch(`/examples/${example.name}`, {
          credentials: "same-origin",
        });
        if (!response.ok)
          throw new Error(
            "The fictional example file is unavailable. No analysis has been started.",
          );
        const content = await response.text();
        await uploadFile(
          project,
          user,
          node,
          new File([content], example.name, { type: "text/plain" }),
          example.category,
        );
      }
    } finally {
      await refreshCase(project.id);
      await refresh();
    }
  }
  function submitForm(
    event: React.FormEvent<HTMLFormElement>,
    work: (data: FormData) => Promise<any>,
    key: string,
    success?: string,
  ) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    void run(key, () => work(form), success);
  }
  const noticeArea = (
    <>
      {error && (
        <div className="alert error" role="alert">
          <TriangleAlert size={18} />
          <span>{error}</span>
          <button
            className="icon-button"
            aria-label="Dismiss error"
            onClick={() => setError("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
      {notice && (
        <div className="alert success" role="status">
          <CheckCircle2 size={18} />
          <span>{notice}</span>
          <button
            className="icon-button"
            aria-label="Dismiss message"
            onClick={() => setNotice("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
    </>
  );

  if (loading)
    return (
      <main className="loading-screen">
        <div className="brand-logo">
          <ShieldCheck size={28} />
        </div>
        <h1>TenderOS</h1>
        <LoaderCircle className="spin" />
        <p>Opening your local workspace…</p>
      </main>
    );
  if (!user)
    return (
      <main className="auth-page">
        <section className="auth-story">
          <div className="brand">
            <div className="brand-logo">
              <ShieldCheck size={24} />
            </div>
            <span>
              Tender<span className="brand-os">OS</span>
            </span>
          </div>
          <Badge tone="teal">OWNER-CONTROLLED · LOCAL PILOT</Badge>
          <h1>
            Every decision
            <br />
            starts with
            <br />
            <em>the evidence.</em>
          </h1>
          <p>
            দরপত্রের শর্ত, আপনার প্রমাণ, এবং পরবর্তী পদক্ষেপ—একটি নির্ভরযোগ্য
            workspace-এ।
          </p>
          <div className="auth-principles">
            <span>
              <LockKeyhole size={18} /> Private engine stays on this computer
            </span>
            <span>
              <FileCheck2 size={18} /> Source-linked findings and clear gaps
            </span>
            <span>
              <ShieldCheck size={18} /> Human review before formal release
            </span>
          </div>
          <small>PILOT_PC · No live payments · No external AI fallback</small>
        </section>
        <section className="auth-form-wrap">
          <div className="auth-form">
            <p className="eyebrow">YOUR TENDER WORKSPACE</p>
            <h2>
              {authMode === "login" ? "Welcome back" : "Create your account"}
            </h2>
            <p className="muted">
              {authMode === "login"
                ? "Sign in to continue your evidence-led work."
                : "A private customer account for the local pilot."}
            </p>
            {noticeArea}
            <form
              onSubmit={(e) =>
                submitForm(
                  e,
                  async (form) => {
                    await post(`/auth/${authMode}`, Object.fromEntries(form));
                    setView("overview");
                    setOperations(null);
                    selectedRef.current = null;
                    setSelected(null);
                    setDetail(null);
                    setResult(null);
                    setResultJob(null);
                    await refresh();
                  },
                  "auth",
                )
              }
            >
              {authMode === "register" && (
                <Field label="Full name / নাম">
                  <input
                    name="name"
                    autoComplete="name"
                    required
                    maxLength={120}
                  />
                </Field>
              )}
              <Field label="Email address">
                <input
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                />
              </Field>
              <Field label="Password">
                <input
                  name="password"
                  type="password"
                  autoComplete={
                    authMode === "login" ? "current-password" : "new-password"
                  }
                  required
                  minLength={12}
                />
              </Field>
              <button className="button primary wide" disabled={Boolean(busy)}>
                {busy === "auth" ? (
                  <LoaderCircle className="spin" size={17} />
                ) : (
                  <ArrowRight size={17} />
                )}{" "}
                {authMode === "login"
                  ? "Sign in / প্রবেশ করুন"
                  : "Create customer account"}
              </button>
            </form>
            <button
              className="text-button"
              onClick={() =>
                setAuthMode(authMode === "login" ? "register" : "login")
              }
            >
              {authMode === "login"
                ? "New here? Create an account"
                : "Already have an account? Sign in"}
            </button>
            <div className="small-note">
              <LockKeyhole size={15} />
              <span>
                Owner access is created by the local setup tool. Customer
                registration never grants staff privileges.
              </span>
            </div>
          </div>
        </section>
      </main>
    );

  return (
    <div className="app-shell">
      <button
        className="mobile-toggle icon-button"
        aria-label="Open navigation"
        onClick={() => setMobile(!mobile)}
      >
        <Menu />
      </button>
      {mobile && (
        <button
          className="sidebar-backdrop"
          onClick={() => setMobile(false)}
          aria-label="Close navigation"
        />
      )}
      <aside className={`sidebar ${mobile ? "is-open" : ""}`}>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate("overview");
          }}
        >
          <div className="brand-logo">
            <ShieldCheck size={25} />
          </div>
          <span>
            Tender<span className="brand-os">OS</span>
          </span>
        </a>
        <div className="workspace-selector">
          <div className="workspace-avatar">
            {String(user.name || "T").slice(0, 1)}
          </div>
          <div>
            <strong>Local workspace</strong>
            <span>Owner-controlled pilot</span>
          </div>
          <ChevronDown size={15} />
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {[
            {
              id: "overview",
              text: "Overview",
              bn: "এক নজরে",
              icon: LayoutDashboard,
            },
            {
              id: "projects",
              text: "Tender cases",
              bn: "কেসসমূহ",
              icon: FolderOpen,
            },
            {
              id: "operations",
              text: "Operations & gates",
              bn: "পরিচালনা",
              icon: Activity,
            },
            {
              id: "privacy",
              text: "Privacy & support",
              bn: "গোপনীয়তা",
              icon: LockKeyhole,
            },
          ].map((item) => (
            <button
              key={item.id}
              className={`nav-link ${view === item.id || (item.id === "projects" && view === "case") ? "active" : ""}`}
              onClick={() => navigate(item.id)}
            >
              <item.icon size={19} />
              <span>
                {item.text}
                <small>{item.bn}</small>
              </span>
              {item.id === "projects" && <b>{projects.length}</b>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="custody-note">
            <ShieldCheck size={19} />
            <strong>Your engine. Your custody.</strong>
            <p>
              Private processing runs on the owner’s computer. This portal holds
              encrypted documents.
            </p>
            <span className={`live-dot ${node.public_key ? "green" : ""}`} />
            <small>
              {node.public_key
                ? "Private node registered"
                : "Waiting for private node"}
            </small>
          </div>
          <button
            className="user-chip"
            onClick={() =>
              void run("logout", async () => {
                await post("/auth/logout");
                setBoot(null);
                setDetail(null);
                setResult(null);
                setResultJob(null);
                setOperations(null);
                setView("overview");
                decrypted.current.clear();
                setConsent(false);
                setCandidateConsent(false);
                setMessage("");
                setDeleteReason("");
                setDraftInstructions("");
                setResearchNotes("");
                selectedRef.current = null;
                setSelected(null);
                await refresh();
              })
            }
          >
            <div className="user-avatar">
              {String(user.name || "U").slice(0, 1)}
            </div>
            <span>
              <strong>{user.name}</strong>
              <small>{label(user.role)}</small>
            </span>
            <LogOut size={16} />
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={14} />
            <strong>
              {view === "case"
                ? project?.title || "Tender case"
                : view === "projects"
                  ? "Tender cases"
                  : view === "operations"
                    ? "Operations & gates"
                    : view === "privacy"
                      ? "Privacy & support"
                      : "Overview"}
            </strong>
          </div>
          <div className="topbar-right">
            <Badge tone="amber">
              <span className="live-dot" /> LOCAL DEVELOPMENT
            </Badge>
            <span className="top-date">
              {new Date().toLocaleDateString("en-GB", {
                day: "numeric",
                month: "short",
                year: "numeric",
                timeZone: "Asia/Dhaka",
              })}
            </span>
            <div className="user-avatar light">
              {String(user.name || "U").slice(0, 1)}
            </div>
          </div>
        </header>
        <main className="main-content">
          {noticeArea}
          {view === "overview" && (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">CLARITY BEFORE COMMITMENT</p>
                  <h1>
                    Your tender command center
                    <span className="heading-dot">.</span>
                  </h1>
                  <p>
                    সব শর্ত ও প্রমাণ একসাথে। Make the next decision with
                    confidence in its source.
                  </p>
                </div>
                <button
                  className="button primary"
                  onClick={() => setShowNew(true)}
                >
                  <Plus size={18} />
                  New tender case
                </button>
              </div>
              <div className="pilot-banner">
                <div className="banner-icon">
                  <ShieldCheck size={24} />
                </div>
                <div>
                  <strong>Built around one operational record.</strong>
                  <p>
                    Each case connects its documents, requirements, evidence,
                    decisions and reports. This local pilot produces preliminary
                    diagnostics.
                  </p>
                </div>
                <Badge tone="teal">PILOT_PC</Badge>
              </div>
              <section className="stats-grid" aria-label="Workspace metrics">
                {[
                  {
                    title: "Tender cases",
                    value: projects.length,
                    icon: FolderOpen,
                    note: "Your owned & assigned cases",
                  },
                  {
                    title: "Active jobs",
                    value: array(boot?.jobs).filter(activeJob).length,
                    icon: Activity,
                    note: "Durable, recoverable processing",
                  },
                  {
                    title: "Private processing",
                    value: node.public_key ? "Registered" : "Offline",
                    icon: Server,
                    note: "Local node · no hosted AI",
                  },
                  {
                    title: "Release status",
                    value: "Preliminary",
                    icon: ShieldCheck,
                    note: "Production gates remain pending",
                  },
                ].map((item) => (
                  <div className="stat-card" key={item.title}>
                    <div className="stat-top">
                      <span>{item.title}</span>
                      <item.icon size={19} />
                    </div>
                    <strong>{item.value}</strong>
                    <p>{item.note}</p>
                  </div>
                ))}
              </section>
              <div className="section-title">
                <div>
                  <h2>How can TenderOS help?</h2>
                  <p>Choose a service. Your evidence stays at the center.</p>
                </div>
                <Badge>4 service profiles</Badge>
              </div>
              <div className="services-grid">
                {SERVICES.map((s) => (
                  <button
                    className="service-card"
                    key={s.id}
                    onClick={() => {
                      setShowNew(true);
                      setTimeout(() => {
                        const select = document.getElementById(
                          "new-service",
                        ) as HTMLSelectElement | null;
                        if (select) select.value = s.id;
                      }, 0);
                    }}
                  >
                    <div className="service-top">
                      <div className="service-icon">
                        <s.icon size={23} />
                      </div>
                      <Badge>{s.letter}</Badge>
                    </div>
                    <h3>{s.title}</h3>
                    <span className="bangla">{s.bn}</span>
                    <p>{s.description}</p>
                    <span className="service-link">
                      {["A", "B"].includes(s.letter)
                        ? "Start a diagnostic"
                        : "Request managed service"}
                      <ArrowRight size={15} />
                    </span>
                  </button>
                ))}
              </div>
              <div className="dashboard-bottom">
                <section className="panel">
                  <div className="panel-heading">
                    <h2>Recent cases</h2>
                    <button
                      className="text-button"
                      onClick={() => navigate("projects")}
                    >
                      View all
                      <ArrowRight size={14} />
                    </button>
                  </div>
                  {projects.length ? (
                    <CaseTable
                      projects={projects.slice(0, 5)}
                      open={openCase}
                    />
                  ) : (
                    <Empty
                      title="Your first case starts here"
                      detail="Create a case, add the tender and supporting documents, then review the evidence."
                    />
                  )}
                </section>
                <section className="panel decision-card">
                  <p className="eyebrow">THE DECISION PRINCIPLE</p>
                  <div className="principle-icon">
                    <FileCheck2 size={30} />
                  </div>
                  <h2>
                    A strong score is only
                    <br />
                    part of the picture.
                  </h2>
                  <p>
                    বাধ্যতামূলক শর্তের প্রমাণ অসম্পূর্ণ হলে clearance হবে{" "}
                    <strong>UNKNOWN</strong>। Commercial opportunity and
                    mandatory eligibility are separate decisions.
                  </p>
                  <div className="principle-footer">
                    <LockKeyhole size={15} />
                    No evidence → no accepted claim
                  </div>
                </section>
              </div>
            </>
          )}

          {view === "projects" && (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">ONE CASE, A COMPLETE RECORD</p>
                  <h1>Tender cases</h1>
                  <p>
                    কাজের ধারাবাহিকতা বজায় রাখুন—source থেকে decision পর্যন্ত।
                  </p>
                </div>
                <button
                  className="button primary"
                  onClick={() => setShowNew(true)}
                >
                  <Plus size={18} />
                  New case
                </button>
              </div>
              <section className="panel">
                <div className="panel-heading">
                  <h2>
                    All cases <span className="count">{projects.length}</span>
                  </h2>
                  <label className="search-field">
                    <Search size={17} />
                    <input
                      aria-label="Search cases"
                      placeholder="Search title, bidder or issuer"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                  </label>
                </div>
                {projects.length ? (
                  <CaseTable
                    projects={projects.filter((p) =>
                      `${p.title} ${p.bidder} ${p.issuer}`
                        .toLowerCase()
                        .includes(search.toLowerCase()),
                    )}
                    open={openCase}
                  />
                ) : (
                  <Empty
                    title="No cases yet"
                    detail="Start with a tender opportunity or request a managed CV or proposal."
                  />
                )}
              </section>
            </>
          )}

          {view === "case" &&
            (!project ? (
              <Empty
                title="Opening case…"
                detail="Loading its encrypted asset metadata and job history."
              />
            ) : (
              <>
                <div className="page-heading case-heading">
                  <div>
                    <button
                      className="text-button"
                      onClick={() => navigate("projects")}
                    >
                      Tender cases / কেসসমূহ
                    </button>
                    <h1>{project.title}</h1>
                    <p>
                      {project.bidder} <span className="separator">·</span>{" "}
                      {project.issuer || "Issuer not specified"}{" "}
                      <span className="separator">·</span>{" "}
                      {service?.title || label(project.service_id)}
                    </p>
                  </div>
                  <Badge tone="teal">
                    {label(project.state || project.status || "DRAFT")}
                  </Badge>
                </div>
                <div className="case-meta">
                  <span>
                    <Clock3 size={16} />
                    Deadline: {date(project.deadline)}
                  </span>
                  <span>
                    <FileText size={16} />
                    {array(detail?.assets).length} encrypted assets
                  </span>
                  <span>
                    <ShieldCheck size={16} />
                    Version {project.version}
                  </span>
                  <span>
                    <LockKeyhole size={16} />
                    Private node processing
                  </span>
                </div>
                <div
                  className="case-tabs"
                  role="tablist"
                  aria-label="Case workspace"
                >
                  {[
                    ["overview", "Case overview"],
                    ["documents", "Documents"],
                    ["matrix", "Requirements & gaps"],
                    ["workbench", "Workbenches"],
                    ["reports", "Reports"],
                    ["activity", "Activity"],
                  ].map(([id, title]) => (
                    <button
                      role="tab"
                      aria-selected={tab === id}
                      key={id}
                      className={tab === id ? "selected" : ""}
                      onClick={() => setTab(id)}
                    >
                      {title}
                    </button>
                  ))}
                </div>
                {resultJob && resultJob.project_version !== project.version && (
                  <div className="alert error">
                    <TriangleAlert size={18} />
                    <span>
                      This is a historical result from source version{" "}
                      {resultJob.project_version}. The case is now version{" "}
                      {project.version}. Run a new analysis before relying on
                      the findings.
                    </span>
                  </div>
                )}
                {tab === "overview" && (
                  <div className="case-grid">
                    <section className="panel padded">
                      <p className="eyebrow">YOUR NEXT STEP</p>
                      <h2>
                        {array(detail?.assets).length
                          ? "Review your sources. Start a diagnostic."
                          : "Build the evidence record."}
                      </h2>
                      <p className="muted">
                        Upload the tender and relevant evidence. Processing
                        happens only on the private owner node. Results return
                        encrypted to this browser.
                      </p>
                      <div className="workflow-steps">
                        {[
                          [
                            "1",
                            "Add source documents",
                            "Tender, amendments and bidder evidence.",
                          ],
                          [
                            "2",
                            "Analyse on the private node",
                            "Local extraction and deterministic checks.",
                          ],
                          [
                            "3",
                            "Resolve gaps & review",
                            "Source-linked findings; no automatic clearance.",
                          ],
                        ].map(([number, title, text]) => (
                          <div className="workflow-step" key={number}>
                            <b>{number}</b>
                            <div>
                              <strong>{title}</strong>
                              <p>{text}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                      <button
                        className="button secondary"
                        onClick={() => setTab("documents")}
                      >
                        <Upload size={17} />
                        Manage documents
                      </button>
                      <hr />
                      <div className="consents">
                        <label>
                          <input
                            type="checkbox"
                            checked={consent}
                            onChange={(e) => setConsent(e.target.checked)}
                          />
                          <span>
                            I authorize local processing of the selected case
                            documents for this service.{" "}
                            <small>
                              আমি এই কাজে local processing-এর অনুমতি দিচ্ছি।
                            </small>
                          </span>
                        </label>
                        {isCandidate && (
                          <label>
                            <input
                              type="checkbox"
                              checked={candidateConsent}
                              onChange={(e) =>
                                setCandidateConsent(e.target.checked)
                              }
                            />
                            <span>
                              I have the candidate’s authorization to process
                              their CV and personal data for this purpose.
                            </span>
                          </label>
                        )}
                      </div>
                      {["A_COMPLIANCE", "B_CV_FIT"].includes(
                        project.service_id,
                      ) ? (
                        <button
                          className="button primary"
                          disabled={
                            !canProcess ||
                            Boolean(busy) ||
                            jobs.some(activeJob) ||
                            !array(detail?.assets).some(
                              (a) => a.state === "ENCRYPTED",
                            )
                          }
                          onClick={() =>
                            void run(
                              "analyse",
                              () => command("ANALYZE"),
                              "Analysis queued on the private node.",
                            )
                          }
                        >
                          <Sparkles size={17} />
                          {busy === "analyse"
                            ? "Queuing…"
                            : "Run preliminary analysis"}
                        </button>
                      ) : (
                        <>
                          <Field label="Managed service request / কাজের বিবরণ">
                            <textarea
                              value={orderNote}
                              onChange={(e) => setOrderNote(e.target.value)}
                              placeholder="Describe the deliverable and requested scope. Do not put private source text here."
                              maxLength={500}
                            />
                          </Field>
                          <button
                            className="button primary"
                            disabled={!orderNote.trim() || Boolean(busy)}
                            onClick={() =>
                              void run(
                                "order",
                                async () => {
                                  await post(`/projects/${project.id}/orders`, {
                                    note: orderNote,
                                  });
                                  setOrderNote("");
                                  await refreshCase(project.id);
                                },
                                "Managed work order recorded. This does not start staff authoring.",
                              )
                            }
                          >
                            <Send size={17} />
                            Request managed service
                          </button>
                        </>
                      )}
                      <p className="caption">
                        Free local pilot. Checkout and paid entitlements are
                        disabled.
                      </p>
                      {array(detail?.orders).length > 0 && (
                        <div className="work-orders">
                          <hr />
                          <h3>Managed work orders</h3>
                          {array(detail?.orders).map((order) => (
                            <div className="job-row" key={order.id}>
                              <div>
                                <strong>{label(order.state)}</strong>
                                <p className="caption">{order.note}</p>
                                <small>{date(order.created_at)}</small>
                              </div>
                              {internal && order.state === "REQUESTED" && (
                                <button
                                  className="button secondary"
                                  disabled={Boolean(busy)}
                                  onClick={() =>
                                    void run(
                                      "accept-order",
                                      async () => {
                                        await post(
                                          `/projects/${project.id}/orders/${order.id}/accept`,
                                        );
                                        await refreshCase(project.id);
                                      },
                                      "Managed work order accepted.",
                                    )
                                  }
                                >
                                  Accept work order
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </section>
                    <div className="stack">
                      <TrustPanel
                        node={node}
                        trust={trust}
                        error={trustError}
                        busy={Boolean(busy)}
                        onTrust={() =>
                          void run(
                            "trust",
                            async () => {
                              await trustNode(node);
                              setTrust(await nodeTrust(node));
                            },
                            "Local node key pinned to this browser. Production trust approval is still pending.",
                          )
                        }
                      />
                      <section className="panel padded">
                        <h2>Latest decision</h2>
                        {result ? (
                          <>
                            <div className="result-badges">
                              <Badge tone="amber">
                                {label(result.readiness)}
                              </Badge>
                              <Badge
                                tone={
                                  result.mandatory_clearance === "PASS"
                                    ? "teal"
                                    : "amber"
                                }
                              >
                                {label(result.mandatory_clearance)}
                              </Badge>
                            </div>
                            <h3>{label(result.business_recommendation)}</h3>
                            <p>
                              {typeof result.summary === "string"
                                ? result.summary
                                : "Open requirements and gaps for the source-linked diagnostic."}
                            </p>
                            <button
                              className="text-button"
                              onClick={() => setTab("matrix")}
                            >
                              Review findings
                              <ArrowRight size={15} />
                            </button>
                            <p className="caption">
                              Snapshot{" "}
                              {String(result.snapshot_digest).slice(0, 14)}…
                            </p>
                          </>
                        ) : (
                          <p className="muted">
                            No decrypted result yet. Completed results are
                            verified and decrypted in this browser.
                          </p>
                        )}
                      </section>
                    </div>
                    <section className="panel full">
                      <div className="panel-heading">
                        <h2>Processing queue</h2>
                        <Badge>{jobs.length} jobs</Badge>
                      </div>
                      {jobs.length ? (
                        <div className="job-list">
                          {jobs.map((j) => (
                            <div className="job-row" key={j.id}>
                              <div className="job-icon">
                                {activeJob(j) ? (
                                  <LoaderCircle size={19} className="spin" />
                                ) : (
                                  <FileCheck2 size={19} />
                                )}
                              </div>
                              <div>
                                <strong>{label(j.action)}</strong>
                                <small>
                                  {date(j.created_at)} ·{" "}
                                  {String(j.id).slice(0, 10)}
                                </small>
                              </div>
                              <Badge tone={activeJob(j) ? "teal" : "neutral"}>
                                {label(state(j))}
                              </Badge>
                              {activeJob(j) && (
                                <button
                                  className="text-button"
                                  disabled={Boolean(busy)}
                                  onClick={() =>
                                    void run(
                                      "cancel",
                                      async () => {
                                        await post(`/jobs/${j.id}/cancel`);
                                        await refreshCase(project.id);
                                      },
                                      "Cancellation request recorded.",
                                    )
                                  }
                                >
                                  Cancel
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <Empty
                          title="No processing jobs"
                          detail="Your first analysis will appear here with recoverable status."
                          icon={Activity}
                        />
                      )}
                    </section>
                  </div>
                )}

                {tab === "documents" && (
                  <div className="case-grid">
                    <section className="panel padded">
                      <h2>Encrypted document upload</h2>
                      <p className="muted">
                        ফাইলটি browser-এ encrypt হবে। Public broker শুধু
                        ciphertext পাবে; file name and content remain inside the
                        envelope.
                      </p>
                      <Field label="Document role">
                        <select
                          value={category}
                          onChange={(e) => setCategory(e.target.value)}
                        >
                          {[
                            "TENDER",
                            "AMENDMENT",
                            "BIDDER",
                            "CV",
                            "RESEARCH",
                            "DERIVED",
                          ].map((c) => (
                            <option key={c}>{c}</option>
                          ))}
                        </select>
                      </Field>
                      <label
                        className={`upload-zone ${!trust?.trusted ? "disabled" : ""}`}
                      >
                        <div className="upload-icon">
                          <Upload size={27} />
                        </div>
                        <strong>
                          {busy === "upload"
                            ? "Encrypting and uploading…"
                            : "Choose a document"}
                        </strong>
                        <span>PDF, DOCX, TXT · maximum 12 MiB per file</span>
                        <input
                          ref={fileInput}
                          type="file"
                          accept=".pdf,.docx,.txt"
                          disabled={Boolean(busy) || !trust?.trusted}
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file)
                              void run(
                                "upload",
                                async () => {
                                  await uploadFile(
                                    project,
                                    user,
                                    node,
                                    file,
                                    category,
                                  );
                                  await refreshCase(project.id);
                                  await refresh();
                                  if (fileInput.current)
                                    fileInput.current.value = "";
                                },
                                "Encrypted document stored. The private node will validate it during analysis.",
                              );
                          }}
                        />
                      </label>
                      <div className="small-note">
                        <LockKeyhole size={17} />
                        <span>
                          Upload acceptance is not document verification. Parser
                          safety, source anchors and evidence checks happen on
                          the local node.
                        </span>
                      </div>
                      {["A_COMPLIANCE", "B_CV_FIT"].includes(
                        project.service_id,
                      ) && (
                        <div className="synthetic-example">
                          <hr />
                          <p className="eyebrow">FICTIONAL WALKTHROUGH</p>
                          <h3>Try a synthetic example / কাল্পনিক উদাহরণ</h3>
                          <p className="muted">
                            Adds two clearly fictional text documents as new
                            encrypted input versions. It never starts analysis
                            or replaces existing source assets.
                          </p>
                          <div className="consents">
                            <label>
                              <input
                                type="checkbox"
                                checked={consent}
                                onChange={(e) => setConsent(e.target.checked)}
                              />
                              <span>
                                I authorize local processing for this fictional
                                pilot case.
                              </span>
                            </label>
                            {isCandidate && (
                              <label>
                                <input
                                  type="checkbox"
                                  checked={candidateConsent}
                                  onChange={(e) =>
                                    setCandidateConsent(e.target.checked)
                                  }
                                />
                                <span>
                                  I confirm this is the fictional candidate
                                  walkthrough, with no real personal data.
                                </span>
                              </label>
                            )}
                          </div>
                          <button
                            className="button secondary"
                            disabled={
                              !canProcess ||
                              Boolean(busy) ||
                              array(detail?.assets).length > 0
                            }
                            onClick={() =>
                              void run(
                                "examples",
                                loadExamples,
                                "Fictional examples uploaded as new encrypted inputs. Review them, then start analysis when ready.",
                              )
                            }
                          >
                            <Sparkles size={16} />
                            {busy === "examples"
                              ? "Encrypting examples…"
                              : "Load synthetic example"}
                          </button>
                          {array(detail?.assets).length > 0 && (
                            <p className="caption">
                              Available only in an empty case. Create a new A/B
                              case for another walkthrough.
                            </p>
                          )}
                        </div>
                      )}
                    </section>
                    <TrustPanel
                      node={node}
                      trust={trust}
                      error={trustError}
                      busy={Boolean(busy)}
                      onTrust={() =>
                        void run("trust", async () => {
                          await trustNode(node);
                          setTrust(await nodeTrust(node));
                        })
                      }
                    />
                    <section className="panel full">
                      <div className="panel-heading">
                        <h2>Case source assets</h2>
                        <Badge>{array(detail?.assets).length} records</Badge>
                      </div>
                      {array(detail?.assets).length ? (
                        <div className="table-wrap">
                          <table>
                            <thead>
                              <tr>
                                <th>Opaque asset</th>
                                <th>Role</th>
                                <th>Broker state</th>
                                <th>Added</th>
                              </tr>
                            </thead>
                            <tbody>
                              {array(detail?.assets).map((a) => (
                                <tr key={a.id}>
                                  <td>
                                    <FileText size={16} />{" "}
                                    {String(a.id).slice(0, 16)}…
                                  </td>
                                  <td>{label(a.category)}</td>
                                  <td>
                                    <Badge>
                                      {label(a.state || a.status || "STORED")}
                                    </Badge>
                                  </td>
                                  <td>{date(a.created_at)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <Empty
                          title="No documents uploaded"
                          detail="Begin with the tender, then add evidence and applicable official amendments."
                        />
                      )}
                    </section>
                  </div>
                )}

                {tab === "matrix" && (
                  <>
                    <div className="section-title">
                      <div>
                        <h2>Requirements & evidence</h2>
                        <p>
                          প্রতিটি finding-এর পাশে source, proof এবং পরবর্তী কাজ
                          দেখুন।
                        </p>
                      </div>
                      {result && (
                        <Badge tone="amber">{label(result.readiness)}</Badge>
                      )}
                    </div>
                    {result ? (
                      <>
                        <div className="stats-grid compact">
                          <div className="stat-card">
                            <span>Requirements</span>
                            <strong>{array(result.requirements).length}</strong>
                          </div>
                          <div className="stat-card">
                            <span>Open gaps</span>
                            <strong>{array(result.gaps).length}</strong>
                          </div>
                          <div className="stat-card">
                            <span>Mandatory clearance</span>
                            <strong className="word-stat">
                              {label(result.mandatory_clearance)}
                            </strong>
                          </div>
                          <div className="stat-card">
                            <span>Recommendation</span>
                            <strong className="word-stat">
                              {label(result.business_recommendation)}
                            </strong>
                          </div>
                        </div>
                        <section className="panel">
                          <div className="table-wrap">
                            <table className="matrix-table">
                              <thead>
                                <tr>
                                  <th>Requirement & source</th>
                                  <th>Finding</th>
                                  <th>Evidence & assurance</th>
                                  <th>Gap / next action</th>
                                </tr>
                              </thead>
                              <tbody>
                                {array(result.requirements).map((r) => (
                                  <tr key={r.id}>
                                    <td>
                                      {r.mandatory && (
                                        <Badge tone="amber">Mandatory</Badge>
                                      )}
                                      <p className="quote">{r.quote}</p>
                                      <SourceReference
                                        sources={array(result.sources)}
                                        id={r.source_id}
                                        page={r.page}
                                        clause={r.clause_ref}
                                      />
                                      <JsonDetails
                                        value={{
                                          requirement_id: r.id,
                                          source_id: r.source_id,
                                        }}
                                        title="Technical reference"
                                      />
                                    </td>
                                    <td>
                                      <Badge
                                        tone={
                                          r.finding_status === "MATCHED"
                                            ? "teal"
                                            : "amber"
                                        }
                                      >
                                        {label(r.finding_status)}
                                      </Badge>
                                      <p>{r.rationale}</p>
                                    </td>
                                    <td>
                                      <Badge>{label(r.assurance)}</Badge>
                                      {array(r.evidence).map((e, i) => (
                                        <div className="evidence-item" key={i}>
                                          <SourceReference
                                            sources={array(result.sources)}
                                            id={
                                              e.source_id ||
                                              e.evidence_source_id
                                            }
                                            page={e.page || e.evidence_page}
                                            clause={e.clause_ref}
                                          />
                                          <p>{e.quote || e.evidence_quote}</p>
                                        </div>
                                      ))}
                                    </td>
                                    <td>
                                      <p>
                                        {r.next_action ||
                                          "Review the source-linked finding."}
                                      </p>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {!array(result.requirements).length && (
                              <Empty
                                title="No normalized requirements"
                                detail="Coverage may be incomplete. Review source readability and the diagnostic limitations."
                              />
                            )}
                          </div>
                        </section>
                        {result.cv && (
                          <section className="panel padded">
                            <h2>CV qualification & chronology</h2>
                            <p className="muted">
                              The private node returns the qualification record
                              and any overlap-union ledger. Entered assignment
                              periods remain draft inputs unless supported and
                              reviewed.
                            </p>
                            <CvResult value={result.cv} />
                          </section>
                        )}
                        <div className="two-column">
                          <section className="panel padded">
                            <h2>Gap register</h2>
                            {array(result.gaps).length ? (
                              array(result.gaps).map((g, i) => (
                                <div className="gap-row" key={i}>
                                  <TriangleAlert size={18} />
                                  <div>
                                    <strong>
                                      {g.title ||
                                        String(
                                          array(result.requirements).find(
                                            (requirement) =>
                                              requirement.id ===
                                              g.requirement_id,
                                          )?.quote || "Evidence gap",
                                        ).slice(0, 100)}
                                    </strong>
                                    <div className="result-badges">
                                      {g.severity && (
                                        <Badge tone="amber">
                                          {label(g.severity)}
                                        </Badge>
                                      )}
                                      {g.status && (
                                        <Badge>{label(g.status)}</Badge>
                                      )}
                                    </div>
                                    <p>
                                      {g.action ||
                                        g.next_action ||
                                        g.description ||
                                        g.reason ||
                                        g.message ||
                                        "Review the linked finding and collect the missing evidence."}
                                    </p>
                                    <JsonDetails
                                      value={g}
                                      title="Technical reference"
                                    />
                                  </div>
                                </div>
                              ))
                            ) : (
                              <p className="muted">
                                No gap rows returned. This alone does not
                                establish complete tender coverage.
                              </p>
                            )}
                          </section>
                          <section className="panel padded">
                            <h2>Coverage & limitations</h2>
                            <JsonDetails
                              value={result.coverage}
                              title="Extraction coverage"
                            />
                            {array(result.limitations).map((item, i) => (
                              <p className="limitation" key={i}>
                                {typeof item === "string"
                                  ? item
                                  : JSON.stringify(item)}
                              </p>
                            ))}
                            <JsonDetails
                              value={result.sources}
                              title="Local source manifest"
                            />
                          </section>
                        </div>
                        {internal && (
                          <section className="panel padded review-panel">
                            <p className="eyebrow">ASSIGNED INTERNAL REVIEW</p>
                            <h2>Record a source-based review</h2>
                            <p className="muted">
                              A review changes the finding record. It cannot
                              bypass evidence checks, extraction coverage or
                              pending release policies.
                            </p>
                            <div className="form-grid">
                              <Field label="Requirement">
                                <select
                                  value={review.requirement_id || ""}
                                  onChange={(e) =>
                                    setReview({
                                      ...review,
                                      requirement_id: e.target.value,
                                    })
                                  }
                                >
                                  <option value="">Select a requirement</option>
                                  {array(result.requirements).map((r) => (
                                    <option value={r.id} key={r.id}>
                                      {String(r.quote || "Requirement").slice(
                                        0,
                                        80,
                                      )}
                                      {r.mandatory ? " · mandatory" : ""}
                                    </option>
                                  ))}
                                </select>
                              </Field>
                              <Field label="Finding status">
                                <select
                                  value={review.finding_status}
                                  onChange={(e) =>
                                    setReview({
                                      ...review,
                                      finding_status: e.target.value,
                                    })
                                  }
                                >
                                  {[
                                    "MATCHED",
                                    "PARTIAL",
                                    "MISSING",
                                    "UNCLEAR",
                                    "NOT_APPLICABLE",
                                  ].map((s) => (
                                    <option key={s}>{s}</option>
                                  ))}
                                </select>
                              </Field>
                              <Field label="Evidence document">
                                <select
                                  value={review.evidence_source_id || ""}
                                  onChange={(e) =>
                                    setReview({
                                      ...review,
                                      evidence_source_id: e.target.value,
                                    })
                                  }
                                >
                                  <option value="">
                                    Choose the supporting document
                                  </option>
                                  {array(result.sources).map(
                                    (source, index) => (
                                      <option
                                        key={
                                          source.id || source.source_id || index
                                        }
                                        value={source.id || source.source_id}
                                      >
                                        {source.filename ||
                                          source.name ||
                                          source.title ||
                                          `Source document ${index + 1}`}
                                      </option>
                                    ),
                                  )}
                                </select>
                              </Field>
                              <Field label="Evidence page">
                                <input
                                  type="number"
                                  min="1"
                                  value={review.evidence_page}
                                  onChange={(e) =>
                                    setReview({
                                      ...review,
                                      evidence_page: Number(e.target.value),
                                    })
                                  }
                                />
                              </Field>
                              <Field label="Evidence assurance">
                                <select
                                  value={review.assurance}
                                  onChange={(e) =>
                                    setReview({
                                      ...review,
                                      assurance: e.target.value,
                                    })
                                  }
                                >
                                  {[
                                    "SOURCE_LOCATED",
                                    "CLIENT_CONFIRMED",
                                    "DOCUMENT_SUPPORTED",
                                    "INDEPENDENTLY_VERIFIED",
                                    "CONFLICTED",
                                    "UNRESOLVED",
                                  ].map((s) => (
                                    <option key={s}>{s}</option>
                                  ))}
                                </select>
                              </Field>
                              <Field label="Exact evidence quote">
                                <textarea
                                  value={review.evidence_quote || ""}
                                  onChange={(e) =>
                                    setReview({
                                      ...review,
                                      evidence_quote: e.target.value,
                                    })
                                  }
                                />
                              </Field>
                              <Field label="Review rationale">
                                <textarea
                                  value={review.rationale || ""}
                                  onChange={(e) =>
                                    setReview({
                                      ...review,
                                      rationale: e.target.value,
                                    })
                                  }
                                />
                              </Field>
                            </div>
                            <label className="checkbox-line">
                              <input
                                type="checkbox"
                                checked={coverageReviewed}
                                onChange={(e) =>
                                  setCoverageReviewed(e.target.checked)
                                }
                              />
                              I reviewed the relevant source section coverage.
                            </label>
                            <button
                              className="button primary"
                              disabled={
                                !canProcess ||
                                !review.requirement_id ||
                                !review.rationale?.trim() ||
                                Boolean(busy)
                              }
                              onClick={() =>
                                void run(
                                  "review",
                                  () =>
                                    command("REVIEW", {
                                      reviews: [review],
                                      coverage_reviewed: coverageReviewed,
                                    }),
                                  "Review queued for private verification.",
                                )
                              }
                            >
                              <Check size={17} />
                              Submit encrypted review
                            </button>
                            <p className="caption">
                              Confirm local processing permission on the Case
                              overview tab before submitting.
                            </p>
                          </section>
                        )}
                      </>
                    ) : (
                      <Empty
                        title="Your matrix will appear here"
                        detail="Add documents and run an analysis. Findings are decrypted only in this browser."
                        icon={FileCheck2}
                      />
                    )}
                  </>
                )}

                {tab === "workbench" && (
                  <>
                    <div className="section-title">
                      <div>
                        <h2>Internal production workbenches</h2>
                        <p>
                          Managed authoring and research remain private,
                          assigned and preliminary.
                        </p>
                      </div>
                      <Badge tone="amber">No external retrieval</Badge>
                    </div>
                    {internal && isCandidate && (
                      <section className="panel padded">
                        <p className="eyebrow">OPTIONAL CV CHRONOLOGY INPUT</p>
                        <h2>Assignment periods / কাজের সময়কাল</h2>
                        <p className="muted">
                          These dates are draft operator inputs, not asserted
                          candidate facts. Upload supporting CV/evidence and
                          review the source. The private node calculates the
                          union of covered months so overlapping assignments are
                          not counted twice.
                        </p>
                        <div className="cv-periods">
                          {cvAssignments.map((period, i) => (
                            <div className="financial-line" key={i}>
                              <Field
                                label={`Assignment ${i + 1} · start month`}
                              >
                                <input
                                  type="month"
                                  value={period.start}
                                  onChange={(e) =>
                                    setCvAssignments(
                                      cvAssignments.map((item, index) =>
                                        index === i
                                          ? { ...item, start: e.target.value }
                                          : item,
                                      ),
                                    )
                                  }
                                />
                              </Field>
                              <Field label="End month (inclusive)">
                                <input
                                  type="month"
                                  value={period.end}
                                  onChange={(e) =>
                                    setCvAssignments(
                                      cvAssignments.map((item, index) =>
                                        index === i
                                          ? { ...item, end: e.target.value }
                                          : item,
                                      ),
                                    )
                                  }
                                />
                              </Field>
                              <button
                                className="icon-button"
                                aria-label={`Remove CV assignment ${i + 1}`}
                                onClick={() =>
                                  setCvAssignments(
                                    cvAssignments.filter(
                                      (_, index) => index !== i,
                                    ),
                                  )
                                }
                              >
                                <X size={17} />
                              </button>
                            </div>
                          ))}
                        </div>
                        <button
                          className="button secondary"
                          disabled={cvAssignments.length >= 40}
                          onClick={() =>
                            setCvAssignments([
                              ...cvAssignments,
                              { start: "", end: "" },
                            ])
                          }
                        >
                          <Plus size={16} />
                          Add assignment period
                        </button>
                        <p className="caption">
                          Completed periods are sent encrypted with your next
                          analysis or finding review. Leave all rows empty to
                          use document-only analysis.
                        </p>
                        {project.service_id === "B_CV_FIT" && (
                          <button
                            className="button primary"
                            disabled={
                              !canProcess ||
                              Boolean(busy) ||
                              jobs.some(activeJob) ||
                              !array(detail?.assets).some(
                                (asset) => asset.state === "ENCRYPTED",
                              )
                            }
                            onClick={() =>
                              void run(
                                "cv-analyse",
                                () => command("ANALYZE"),
                                "CV analysis with the entered draft periods queued.",
                              )
                            }
                          >
                            <ClipboardList size={16} />
                            Analyse CV with draft periods
                          </button>
                        )}
                      </section>
                    )}
                    {!internal ? (
                      <section className="panel padded">
                        <Empty
                          title="Managed work is handled by the internal team"
                          detail="Customers can request managed services and view authorized deliverables. Internal drafting actions require staff assignment."
                          icon={LockKeyhole}
                        />
                        <JsonDetails
                          value={detail?.orders}
                          title="Your work orders"
                        />
                      </section>
                    ) : (
                      <>
                        <div className="two-column">
                          <section className="panel padded">
                            <div className="section-icon">
                              <BookOpen size={23} />
                            </div>
                            <h2>Managed CV & proposal draft</h2>
                            <p className="muted">
                              Only confirmed source facts may support the draft.
                              Instructions are encrypted before leaving this
                              browser.
                            </p>
                            <Field label="Drafting brief / কাজের নির্দেশনা">
                              <textarea
                                rows={5}
                                value={draftInstructions}
                                onChange={(e) =>
                                  setDraftInstructions(e.target.value)
                                }
                                placeholder="Specify the requested sections and constraints."
                                maxLength={10000}
                              />
                            </Field>
                            <button
                              className="button primary"
                              disabled={
                                !canProcess ||
                                !["C_MANAGED_CV", "D_PROPOSAL"].includes(
                                  project.service_id,
                                ) ||
                                !draftInstructions.trim() ||
                                Boolean(busy)
                              }
                              onClick={() =>
                                void run(
                                  "draft",
                                  () =>
                                    command("MANAGED_DRAFT", {
                                      instructions: draftInstructions,
                                    }),
                                  "Managed draft queued.",
                                )
                              }
                            >
                              <Sparkles size={16} />
                              Prepare internal draft
                            </button>
                            <p className="caption">
                              Requires C/D case, work order and assigned staff.
                              Not a final deliverable.
                            </p>
                            {result?.managed && (
                              <JsonDetails
                                value={result.managed}
                                title="Decrypted managed draft"
                              />
                            )}
                          </section>
                          <section className="panel padded">
                            <div className="section-icon">
                              <Search size={23} />
                            </div>
                            <h2>Offline research workspace</h2>
                            <p className="muted">
                              Stored case files only. No web retrieval, hosted
                              AI or automatic research-to-proposal clearance.
                            </p>
                            <Field label="Research question">
                              <textarea
                                value={researchQuestion}
                                onChange={(e) =>
                                  setResearchQuestion(e.target.value)
                                }
                                maxLength={5000}
                              />
                            </Field>
                            <Field label="Working notes">
                              <textarea
                                value={researchNotes}
                                onChange={(e) =>
                                  setResearchNotes(e.target.value)
                                }
                                maxLength={10000}
                              />
                            </Field>
                            <button
                              className="button secondary"
                              disabled={
                                !canProcess ||
                                !["R_RESEARCH", "D_PROPOSAL"].includes(
                                  project.service_id,
                                ) ||
                                !researchQuestion.trim() ||
                                Boolean(busy)
                              }
                              onClick={() =>
                                void run(
                                  "research",
                                  () =>
                                    command("RESEARCH", {
                                      question: researchQuestion,
                                      notes: researchNotes,
                                      retrieval_allowed: false,
                                    }),
                                  "Offline research draft queued.",
                                )
                              }
                            >
                              <Search size={16} />
                              Build source-grounded draft
                            </button>
                            {result?.research && (
                              <JsonDetails
                                value={result.research}
                                title="Decrypted research draft"
                              />
                            )}
                          </section>
                        </div>
                        <section className="panel padded">
                          <div className="section-title">
                            <div>
                              <h2>Financial working sheet</h2>
                              <p>
                                Deterministic draft arithmetic from explicit
                                quantities and rates.
                              </p>
                            </div>
                            <Badge>Internal only</Badge>
                          </div>
                          <div className="financial-lines">
                            {lines.map((line, i) => (
                              <div className="financial-line" key={i}>
                                <Field label="Line description">
                                  <input
                                    value={line.label}
                                    maxLength={200}
                                    onChange={(e) =>
                                      setLines(
                                        lines.map((l, n) =>
                                          n === i
                                            ? { ...l, label: e.target.value }
                                            : l,
                                        ),
                                      )
                                    }
                                  />
                                </Field>
                                <Field label="Quantity">
                                  <input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={line.quantity}
                                    onChange={(e) =>
                                      setLines(
                                        lines.map((l, n) =>
                                          n === i
                                            ? { ...l, quantity: e.target.value }
                                            : l,
                                        ),
                                      )
                                    }
                                  />
                                </Field>
                                <Field label="Rate">
                                  <input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={line.rate}
                                    onChange={(e) =>
                                      setLines(
                                        lines.map((l, n) =>
                                          n === i
                                            ? { ...l, rate: e.target.value }
                                            : l,
                                        ),
                                      )
                                    }
                                  />
                                </Field>
                                <button
                                  className="icon-button"
                                  aria-label={`Remove line ${i + 1}`}
                                  disabled={lines.length === 1}
                                  onClick={() =>
                                    setLines(lines.filter((_, n) => n !== i))
                                  }
                                >
                                  <X size={17} />
                                </button>
                              </div>
                            ))}
                          </div>
                          <div className="financial-bottom">
                            <button
                              className="button secondary"
                              disabled={lines.length >= 40}
                              onClick={() =>
                                setLines([
                                  ...lines,
                                  { label: "", quantity: "1", rate: "0" },
                                ])
                              }
                            >
                              <Plus size={16} />
                              Add line
                            </button>
                            <Field label="Currency">
                              <input
                                value={currency}
                                maxLength={3}
                                onChange={(e) =>
                                  setCurrency(e.target.value.toUpperCase())
                                }
                              />
                            </Field>
                            <Field label="Tax % (explicit assumption)">
                              <input
                                type="number"
                                min="0"
                                max="100"
                                step="0.01"
                                value={tax}
                                onChange={(e) => setTax(e.target.value)}
                              />
                            </Field>
                            <button
                              className="button primary"
                              disabled={
                                !canProcess ||
                                project.service_id !== "D_PROPOSAL" ||
                                Boolean(busy)
                              }
                              onClick={() =>
                                void run(
                                  "financial",
                                  () =>
                                    command("FINANCIAL", {
                                      lines: lines.map((l) => ({
                                        ...l,
                                        quantity: Number(l.quantity),
                                        rate: Number(l.rate),
                                      })),
                                      currency,
                                      tax_percent: Number(tax),
                                    }),
                                  "Financial calculation queued.",
                                )
                              }
                            >
                              <Wallet size={17} />
                              Calculate draft
                            </button>
                          </div>
                          {result?.financial && (
                            <FinancialResult value={result.financial} />
                          )}
                        </section>
                        {user.role === "OWNER" && (
                          <section className="panel padded">
                            <h2>Case assignment</h2>
                            <form
                              className="inline-form"
                              onSubmit={(e) =>
                                submitForm(
                                  e,
                                  async (f) => {
                                    await post(
                                      `/projects/${project.id}/assign`,
                                      { user_id: f.get("user_id") },
                                    );
                                    await refreshCase(project.id);
                                  },
                                  "assign",
                                  "Staff assignment recorded.",
                                )
                              }
                            >
                              <Field label="Authorized staff user ID">
                                <input name="user_id" required />
                              </Field>
                              <button
                                className="button secondary"
                                disabled={Boolean(busy)}
                              >
                                Assign staff
                              </button>
                            </form>
                          </section>
                        )}
                      </>
                    )}
                    <p className="caption">
                      Confirm processing consent on Case overview. Candidate
                      consent is also required for CV services.
                    </p>
                  </>
                )}

                {tab === "reports" && (
                  <>
                    <div className="section-title">
                      <div>
                        <h2>Encrypted reports & artifacts</h2>
                        <p>
                          Downloads are decrypted in your browser. No plaintext
                          report is stored on the public broker.
                        </p>
                      </div>
                      <Badge tone="amber">PRELIMINARY</Badge>
                    </div>
                    <div className="alert info">
                      <LockKeyhole size={18} />
                      <span>
                        Use the same account and browser profile for source
                        uploads, processing and downloads. Its private keys and
                        case binding stay in IndexedDB. Cross-profile or staff
                        handoff and key recovery require future private
                        delegation.
                      </span>
                    </div>
                    <section className="panel">
                      {array(result?.artifacts).length ? (
                        <div className="artifact-grid">
                          {array(result?.artifacts).map((a) => (
                            <div className="artifact-card" key={a.id}>
                              <div className="artifact-icon">
                                <FileText size={28} />
                              </div>
                              <div>
                                <h3>{a.name}</h3>
                                <p>{a.mime}</p>
                                <Badge tone="amber">
                                  {label(a.readiness || result?.readiness)}
                                </Badge>
                              </div>
                              <button
                                className="button secondary"
                                onClick={() =>
                                  void run("download", async () =>
                                    downloadArtifact(
                                      resultJob?.project_version !==
                                        project.version
                                        ? { ...a, name: `HISTORICAL_${a.name}` }
                                        : a,
                                    ),
                                  )
                                }
                              >
                                <ArrowDownToLine size={17} />
                                Download
                              </button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <Empty
                          title="No report artifacts yet"
                          detail="A completed private-node run can return encrypted draft reports. Final release remains gated."
                          icon={FileText}
                        />
                      )}
                    </section>
                    {internal && (
                      <section className="panel padded">
                        <h2>Formal release is gated</h2>
                        <p className="muted">
                          Named policy approval, qualified review, current
                          snapshot and service gates must be recorded. This
                          development build does not infer approval from a
                          successful run.
                        </p>
                        <button
                          className="button secondary"
                          disabled={!canProcess || Boolean(busy)}
                          onClick={() =>
                            void run("release", () => command("RELEASE", {}))
                          }
                        >
                          <ShieldCheck size={17} />
                          Check release gate
                        </button>
                        <JsonDetails
                          value={result?.approval}
                          title="Current approval record"
                        />
                      </section>
                    )}
                    <p className="caption">
                      TenderOS provides decision support. It does not certify
                      procurement eligibility, submit tenders or guarantee an
                      award.
                    </p>
                  </>
                )}

                {tab === "activity" && (
                  <section className="panel padded">
                    <h2>Case audit trail</h2>
                    <p className="muted">
                      Broker events contain operational metadata. Detailed
                      evidence and private engine traces stay local.
                    </p>
                    {array(detail?.events).length ? (
                      <div className="timeline">
                        {array(detail?.events).map((event, i) => (
                          <div className="timeline-row" key={event.id || i}>
                            <div className="timeline-dot" />
                            <div>
                              <strong>
                                {label(
                                  event.action || event.type || event.event,
                                )}
                              </strong>
                              <p>
                                {date(event.created_at || event.timestamp)} ·{" "}
                                {event.actor_name || event.actor_id || "System"}
                              </p>
                              <JsonDetails
                                value={event.details || event.metadata}
                                title="Event metadata"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <Empty
                        title="No events returned"
                        detail="New case actions will be recorded in the audit history."
                      />
                    )}
                  </section>
                )}
              </>
            ))}

          {view === "operations" && internal && (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">VISIBLE OPERATIONS, EXPLICIT GATES</p>
                  <h1>Operations & readiness</h1>
                  <p>
                    Development activity is not production approval. Readiness
                    requires recorded evidence.
                  </p>
                </div>
                <button
                  className="button secondary"
                  onClick={() =>
                    void run("operations", async () => {
                      await refresh();
                      setOperations(await api("/operations"));
                    })
                  }
                >
                  <Activity size={17} />
                  Refresh
                </button>
              </div>
              <div className="two-column">
                <TrustPanel
                  node={node}
                  trust={trust}
                  error={trustError}
                  busy={Boolean(busy)}
                  onTrust={() =>
                    void run("trust", async () => {
                      await trustNode(node);
                      setTrust(await nodeTrust(node));
                    })
                  }
                />
                <section className="panel padded">
                  <h2>Commercial services</h2>
                  <div className="status-line">
                    <Wallet size={20} />
                    <strong>Payments disabled</strong>
                    <Badge tone="amber">PILOT_PC</Badge>
                  </div>
                  <p className="muted">
                    No live merchant checkout or paid launch. Sandbox status and
                    a payment notification cannot create a paid entitlement.
                  </p>
                  <div className="status-line">
                    <Server size={20} />
                    <span>Private node heartbeat</span>
                  </div>
                  <p>{date(node.last_seen_at || node.heartbeat_at)}</p>
                  <p className="caption">
                    A registered key does not prove the node is currently online
                    or production ready.
                  </p>
                </section>
              </div>
              <section className="panel padded">
                <h2>Acceptance gates</h2>
                <p className="muted">
                  G0 design, G1A private slice, G1B broker, G2 pilot and GS
                  dedicated server precede a paid launch authorization.
                </p>
                <JsonDetails
                  value={operations?.gates || boot?.gates}
                  title="Recorded gate states"
                />
                <div className="gate-row">
                  {array(operations?.gates || boot?.gates).map((g) => (
                    <div key={g.id} title={g.detail}>
                      <ShieldCheck size={21} />
                      <strong>{g.id}</strong>
                      <small>{label(g.state)}</small>
                    </div>
                  ))}
                </div>
                <p className="caption">
                  No model benchmark, independent crypto review, backup restore,
                  legal approval or signed production readiness is asserted.
                </p>
              </section>
              {operations && (
                <section className="panel padded">
                  <h2>Authorized operational metadata</h2>
                  <JsonDetails
                    value={operations}
                    title="Node, queue and service information"
                  />
                </section>
              )}
            </>
          )}

          {view === "privacy" && (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">PRIVATE BY BOUNDARY</p>
                  <h1>Privacy & support</h1>
                  <p>
                    আপনার নথি, আপনার নিয়ন্ত্রণ। Understand where information is
                    processed.
                  </p>
                </div>
              </div>
              <div className="two-column">
                <section className="panel padded">
                  <h2>Where your information lives</h2>
                  <div className="privacy-row">
                    <LockKeyhole size={21} />
                    <div>
                      <strong>In this browser</strong>
                      <p>
                        Selected file plaintext, encryption and decrypted
                        reports. Non-extractable per-case download keys are
                        stored in IndexedDB.
                      </p>
                    </div>
                  </div>
                  <div className="privacy-row">
                    <Workflow size={21} />
                    <div>
                      <strong>On the public broker</strong>
                      <p>
                        Account and case metadata, encrypted asset envelopes,
                        durable job status and request records.
                      </p>
                    </div>
                  </div>
                  <div className="privacy-row">
                    <Server size={21} />
                    <div>
                      <strong>On the private owner computer</strong>
                      <p>
                        Decryption, source parsing, private knowledge engine,
                        evidence, local inference and draft production.
                      </p>
                    </div>
                  </div>
                  <div className="alert info">
                    <TriangleAlert size={18} />
                    <span>
                      Development key pinning is not an independently signed
                      production trust manifest. A compromised browser or
                      uploader can access plaintext before encryption.
                    </span>
                  </div>
                </section>
                <section className="panel padded">
                  <h2>Request support or deletion</h2>
                  <p className="muted">
                    Choose a case. Requests are recorded for follow-up;
                    submitting a deletion request does not mean the data has
                    already been deleted.
                  </p>
                  <Field label="Case">
                    <select
                      value={selected || ""}
                      onChange={(e) => {
                        selectedRef.current = e.target.value;
                        setSelected(e.target.value || null);
                      }}
                    >
                      <option value="">Choose a case</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.title}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Support / consultation message">
                    <textarea
                      value={message}
                      maxLength={1000}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Operational questions only. Do not paste private document content."
                    />
                  </Field>
                  <button
                    className="button secondary"
                    disabled={!selected || !message.trim() || Boolean(busy)}
                    onClick={() =>
                      void run(
                        "consult",
                        async () => {
                          await post(`/projects/${selected}/consultations`, {
                            message,
                          });
                          setMessage("");
                        },
                        "Support request recorded. No appointment or delivery promise has been made.",
                      )
                    }
                  >
                    <Send size={16} />
                    Send request
                  </button>
                  <hr />
                  <Field label="Reason for deletion request">
                    <textarea
                      value={deleteReason}
                      maxLength={1000}
                      onChange={(e) => setDeleteReason(e.target.value)}
                    />
                  </Field>
                  <button
                    className="button danger"
                    disabled={
                      !selected || !deleteReason.trim() || Boolean(busy)
                    }
                    onClick={() =>
                      void run(
                        "delete",
                        async () => {
                          await post(
                            `/projects/${selected}/deletion-requests`,
                            { reason: deleteReason },
                          );
                          setDeleteReason("");
                        },
                        "Deletion request recorded for owner review. Completion and retention exceptions require confirmation.",
                      )
                    }
                  >
                    Request case deletion
                  </button>
                </section>
              </div>
            </>
          )}
          <footer className="footer">
            <span>
              TenderOS <b>·</b> Evidence-led decisions
            </span>
            <span>
              <LockKeyhole size={12} /> Owner-controlled local development · Not
              a paid production service
            </span>
          </footer>
        </main>
      </div>

      {showNew && (
        <div className="modal-backdrop" onClick={() => setShowNew(false)}>
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="new-case-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-heading">
              <div>
                <p className="eyebrow">START WITH A CASE</p>
                <h2 id="new-case-title">New tender case / নতুন কেস</h2>
              </div>
              <button
                className="icon-button"
                aria-label="Close dialog"
                onClick={() => setShowNew(false)}
              >
                <X size={21} />
              </button>
            </div>
            <p className="muted">
              Case names and bidder/issuer identifiers are broker metadata. Keep
              sensitive source content in encrypted documents.
            </p>
            <form
              onSubmit={(e) =>
                submitForm(
                  e,
                  async (f) => {
                    const values = Object.fromEntries(f);
                    const deadline = values.deadline
                      ? new Date(String(values.deadline)).toISOString()
                      : null;
                    const created = await post("/projects", {
                      ...values,
                      deadline,
                    });
                    await refresh();
                    setShowNew(false);
                    openCase(created.project?.id || created.id);
                  },
                  "create",
                )
              }
            >
              <Field label="Case title">
                <input
                  name="title"
                  required
                  minLength={3}
                  autoFocus
                  maxLength={160}
                  placeholder="e.g. Urban resilience technical assistance"
                />
              </Field>
              <div className="form-grid">
                <Field label="Bidder / organization">
                  <input name="bidder" required minLength={2} maxLength={160} />
                </Field>
                <Field label="Issuer">
                  <input name="issuer" required minLength={2} maxLength={160} />
                </Field>
                <Field label="Deadline (your browser’s local time)">
                  <input name="deadline" type="datetime-local" />
                </Field>
                <Field label="Service profile">
                  <select name="service_id" id="new-service">
                    {SERVICES.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.letter} — {s.title}
                      </option>
                    ))}
                    {internal && (
                      <option value="R_RESEARCH">
                        R — Internal offline research
                      </option>
                    )}
                  </select>
                </Field>
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="button secondary"
                  onClick={() => setShowNew(false)}
                >
                  Cancel
                </button>
                <button className="button primary" disabled={Boolean(busy)}>
                  <Plus size={17} />
                  {busy === "create" ? "Creating…" : "Create case"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}

function CaseTable({
  projects,
  open,
}: {
  projects: Json[];
  open: (id: string) => void;
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Case / organization</th>
            <th>Service</th>
            <th>State</th>
            <th>Deadline</th>
            <th>
              <span className="sr-only">Open case</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {projects.map((p) => (
            <tr key={p.id}>
              <td>
                <button className="case-title" onClick={() => open(p.id)}>
                  {p.title}
                </button>
                <small className="block">{p.bidder}</small>
              </td>
              <td>
                <Badge>
                  {SERVICES.find((s) => s.id === p.service_id)?.letter ||
                    p.service_id}
                </Badge>
              </td>
              <td>
                <Badge tone="teal">
                  {label(p.state || p.status || "DRAFT")}
                </Badge>
              </td>
              <td>
                {p.deadline
                  ? new Date(p.deadline).toLocaleDateString("en-GB", {
                      timeZone: "Asia/Dhaka",
                    })
                  : "Not set"}
              </td>
              <td>
                <button
                  className="icon-button"
                  aria-label={`Open ${p.title}`}
                  onClick={() => open(p.id)}
                >
                  <ArrowRight size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!projects.length && (
        <Empty
          title="No matching cases"
          detail="Try another title, bidder or issuer."
        />
      )}
    </div>
  );
}
function TrustPanel({
  node,
  trust,
  error,
  busy,
  onTrust,
}: {
  node: Json;
  trust: { fingerprint: string; trusted: boolean } | null;
  error: string;
  busy: boolean;
  onTrust: () => void;
}) {
  return (
    <section className="panel padded trust-panel">
      <div className="panel-title-icon">
        <LockKeyhole size={21} />
        <h2>Local encryption boundary</h2>
      </div>
      <p className="muted">
        Documents and commands are encrypted before broker upload. Only the
        owner node can decrypt inputs.
      </p>
      {error ? (
        <div className="alert error">
          <TriangleAlert size={17} />
          <span>{error}</span>
        </div>
      ) : trust ? (
        <>
          <div className="fingerprint-label">NODE PUBLIC KEY · SHA-256</div>
          <code className="fingerprint">
            {trust.fingerprint.match(/.{1,4}/g)?.join(" ")}
          </code>
          {trust.trusted ? (
            <div className="trusted">
              <CheckCircle2 size={17} />
              Pinned in this browser
            </div>
          ) : (
            <>
              <p className="caption">
                First use: compare this fingerprint with the owner’s local node
                output. This is a development trust decision, not a signed
                production manifest.
              </p>
              <button
                className="button secondary wide"
                disabled={busy}
                onClick={onTrust}
              >
                <ShieldCheck size={17} />
                Trust this local node key
              </button>
            </>
          )}
        </>
      ) : (
        <div className="small-note">
          <Server size={18} />
          <span>
            No node encryption key is available. Start the owner-controlled node
            before uploading.
          </span>
        </div>
      )}
      <p className="caption">
        Key ID: {node.key_id || "not registered"} · No automatic external
        provider fallback.
      </p>
    </section>
  );
}

function CvResult({ value }: { value: Json }) {
  return (
    <div className="cv-result">
      <div className="result-badges">
        <Badge tone="amber">{label(value.status)}</Badge>
        <Badge
          tone={value.qualification_clearance === "PASS" ? "teal" : "amber"}
        >
          Qualification: {label(value.qualification_clearance)}
        </Badge>
      </div>
      <div className="duration-cards">
        {[
          {
            label: "Unique experience",
            value: value.unique_months,
            detail: "Covered months, counted once",
          },
          {
            label: "Gross assignment time",
            value: value.gross_months,
            detail: "Before removing overlaps",
          },
          {
            label: "Overlapping months",
            value: value.overlap_months,
            detail: "Removed from double counting",
          },
        ].map((item) => (
          <div key={item.label}>
            <span>{item.label}</span>
            <strong>
              {item.value ?? "—"} <small>months</small>
            </strong>
            <p>{item.detail}</p>
          </div>
        ))}
      </div>
      {array(value.assignments).length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Draft assignment period</th>
                <th>Start</th>
                <th>End</th>
                <th>Duration</th>
              </tr>
            </thead>
            <tbody>
              {array(value.assignments).map((assignment, i) => (
                <tr key={i}>
                  <td>{assignment.label || `Assignment ${i + 1}`}</td>
                  <td>{assignment.start || "—"}</td>
                  <td>{assignment.end || "—"}</td>
                  <td>
                    {assignment.months ?? assignment.duration_months ?? "—"}{" "}
                    months
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {array(value.issues).map((issue, i) => (
        <p className="limitation" key={i}>
          {typeof issue === "string" ? issue : JSON.stringify(issue)}
        </p>
      ))}
      <p className="caption">
        {typeof value.duration_policy === "string"
          ? value.duration_policy
          : "Experience arithmetic is separate from source verification and the role’s minimum qualifications."}
      </p>
      <JsonDetails
        value={value}
        title="Source facts and full chronology record"
      />
    </div>
  );
}
function FinancialResult({ value }: { value: Json }) {
  const number = (input: any) =>
    input === null || input === undefined
      ? "—"
      : Number.isFinite(Number(input))
        ? new Intl.NumberFormat("en-GB", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }).format(Number(input))
        : String(input);
  return (
    <div className="financial-result">
      <hr />
      <div className="section-title">
        <div>
          <h3>Financial draft calculation</h3>
          <p>
            Calculated on the private node. Rates and tax remain explicit input
            assumptions.
          </p>
        </div>
        <Badge tone="amber">{label(value.status)}</Badge>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Description</th>
              <th>Quantity</th>
              <th>Rate</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            {array(value.lines).map((line, i) => (
              <tr key={i}>
                <td>{line.label}</td>
                <td>{number(line.quantity)}</td>
                <td>{number(line.rate)}</td>
                <td>
                  {number(line.amount)} {line.currency || value.currency}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="financial-totals">
        <div>
          <span>Subtotal</span>
          <strong>
            {number(value.subtotal)} {value.currency}
          </strong>
        </div>
        <div>
          <span>Tax ({value.tax_percent ?? "—"}%)</span>
          <strong>
            {number(value.tax)} {value.currency}
          </strong>
        </div>
        <div className="total">
          <span>Total</span>
          <strong>
            {number(value.total)} {value.currency}
          </strong>
        </div>
      </div>
      <p className="caption">
        {value.assumptions_approved
          ? "Assumptions marked approved in the local result."
          : "Assumptions require authorized review before a managed deliverable can be released."}
      </p>
      {array(value.limitations).map((item, i) => (
        <p className="limitation" key={i}>
          {typeof item === "string" ? item : JSON.stringify(item)}
        </p>
      ))}
      <JsonDetails
        value={{
          rounding: value.rounding,
          reconciliation: value.reconciliation,
          assumptions_approved: value.assumptions_approved,
        }}
        title="Reconciliation and calculation policy"
      />
    </div>
  );
}

function SourceReference({
  sources,
  id,
  page,
  clause,
}: {
  sources: Json[];
  id: any;
  page?: any;
  clause?: any;
}) {
  const source = id
    ? sources.find((item) => item.id === id || item.source_id === id)
    : undefined;
  const filename =
    source?.filename || source?.name || source?.title || "Source document";
  return (
    <small className="block">
      <strong style={{ display: "inline", fontWeight: 500 }}>{filename}</strong>
      {page ? ` · page ${page}` : ""}
      {clause ? ` · ${clause}` : ""}
      {!page && !clause ? " · location needs review" : ""}
    </small>
  );
}
