import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import {
  ArrowRight, BookOpen, Bot, BrainCircuit, CheckCircle2, ChevronRight, CircleHelp, FileBarChart,
  FileText, FolderOpen, GraduationCap, LayoutDashboard, Library, LogOut, Menu, MessageSquare,
  Network, Plus, Search, Send, Sparkles, Trash2, Upload, X, Zap
} from 'lucide-react'
import api, { apiError } from './services/api'

const NAV = [
  ['dashboard', 'Dashboard', LayoutDashboard], ['papers', 'My papers', FolderOpen], ['workspace', 'Research studio', BrainCircuit],
  ['compare', 'Compare papers', Network], ['literature', 'Literature review', Library], ['analytics', 'Trend analytics', FileBarChart],
]
const SUMMARY_LABELS = {
  abstract_summary: 'Abstract summary', introduction_summary: 'Introduction', problem_statement: 'Problem statement', research_objectives: 'Research objectives',
  methodology: 'Methodology', algorithms_used: 'Algorithms used', dataset_information: 'Dataset information', experimental_results: 'Experimental results',
  advantages: 'Advantages', limitations: 'Limitations', conclusion: 'Conclusion', future_scope: 'Future scope',
}

function useAsync(callback, dependencies = []) {
  const [state, setState] = useState({ loading: false, error: '', data: null })
  const run = useCallback(async (...args) => {
    setState({ loading: true, error: '', data: null })
    try { const data = await callback(...args); setState({ loading: false, error: '', data }); return data }
    catch (error) { setState({ loading: false, error: apiError(error), data: null }); throw error }
  }, dependencies)
  return [state, run, setState]
}

function App() {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(true)
  const [notice, setNotice] = useState(null)
  useEffect(() => {
    const token = localStorage.getItem('research_token')
    if (!token) return setBooting(false)
    api.get('/api/auth/me').then(({ data }) => setUser(data)).catch(() => localStorage.removeItem('research_token')).finally(() => setBooting(false))
  }, [])
  const onAuth = (payload) => { localStorage.setItem('research_token', payload.access_token); setUser(payload.user); setNotice({ type: 'success', text: 'Welcome to your research workspace.' }) }
  const logout = () => { localStorage.removeItem('research_token'); setUser(null) }
  if (booting) return <div className="splash"><Sparkles /> Loading your research workspace…</div>
  return user ? <AppShell user={user} onLogout={logout} notice={notice} setNotice={setNotice} /> : <AuthScreen onAuth={onAuth} />
}

function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event) => {
    event.preventDefault(); setLoading(true); setError('')
    try { const { data } = await api.post(`/api/auth/${mode === 'login' ? 'login' : 'register'}`, form); onAuth(data) }
    catch (err) { setError(apiError(err)) } finally { setLoading(false) }
  }
  return <main className="auth-page">
    <section className="auth-hero">
      <div className="brand"><span><BrainCircuit /></span> Paperly</div>
      <div className="hero-copy"><div className="eyebrow"><Sparkles size={14} /> Research, amplified</div><h1>Make every paper<br /><i>intelligible.</i></h1><p>A private AI research desk for reading deeply, finding evidence, and seeing what comes next.</p></div>
      <div className="hero-orb orb-one" /><div className="hero-orb orb-two" />
      <div className="feature-stack"><span><CheckCircle2 /> Grounded in your PDFs</span><span><CheckCircle2 /> Evidence with page citations</span><span><CheckCircle2 /> Private by design</span></div>
    </section>
    <section className="auth-panel"><div className="auth-card"><div className="mobile-brand brand"><span><BrainCircuit /></span> Paperly</div><p className="eyebrow">{mode === 'login' ? 'Welcome back' : 'Start your workspace'}</p><h2>{mode === 'login' ? 'Continue your research.' : 'Build your research edge.'}</h2><p className="muted">{mode === 'login' ? 'Sign in to return to your private library.' : 'Create a private workspace in seconds.'}</p>
      <form onSubmit={submit}>{mode === 'register' && <label>Full name<input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required minLength="2" placeholder="Ada Lovelace" /></label>}<label>Email<input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required placeholder="you@university.edu" /></label><label>Password<input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required minLength="8" placeholder="At least 8 characters" /></label>{error && <div className="form-error">{error}</div>}<button className="primary full" disabled={loading}>{loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'} <ArrowRight size={17} /></button></form>
      <p className="auth-switch">{mode === 'login' ? 'New to Paperly?' : 'Already have an account?'} <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></p>
    </div></section>
  </main>
}

function AppShell({ user, onLogout, notice, setNotice }) {
  const [page, setPage] = useState('dashboard'), [sidebarOpen, setSidebarOpen] = useState(false)
  const [papers, setPapers] = useState([]), [selectedId, setSelectedId] = useState(null)
  const refreshPapers = useCallback(async () => { const { data } = await api.get('/api/papers'); setPapers(data); return data }, [])
  useEffect(() => { refreshPapers().catch(() => setNotice({ type: 'error', text: 'Could not load your papers.' })) }, [refreshPapers])
  const choosePaper = (id, destination = 'workspace') => { setSelectedId(id); setPage(destination); setSidebarOpen(false) }
  return <div className="app-shell">
    <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}><div className="brand"><span><BrainCircuit /></span> Paperly</div><nav>{NAV.map(([id, label, Icon]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => { setPage(id); setSidebarOpen(false) }}><Icon size={19} />{label}</button>)}</nav><div className="sidebar-bottom"><div className="upgrade-card"><Zap size={17} /><span>Bring your next idea into focus.</span></div><div className="profile"><div className="avatar">{user.name.slice(0, 1).toUpperCase()}</div><div><strong>{user.name}</strong><small>{user.email}</small></div><button onClick={onLogout} title="Sign out"><LogOut size={17} /></button></div></div></aside>
    <main className="main"><header className="topbar"><button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}><Menu /></button><div><p className="page-kicker">YOUR PRIVATE RESEARCH DESK</p><h1>{NAV.find(item => item[0] === page)?.[1] || 'Paperly'}</h1></div><button className="upload-shortcut" onClick={() => setPage('papers')}><Plus size={17} /> Upload paper</button></header>
      {notice && <Toast notice={notice} onClose={() => setNotice(null)} />}
      <div className="content">{page === 'dashboard' && <Dashboard papers={papers} selectPaper={choosePaper} goUpload={() => setPage('papers')} />}{page === 'papers' && <Papers papers={papers} refresh={refreshPapers} selectPaper={choosePaper} setNotice={setNotice} />}{page === 'workspace' && <Studio papers={papers} selectedId={selectedId} selectPaper={setSelectedId} />}{page === 'compare' && <Compare papers={papers} selectPaper={choosePaper} />}{page === 'literature' && <Literature papers={papers} />}{page === 'analytics' && <Analytics />}</div>
    </main></div>
}

function Toast({ notice, onClose }) { useEffect(() => { const id = setTimeout(onClose, 4200); return () => clearTimeout(id) }, [onClose]); return <div className={`toast ${notice.type}`}><CheckCircle2 size={18} />{notice.text}<button onClick={onClose}><X size={15} /></button></div> }

function Dashboard({ papers, selectPaper, goUpload }) {
  const [stats, setStats] = useState(null), [trends, setTrends] = useState(null), [error, setError] = useState('')
  useEffect(() => { Promise.all([api.get('/api/dashboard/stats'), api.get('/api/analytics/research-trends')]).then(([a, b]) => { setStats(a.data); setTrends(b.data) }).catch(e => setError(apiError(e))) }, [papers.length])
  if (error) return <ErrorState message={error} />
  if (!stats) return <LoadingPanel label="Mapping your research library" />
  return <><section className="welcome-row"><div><div className="eyebrow"><Sparkles size={14} /> A sharper research practice</div><h2>Good {new Date().getHours() < 12 ? 'morning' : 'afternoon'}, researcher.</h2><p>Turn a shelf of PDFs into a connected body of knowledge.</p></div><button className="primary" onClick={goUpload}><Upload size={17} /> Add a paper</button></section>
    <section className="metric-grid"><Metric icon={<FileText />} value={stats.total_papers} label="Papers in library" tone="library" /><Metric icon={<Sparkles />} value={stats.papers_analyzed} label="Papers analyzed" tone="analyzed" /><Metric icon={<BrainCircuit />} value={stats.analysis_runs} label="Intelligence runs" tone="intelligence" /></section>
    {papers.length === 0 ? <EmptyState icon={<BookOpen />} title="Your research library starts here" text="Upload a PDF to extract its evidence, explore it with grounded chat, and uncover connections." action="Upload your first paper" onAction={goUpload} /> : <section className="dashboard-grid"><div className="panel recent-panel"><PanelHeading title="Recently added" action="View all" onAction={goUpload} />{stats.recent_papers.map(paper => <button className="paper-row" key={paper.id} onClick={() => selectPaper(paper.id)}><div className="file-icon"><FileText size={18} /></div><div><strong>{paper.title}</strong><small>{paper.topic || 'Uncategorized'} · {paper.status}</small></div><ChevronRight size={18} /></button>)}</div><div className="panel chart-panel"><PanelHeading title="Research areas" /><MiniPie data={trends?.topics || []} /></div></section>}</>
}

function Metric({ icon, value, label, tone }) { return <div className={`metric ${tone}`}><div className="metric-icon">{icon}</div><div><strong>{value}</strong><span>{label}</span></div></div> }
function PanelHeading({ title, action, onAction }) { return <div className="panel-heading"><h3>{title}</h3>{action && <button onClick={onAction}>{action} <ArrowRight size={14} /></button>}</div> }

function Papers({ papers, refresh, selectPaper, setNotice }) {
  const [query, setQuery] = useState(''), [uploading, setUploading] = useState(false), [dragging, setDragging] = useState(false), [error, setError] = useState('')
  const input = useRef(null)
  const upload = async (file) => { if (!file) return; if (file.type !== 'application/pdf') return setError('Please select a PDF document.'); setUploading(true); setError(''); const form = new FormData(); form.append('file', file); try { const { data } = await api.post('/api/papers/upload', form); await refresh(); setNotice({ type: 'success', text: `“${data.title}” is ready to explore.` }) } catch (e) { setError(apiError(e)) } finally { setUploading(false) } }
  const remove = async (event, id) => { event.stopPropagation(); if (!window.confirm('Delete this paper and all of its extracted data?')) return; try { await api.delete(`/api/papers/${id}`); await refresh(); setNotice({ type: 'success', text: 'Paper removed from your library.' }) } catch (e) { setError(apiError(e)) } }
  const listed = papers.filter(paper => paper.title.toLowerCase().includes(query.toLowerCase()) || (paper.topic || '').toLowerCase().includes(query.toLowerCase()))
  return <><section className="upload-zone" onDragOver={e => { e.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); upload(e.dataTransfer.files[0]) }}><div className={`drop-inner ${dragging ? 'dragging' : ''}`}><div className="drop-icon"><Upload /></div><div><h2>{uploading ? 'Reading and indexing your paper…' : 'Bring a paper into focus.'}</h2><p>Drop a PDF here, or choose a file. Your document stays private to your workspace.</p></div><button className="secondary" onClick={() => input.current?.click()} disabled={uploading}>{uploading ? 'Processing…' : 'Choose PDF'}</button><input ref={input} type="file" accept="application/pdf" hidden onChange={e => upload(e.target.files[0])} /></div>{error && <div className="inline-error">{error}</div>}</section>
    <section className="library-head"><div><h2>Paper library <span>{papers.length}</span></h2><p>Your source material, organized and searchable.</p></div><div className="search"><Search size={17} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search papers" /></div></section>
    {listed.length === 0 ? <EmptyState icon={<FolderOpen />} title={papers.length ? 'No matching papers' : 'Nothing here yet'} text={papers.length ? 'Try another search phrase.' : 'Drop a research paper above to get started.'} /> : <div className="paper-grid">{listed.map(paper => <article className="paper-card" key={paper.id} onClick={() => selectPaper(paper.id)}><div className="card-top"><div className="file-icon"><FileText /></div><button className="delete-btn" onClick={e => remove(e, paper.id)} title="Delete paper"><Trash2 size={16} /></button></div><div className="status-line"><span className={paper.status === 'ready' ? 'ready-dot' : 'pending-dot'} /> {paper.status.replace('_', ' ')}</div><h3>{paper.title}</h3><p>{paper.topic || 'No research area assigned'}</p><footer><span>{paper.page_count} pages</span><span>{new Date(paper.created_at).toLocaleDateString()}</span></footer></article>)}</div>}</>
}

function Studio({ papers, selectedId, selectPaper }) {
  const paper = papers.find(item => item.id === selectedId) || papers[0]
  const [tab, setTab] = useState('summary'), [data, setData] = useState(null), [loading, setLoading] = useState(false), [error, setError] = useState(''), [messages, setMessages] = useState([]), [question, setQuestion] = useState(''), [session, setSession] = useState(null)
  useEffect(() => { setData(null); setMessages([]); setSession(null); setError('') }, [paper?.id])
  const runAnalysis = async (kind) => { if (!paper) return; setLoading(true); setError(''); try { const config = kind === 'summary' ? { detail_level: 'medium' } : undefined; const { data: result } = await api.post(`/api/analysis/${paper.id}/${kind === 'gaps' ? 'research-gaps' : kind}`, config); setData(result.content) } catch (e) { setError(apiError(e)) } finally { setLoading(false) } }
  const download = async (format) => { try { const response = await api.get(`/api/exports/${paper.id}/summary?format=${format}`, { responseType: 'blob' }); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = `${paper.title.replace(/[^a-z0-9]/gi, '-')}-summary.${format}`; link.click(); URL.revokeObjectURL(url) } catch (e) { setError(apiError(e)) } }
  useEffect(() => { if (paper && tab !== 'chat') runAnalysis(tab) }, [paper?.id, tab])
  const ask = async (event) => { event.preventDefault(); if (!question.trim() || !paper) return; const prompt = question; setQuestion(''); setMessages(current => [...current, { role: 'user', content: prompt }]); try { const { data: result } = await api.post(`/api/chat/${paper.id}`, { question: prompt, session_id: session }); setSession(result.session_id); setMessages(current => [...current, { role: 'assistant', content: result.answer, sources: result.sources }]) } catch (e) { setMessages(current => [...current, { role: 'assistant', content: `Error: ${apiError(e)}` }]) } }
  if (!papers.length) return <EmptyState icon={<BrainCircuit />} title="The research studio is waiting" text="Upload a paper first, then return here to pull out its evidence and ask grounded questions." />
  return <div className="studio"><aside className="studio-sidebar"><p className="eyebrow">ACTIVE PAPER</p><select value={paper?.id || ''} onChange={e => selectPaper(Number(e.target.value))}>{papers.map(item => <option value={item.id} key={item.id}>{item.title}</option>)}</select><div className="active-paper"><FileText /><strong>{paper?.title}</strong><small>{paper?.page_count} pages · {paper?.status}</small></div><button onClick={() => download('pdf')}><FileText size={16} /> Export PDF</button><button onClick={() => download('docx')}><FileText size={16} /> Export DOCX</button></aside><section className="studio-main"><div className="tabs">{[['summary', 'Summary'], ['methodology', 'Methodology'], ['gaps', 'Research gaps'], ['chat', 'Ask paper']].map(([id, label]) => <button key={id} className={tab === id ? 'selected' : ''} onClick={() => setTab(id)}>{id === 'chat' && <MessageSquare size={15} />}{label}</button>)}</div>{error && <div className="inline-error">{error}</div>}{tab === 'chat' ? <ChatPanel messages={messages} question={question} setQuestion={setQuestion} ask={ask} /> : loading ? <LoadingPanel label="Extracting paper-grounded evidence" /> : <AnalysisPanel data={data} tab={tab} />}</section></div>
}

function AnalysisPanel({ data, tab }) { if (!data) return <LoadingPanel label="Preparing the analysis" />; if (tab === 'gaps') return <div className="analysis-content"><div className="safety-note"><CircleHelp size={17} /><span>Paper-stated evidence and AI-generated hypotheses are intentionally kept separate.</span></div><article><h3>Paper-stated limitations</h3><p>{data.paper_stated_limitations}</p></article><article><h3>AI-generated hypotheses</h3>{data.ai_generated_hypotheses?.length ? data.ai_generated_hypotheses.map(item => <p key={item}>{item}</p>) : <p className="muted">{data.notice}</p>}</article></div>; return <div className="analysis-content">{Object.entries(data).map(([key, value]) => <article key={key}><h3>{(SUMMARY_LABELS[key] || key.replaceAll('_', ' ')).replace(/\b\w/g, letter => letter.toUpperCase())}</h3><p>{value}</p></article>)}</div> }
function ChatPanel({ messages, question, setQuestion, ask }) { return <div className="chat"><div className="chat-messages">{messages.length === 0 && <div className="chat-empty"><Bot /><h3>Ask what matters.</h3><p>Answers stay grounded in the selected PDF and include supporting page excerpts.</p><div>{['What problem does this paper solve?', 'Explain the methodology simply.', 'What are its limitations?'].map(prompt => <button key={prompt} onClick={() => setQuestion(prompt)}>{prompt}</button>)}</div></div>}{messages.map((message, index) => <div className={`bubble ${message.role}`} key={index}><p>{message.content}</p>{message.sources?.length > 0 && <div className="source-list">{message.sources.map((source, i) => <span key={i}>p. {source.page}</span>)}</div>}</div>)}</div><form className="chat-input" onSubmit={ask}><input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask about this paper…" /><button className="primary" disabled={!question.trim()}><Send size={17} /></button></form></div> }

function Compare({ papers, selectPaper }) { const [chosen, setChosen] = useState([]), [rows, setRows] = useState(null), [loading, setLoading] = useState(false), [error, setError] = useState(''); const toggle = id => setChosen(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id]); const run = async () => { setLoading(true); setError(''); try { const { data } = await api.post('/api/compare', { paper_ids: chosen }); setRows(data.rows) } catch (e) { setError(apiError(e)) } finally { setLoading(false) } }; if (papers.length < 2) return <EmptyState icon={<Network />} title="Comparison needs at least two papers" text="Add another paper to your library to map their shared and divergent approaches." />; return <><section className="compare-intro"><div><div className="eyebrow"><Network size={14} /> CROSS-PAPER INTELLIGENCE</div><h2>See the research landscape, not just one paper.</h2><p>Select up to six papers and compare only what their source text supports.</p></div><button className="primary" disabled={chosen.length < 2 || loading} onClick={run}>{loading ? 'Comparing…' : `Compare ${chosen.length} papers`} <ArrowRight size={16} /></button></section><div className="select-paper-grid">{papers.map(paper => <button className={`select-paper ${chosen.includes(paper.id) ? 'chosen' : ''}`} key={paper.id} onClick={() => toggle(paper.id)}><span className="check">{chosen.includes(paper.id) && <CheckCircle2 />}</span><FileText /><strong>{paper.title}</strong><small>{paper.topic || 'Uncategorized'}</small></button>)}</div>{error && <div className="inline-error">{error}</div>}{rows && <div className="comparison-table"><table><thead><tr><th>Dimension</th>{rows.map(row => <th key={row.paper_id}>{row.paper}</th>)}</tr></thead><tbody>{['research_objective', 'methodology', 'algorithms', 'dataset', 'evaluation_metrics', 'results', 'limitations', 'future_directions'].map(key => <tr key={key}><td>{key.replaceAll('_', ' ')}</td>{rows.map(row => <td key={row.paper_id}>{row[key]}</td>)}</tr>)}</tbody></table></div>}</> }

function Literature({ papers }) { const [chosen, setChosen] = useState([]), [title, setTitle] = useState(''), [result, setResult] = useState(null), [loading, setLoading] = useState(false), [error, setError] = useState(''); const create = async e => { e.preventDefault(); setLoading(true); setError(''); try { const { data } = await api.post('/api/literature-review/generate', { paper_ids: chosen, title }); setResult(data) } catch (err) { setError(apiError(err)) } finally { setLoading(false) } }; return <div className="literature-layout"><section className="panel review-form"><div className="eyebrow"><Library size={14} /> EVIDENCE-LED DRAFTING</div><h2>Literature review assistant</h2><p>Organize evidence across uploaded papers—without fabricated citations.</p><form onSubmit={create}><label>Draft title<input value={title} onChange={e => setTitle(e.target.value)} required minLength="3" placeholder="A review of…" /></label><label>Include papers <span className="label-note">{chosen.length} selected</span></label><div className="review-paper-list">{papers.map(paper => <label key={paper.id} className="checkbox-row"><input type="checkbox" checked={chosen.includes(paper.id)} onChange={() => setChosen(old => old.includes(paper.id) ? old.filter(id => id !== paper.id) : [...old, paper.id])} /><span>{paper.title}</span></label>)}</div>{error && <div className="inline-error">{error}</div>}<button className="primary full" disabled={!chosen.length || loading}>{loading ? 'Organizing evidence…' : 'Generate draft'} <ArrowRight size={16} /></button></form></section><section className="review-output">{result ? <article className="review-document"><div className="document-top"><span><BookOpen size={17} /> Evidence draft</span><button onClick={() => navigator.clipboard.writeText(result.content)}>Copy</button></div><div className="markdown">{result.content.split('\n').map((line, index) => line.startsWith('# ') ? <h1 key={index}>{line.slice(2)}</h1> : line.startsWith('## ') ? <h2 key={index}>{line.slice(3)}</h2> : line.startsWith('### ') ? <h3 key={index}>{line.slice(4)}</h3> : line ? <p key={index}>{line.replaceAll('**', '')}</p> : null)}</div></article> : <EmptyState icon={<GraduationCap />} title="Turn sources into structure" text="Choose papers, name your review, and this space will organize only their evidence." />}</section></div> }

function Analytics() { const [trends, setTrends] = useState(null), [error, setError] = useState(''); useEffect(() => { api.get('/api/analytics/research-trends').then(({ data }) => setTrends(data)).catch(e => setError(apiError(e))) }, []); if (error) return <ErrorState message={error} />; if (!trends) return <LoadingPanel label="Reading trends from your paper library" />; const hasData = Object.values(trends).some(group => group.length); if (!hasData) return <EmptyState icon={<FileBarChart />} title="Insights appear as your library grows" text="Upload papers with research areas and extracted text to see actual topic, dataset, and model trends." />; return <><section className="compare-intro"><div><div className="eyebrow"><FileBarChart size={14} /> YOUR RESEARCH CORPUS</div><h2>Patterns from actual extracted data.</h2><p>Charts update from the papers in your private workspace.</p></div></section><div className="analytics-grid"><ChartCard title="Research areas"><MiniPie data={trends.topics} /></ChartCard><ChartCard title="Algorithm mentions"><BarView data={trends.algorithms} /></ChartCard><ChartCard title="Publication years"><BarView data={trends.publication_years} /></ChartCard><ChartCard title="Dataset / corpus mentions"><BarView data={trends.datasets} /></ChartCard></div></> }
function MiniPie({ data }) { if (!data.length) return <div className="no-chart">No categorized papers yet.</div>; const colors = ['#C8792C', '#F4D9A0', '#9B7653', '#E5A95D', '#D8BE91']; return <div className="topic-breakdown">{data.map((entry, index) => <div className="topic-row" key={entry.name}><span className="topic-swatch" style={{ background: colors[index % colors.length] }} /><span className="topic-name" title={entry.name}>{entry.name}</span><span className="topic-count">{entry.value} {entry.value === 1 ? 'paper' : 'papers'}</span><span className="topic-track"><i style={{ width: `${Math.max(8, Math.round(entry.value / Math.max(...data.map(item => item.value)) * 100))}%`, background: colors[index % colors.length] }} /></span></div>)}</div> }
function BarView({ data }) { if (!data.length) return <div className="no-chart">No extracted values yet.</div>; return <ResponsiveContainer width="100%" height={210}><BarChart data={data}><CartesianGrid stroke="#5B4632" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" tick={{ fill: '#d4bfa0', fontSize: 11 }} /><YAxis allowDecimals={false} tick={{ fill: '#d4bfa0', fontSize: 11 }} /><Tooltip cursor={{ fill: '#5B4632' }} contentStyle={{ background: '#33261c', border: '1px solid #70583f', borderRadius: 10 }} /><Bar dataKey="value" fill="#C8792C" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer> }
function ChartCard({ title, children }) { return <section className="panel chart-card"><PanelHeading title={title} />{children}</section> }
function EmptyState({ icon, title, text, action, onAction }) { return <section className="empty"><div>{icon}</div><h2>{title}</h2><p>{text}</p>{action && <button className="primary" onClick={onAction}>{action} <ArrowRight size={16} /></button>}</section> }
function LoadingPanel({ label }) { return <div className="loading"><span /><p>{label}…</p></div> }
function ErrorState({ message }) { return <section className="empty error-state"><div><CircleHelp /></div><h2>We couldn’t load this view.</h2><p>{message}</p><button className="secondary" onClick={() => location.reload()}>Try again</button></section> }

export default App
