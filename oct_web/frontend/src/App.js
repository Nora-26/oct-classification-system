import React, { useState, useRef, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { predictImage } from './api';
import './App.css';
// 放在 App.js 顶部，import 之后
const MAX_HISTORY = 20;

// ─── 压缩图片 ────────────────────────────────────────────────────────────
async function compressToThumbnail(base64DataUrl, size = 128, quality = 0.6) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');
      const scale = Math.max(size / img.width, size / img.height);
      const w = img.width * scale;
      const h = img.height * scale;
      ctx.drawImage(img, (size - w) / 2, (size - h) / 2, w, h);
      resolve(canvas.toDataURL('image/jpeg', quality));
    };
    img.onerror = () => resolve(null);
    img.src = base64DataUrl;
  });
}

// ─── 历史记录 ────────────────────────────────────────────────────────────
function useHistory() {
  const [history, setHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('oct_history') || '[]');
    } catch { return []; }
  });
// ─── 添加历史记录 ────────────────────────────────────────────────────────────
  const addRecord = useCallback(async (result, overlayImage, fileName) => {
    const thumbnail = await compressToThumbnail(overlayImage);
    const record = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      fileName,
      result,
      overlayImage: thumbnail,
    };
    setHistory(prev => {
      const next = [record, ...prev].slice(0, MAX_HISTORY);
      try {
        localStorage.setItem('oct_history', JSON.stringify(next));
      } catch (e) {
        const half = next.slice(0, Math.floor(next.length / 2));
        try { localStorage.setItem('oct_history', JSON.stringify(half)); } catch {}
        return half;
      }
      return next;
    });
  }, []);
// ─── 删除历史记录 ────────────────────────────────────────────────────────────
  const deleteRecord = useCallback((id) => {
    setHistory(prev => {
      const next = prev.filter(r => r.id !== id);
      localStorage.setItem('oct_history', JSON.stringify(next));
      return next;
    });
  }, []);
// ─── 清空历史记录 ────────────────────────────────────────────────────────────
  const clearAll = useCallback(() => {
    localStorage.removeItem('oct_history');
    setHistory([]);
  }, []);

  return { history, addRecord, deleteRecord, clearAll };
}

// ─── 生成报告 ────────────────────────────────────────────────────────
function generateReportHTML(result, originalImageUrl, overlayImageUrl, filename) {
  const now = new Date();
  const dateStr = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
  const timeStr = now.toLocaleTimeString('zh-CN');
  const reportId = 'OCT-' + Date.now().toString(36).toUpperCase();
// ─── 诊断结论 ────────────────────────────────────────────────────────────
  const severityMap = {
    NORMAL: { level: '正常', color: '#10b981', bg: '#d1fae5', border: '#6ee7b7' },
    CNV:    { level: '需紧急就医', color: '#ef4444', bg: '#fee2e2', border: '#fca5a5' },
    DME:    { level: '需积极治疗', color: '#f97316', bg: '#ffedd5', border: '#fdba74' },
    DRUSEN: { level: '需定期复查', color: '#eab308', bg: '#fef9c3', border: '#fde047' },
  };
  const sev = severityMap[result.class] || severityMap.NORMAL;
// ─── 各类别概率分布 ────────────────────────────────────────────────────────────
  const probRows = Object.entries(result.probabilities)
    .map(([name, prob]) => {
      const pct = (prob * 100).toFixed(1);
      const isTop = name === result.class;
      return `
        <tr style="background:${isTop ? '#f0f7ff' : 'white'}">
          <td style="padding:10px 16px;font-weight:${isTop ? '700' : '400'};color:${isTop ? '#1E40AF' : '#374151'}">${name}</td>
          <td style="padding:10px 16px">
            <div style="background:#e5e7eb;border-radius:99px;height:10px;overflow:hidden">
              <div style="background:${isTop ? 'linear-gradient(90deg,#3B82F6,#60A5FA)' : '#9CA3AF'};width:${pct}%;height:100%;border-radius:99px"></div>
            </div>
          </td>
          <td style="padding:10px 16px;text-align:right;font-weight:${isTop ? '700' : '400'};color:${isTop ? '#1E40AF' : '#374151'}">${pct}%</td>
        </tr>`;
    }).join('');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <title>OCT 诊断报告 ${reportId}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Noto Sans SC',sans-serif;background:#f8fafc;color:#1e293b;padding:40px 20px}
    .page{max-width:860px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 40px rgba(0,0,0,.1)}
    .cover{background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 50%,#0f172a 100%);padding:48px;color:white;position:relative;overflow:hidden}
    .cover::before{content:'';position:absolute;top:-80px;right:-80px;width:300px;height:300px;background:radial-gradient(circle,rgba(59,130,246,.3),transparent 70%);pointer-events:none}
    .cover-tag{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#60A5FA;margin-bottom:16px}
    .cover-title{font-size:32px;font-weight:700;letter-spacing:1px;margin-bottom:8px}
    .cover-sub{font-size:14px;color:#94a3b8;margin-bottom:32px}
    .cover-meta{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;border-top:1px solid rgba(255,255,255,.1);padding-top:24px}
    .meta-item label{font-size:10px;letter-spacing:2px;color:#64748b;display:block;margin-bottom:4px}
    .meta-item span{font-size:14px;color:#e2e8f0}
    .body{padding:40px}
    .section{margin-bottom:36px}
    .section-title{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#64748b;margin-bottom:16px;display:flex;align-items:center;gap:8px}
    .section-title::after{content:'';flex:1;height:1px;background:#e2e8f0}
    .verdict-card{border:2px solid ${sev.border};background:${sev.bg};border-radius:12px;padding:24px;display:flex;align-items:center;gap:20px}
    .verdict-icon{font-size:40px;flex-shrink:0}
    .verdict-name{font-size:22px;font-weight:700;color:${sev.color};margin-bottom:4px}
    .verdict-level{font-size:13px;color:#64748b}
    .confidence-display{display:flex;align-items:center;gap:16px;margin-top:12px}
    .conf-label{font-size:13px;color:#64748b;white-space:nowrap}
    .conf-bar{flex:1;background:#e2e8f0;border-radius:99px;height:12px;overflow:hidden}
    .conf-fill{background:linear-gradient(90deg,#3B82F6,#60A5FA);height:100%;border-radius:99px}
    .conf-value{font-size:18px;font-weight:700;color:#1e40af;white-space:nowrap}
    .images-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    .img-box{border-radius:10px;overflow:hidden;border:1px solid #e2e8f0}
    .img-box img{width:100%;display:block;object-fit:cover}
    .img-label{font-size:12px;color:#64748b;text-align:center;padding:8px;background:#f8fafc}
    table{width:100%;border-collapse:collapse;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0}
    th{background:#f1f5f9;padding:10px 16px;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#64748b;text-align:left}
    .desc-box{background:#f8fafc;border-radius:10px;padding:20px;font-size:14px;line-height:1.8;color:#374151;border-left:4px solid #3B82F6}
    .rec-box{background:#fffbeb;border-radius:10px;padding:20px;font-size:14px;line-height:1.8;color:#78350f;border-left:4px solid #f59e0b}
    .rec-box strong{display:block;margin-bottom:6px;font-size:13px;letter-spacing:1px;color:#92400e}
    .disclaimer{background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:16px 20px;font-size:12px;color:#991b1b;line-height:1.7}
    .footer-bar{background:#0f172a;padding:20px 40px;display:flex;justify-content:space-between;align-items:center}
    .footer-bar span{font-size:11px;color:#475569}
    @media print{body{padding:0;background:white}.page{box-shadow:none;border-radius:0}}
  </style>
</head>
<body>
<div class="page">
  <div class="cover">
    <div class="cover-tag">Medical Imaging AI Report</div>
    <div class="cover-title">眼底 OCT 智能诊断报告</div>
    <div class="cover-sub">Optical Coherence Tomography Classification Analysis</div>
    <div class="cover-meta">
      <div class="meta-item"><label>报告编号</label><span>${reportId}</span></div>
      <div class="meta-item"><label>分析日期</label><span>${dateStr}</span></div>
      <div class="meta-item"><label>分析时间</label><span>${timeStr}</span></div>
      <div class="meta-item"><label>图像文件</label><span>${filename || '未知'}</span></div>
      <div class="meta-item"><label>分析模型</label><span>EfficientNet-B0</span></div>
      <div class="meta-item"><label>系统版本</label><span>v1.0.0</span></div>
    </div>
  </div>

  <div class="body">
    <div class="section">
      <div class="section-title">诊断结论</div>
      <div class="verdict-card">
        <div class="verdict-icon">${result.icon}</div>
        <div style="flex:1">
          <div class="verdict-name">${result.class_name} (${result.class})</div>
          <div class="verdict-level">风险评级：${sev.level}</div>
          <div class="confidence-display">
            <span class="conf-label">置信度</span>
            <div class="conf-bar"><div class="conf-fill" style="width:${(result.confidence*100).toFixed(1)}%"></div></div>
            <span class="conf-value">${(result.confidence*100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">影像对比</div>
      <div class="images-grid">
        <div class="img-box">
          <img src="${originalImageUrl}" alt="原始图像"/>
          <div class="img-label">原始 OCT 图像</div>
        </div>
        <div class="img-box">
          <img src="${overlayImageUrl}" alt="标注图像"/>
          <div class="img-label">AI 病灶标注图像</div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">各类别概率分布</div>
      <table>
        <thead><tr><th>分类</th><th>概率分布</th><th style="text-align:right">概率值</th></tr></thead>
        <tbody>${probRows}</tbody>
      </table>
    </div>

    <div class="section">
      <div class="section-title">病情说明</div>
      <div class="desc-box">${result.description}</div>
    </div>

    <div class="section">
      <div class="section-title">医疗建议</div>
      <div class="rec-box">
        <strong>💡 临床建议</strong>
        ${result.recommendation}
      </div>
    </div>

    <div class="section">
      <div class="section-title">重要声明</div>
      <div class="disclaimer">
        ⚠️ <strong>本报告仅供参考，不构成临床诊断依据。</strong>本系统基于人工智能深度学习模型对 OCT 影像进行自动分析，结果可能存在误差。
        所有诊断及治疗决策须由具备资质的眼科医生根据患者完整临床资料作出判断。如有疑问，请及时就医。
      </div>
    </div>
  </div>

  <div class="footer-bar">
    <span>© 2026 眼底 OCT 智能分类系统</span>
    <span>报告 ID: ${reportId} | 仅供医学研究辅助使用</span>
  </div>
</div>
<script>window.onload=()=>window.print()</script>
</body>
</html>`;
}

function downloadReport(result, originalImageUrl, overlayImageUrl, filename) {
  const html = generateReportHTML(result, originalImageUrl, overlayImageUrl, filename);
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const win = window.open(url, '_blank');
  if (!win) {
    // 下载文件
    const a = document.createElement('a');
    a.href = url;
    a.download = `OCT_Report_${Date.now()}.html`;
    a.click();
  }
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

// ─── 概率条 ──────────────────────────────────────────────────────────
function ProbBar({ name, prob, isTop }) {
  const pct = (prob * 100).toFixed(1);
  return (
    <div className={`prob-row ${isTop ? 'prob-row--top' : ''}`}>
      <div className="prob-row-header">
        <span className="prob-name">{name}</span>
        <span className="prob-pct">{pct}%</span>
      </div>
      <div className="prob-track">
        <div className="prob-fill" style={{ width: `${pct}%`, '--pct': `${pct}%` }} />
      </div>
    </div>
  );
}
// ─── 历史记录面板 ────────────────────────────────────────────────────────────
function HistoryPanel({ history, onSelect, onDelete, onClear, onClose }) {
  const severityColor = { NORMAL:'#10b981', CNV:'#ef4444', DME:'#f97316', DRUSEN:'#eab308' };

  return (
    <div className="hist-backdrop" onClick={onClose}>
      <aside className="hist-panel" onClick={e => e.stopPropagation()}>
        <div className="hist-header">
          <span className="panel-label" style={{margin:0}}>历史记录</span>
          <div style={{display:'flex',gap:8}}>
            {history.length > 0 && (
              <button className="hist-action-btn" onClick={onClear}>清空</button>
            )}
            <button className="hist-action-btn" onClick={onClose}>✕ 关闭</button>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="hist-empty">暂无历史记录</div>
        ) : (
          <ul className="hist-list">
            {history.map(rec => {
              const date = new Date(rec.timestamp);
              const dateStr = date.toLocaleDateString('zh-CN');
              const timeStr = date.toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'});
              const color = severityColor[rec.result.class] || '#64748b';

              return (
                <li key={rec.id} className="hist-item" onClick={() => onSelect(rec)}>
                  <img
                    src={rec.overlayImage}
                    alt="thumb"
                    className="hist-thumb"
                  />
                  <div className="hist-item-info">
                    <div className="hist-item-name">{rec.fileName}</div>
                    <div className="hist-item-meta">
                      <span style={{color, fontWeight:600}}>{rec.result.icon} {rec.result.class_name}</span>
                      <span className="hist-item-conf">{(rec.result.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="hist-item-time">{dateStr} {timeStr}</div>
                  </div>
                  <button
                    className="hist-del-btn"
                    onClick={e => { e.stopPropagation(); onDelete(rec.id); }}
                    title="删除此记录"
                  >✕</button>
                </li>
              );
            })}
          </ul>
        )}
      </aside>
    </div>
  );
}

// ─── 主应用 ─────────────────────────────────────────────────────────────────
export default function App() {
  const [originalImage, setOriginalImage] = useState(null);
  const [overlayImage, setOverlayImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');
  const [activeTab, setActiveTab] = useState('original');
  const [dragOver, setDragOver] = useState(false);
  const { history, addRecord, deleteRecord, clearAll } = useHistory();
  const [showHistory, setShowHistory] = useState(false);
// ─── 上传图像 ────────────────────────────────────────────────────────────
  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;
    setFileName(file.name);
    const url = URL.createObjectURL(file);
    setOriginalImage(url);
    setOverlayImage(null);
    setResult(null);
    setLoading(true);
    setActiveTab('original');
    try {
      const data = await predictImage(file);
      setOverlayImage(`data:image/png;base64,${data.overlay_image}`);
      setResult(data);
      await addRecord(data, `data:image/png;base64,${data.overlay_image}`, file.name);
      setActiveTab('overlay');
    } catch (err) {
      console.error(err);
      alert('预测失败，请检查后端服务是否正常运行。');
    } finally {
      setLoading(false);
    }
  }, []);
// ─── 拖拽上传 ────────────────────────────────────────────────────────────
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    onDragEnter: () => setDragOver(true),
    onDragLeave: () => setDragOver(false),
    onDropAccepted: () => setDragOver(false),
  });
// ─── 诊断结论 ────────────────────────────────────────────────────────────
  const severityClass = result ? {
    NORMAL: 'sev-normal', CNV: 'sev-critical', DME: 'sev-high', DRUSEN: 'sev-medium'
  }[result.class] || '' : '';

  return (
    <div className="app">
      {/* ── 头部 ── */}
      <header className="site-header">
        <div className="header-inner">
          <div className="header-brand">
            <div className="brand-icon">
              <svg viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="20" r="18" stroke="currentColor" strokeWidth="2"/>
                <circle cx="20" cy="20" r="8" fill="currentColor" opacity=".3"/>
                <circle cx="20" cy="20" r="3" fill="currentColor"/>
                <line x1="20" y1="2" x2="20" y2="10" stroke="currentColor" strokeWidth="2"/>
                <line x1="20" y1="30" x2="20" y2="38" stroke="currentColor" strokeWidth="2"/>
                <line x1="2" y1="20" x2="10" y2="20" stroke="currentColor" strokeWidth="2"/>
                <line x1="30" y1="20" x2="38" y2="20" stroke="currentColor" strokeWidth="2"/>
              </svg>
            </div>
            <div>
              <h1 className="brand-title">OCT 智能诊断</h1>
              <p className="brand-sub">Retinal OCT Classification System</p>
            </div>
          </div>
          <div className="header-badges">
            <span className="badge">EfficientNet-B0</span>
            <span className="badge badge--green">● 服务运行中</span>
            <button className="badge badge--btn" onClick={() => setShowHistory(v => !v)}>
              🕐 历史记录 {history.length > 0 && <span className="hist-count">{history.length}</span>}
            </button>
          </div>
        </div>
      </header>

      {/* ── 主内容区域 ── */}
      <main className="main-grid">
        {/* ── 影像输入 ── */}
        <section className="panel panel--left">
          <div className="panel-label">影像输入</div>

          {/* 拖拽上传 */}
          <div
            {...getRootProps()}
            className={`dropzone ${isDragActive || dragOver ? 'dropzone--active' : ''} ${originalImage ? 'dropzone--filled' : ''}`}
          >
            <input {...getInputProps()} />
            {!originalImage ? (
              <div className="dropzone-prompt">
                <div className="drop-icon">
                  <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <rect x="6" y="10" width="36" height="28" rx="4"/>
                    <circle cx="18" cy="22" r="4"/>
                    <path d="M6 32l10-8 8 6 6-4 12 10"/>
                  </svg>
                </div>
                <p className="drop-title">拖拽 OCT 图像至此</p>
                <p className="drop-sub">或点击选择文件 · 支持 JPG / PNG / BMP</p>
              </div>
            ) : (
              <div className="preview-wrapper">
                {/* Tab Switcher */}
                <div className="img-tabs">
                  <button
                    className={`img-tab ${activeTab === 'original' ? 'img-tab--active' : ''}`}
                    onClick={e => { e.stopPropagation(); setActiveTab('original'); }}
                  >原始图像</button>
                  {overlayImage && (
                    <button
                      className={`img-tab ${activeTab === 'overlay' ? 'img-tab--active' : ''}`}
                      onClick={e => { e.stopPropagation(); setActiveTab('overlay'); }}
                    >AI 标注</button>
                  )}
                </div>
                <img
                  src={activeTab === 'overlay' && overlayImage ? overlayImage : originalImage}
                  alt="OCT Preview"
                  className="preview-img"
                />
                <div className="preview-filename">{fileName}</div>
                {loading && (
                  <div className="loading-overlay">
                    <div className="spinner"/>
                    <span>AI 分析中…</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Re-upload hint */}
          {originalImage && (
            <p className="re-upload-hint">
              <span {...getRootProps()} style={{cursor:'pointer',color:'var(--accent)'}}>点击此处</span> 重新上传图像
            </p>
          )}
        </section>

        {/* ── 诊断结果 ── */}
        <section className="panel panel--right">
          <div className="panel-label">诊断结果</div>

          {!result && !loading && (
            <div className="empty-state">
              <div className="empty-icon">
                <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="1.2">
                  <path d="M32 8C18.7 8 8 18.7 8 32s10.7 24 24 24 24-10.7 24-24S45.3 8 32 8z"/>
                  <path d="M32 20v16M32 40v2" strokeWidth="2.5" strokeLinecap="round"/>
                </svg>
              </div>
              <p>上传 OCT 图像后</p>
              <p>AI 将自动分析并显示结果</p>
            </div>
          )}

          {loading && !result && (
            <div className="empty-state">
              <div className="scanning-anim">
                <div className="scan-ring"/>
                <div className="scan-ring scan-ring--2"/>
                <div className="scan-dot"/>
              </div>
              <p style={{marginTop:'16px',color:'var(--accent)'}}>正在分析影像…</p>
            </div>
          )}

          {result && (
            <div className="results-content">
              {/* 诊断结论 */}
              <div className={`verdict ${severityClass}`}>
                <div className="verdict-icon-wrap">{result.icon}</div>
                <div className="verdict-info">
                  <div className="verdict-name">{result.class_name}</div>
                  <div className="verdict-code">{result.class}</div>
                </div>
                <div className="verdict-conf">
                  <div className="conf-num">{(result.confidence * 100).toFixed(1)}<span>%</span></div>
                  <div className="conf-label">置信度</div>
                </div>
              </div>

              {/* 置信度环 */}
              <div className="conf-section">
                <div className="conf-bar-wrap">
                  <div className="conf-track">
                    <div className="conf-fill-bar" style={{ width: `${result.confidence * 100}%` }}/>
                  </div>
                  <span className="conf-text">{(result.confidence * 100).toFixed(1)}% 置信度</span>
                </div>
              </div>

              {/* 各类别概率分布 */}
              <div className="card">
                <div className="card-title">
                  <svg viewBox="0 0 16 16" fill="currentColor"><path d="M2 12h2v2H2zm4-4h2v6H6zm4-4h2v10h-2zm4-4h2v14h-2z"/></svg>
                  各类别概率分布
                </div>
                {Object.entries(result.probabilities).map(([name, prob]) => (
                  <ProbBar key={name} name={name} prob={prob} isTop={name === result.class} />
                ))}
              </div>

              {/* 病情说明 */}
              <div className="card card--info">
                <div className="card-title">
                  <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 3a1 1 0 110 2 1 1 0 010-2zm0 3.5c.28 0 .5.22.5.5v3a.5.5 0 01-1 0V8c0-.28.22-.5.5-.5z"/></svg>
                  病情说明
                </div>
                <p className="card-body">{result.description}</p>
              </div>

              {/* 医疗建议 */}
              <div className="card card--warn">
                <div className="card-title">
                  <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 1L1 14h14L8 1zm0 3l5.4 9H2.6L8 4zm0 3v3m0 1v1"/></svg>
                  医疗建议
                </div>
                <p className="card-body">{result.recommendation}</p>
              </div>

              {/* 生成报告 */}
              <button
                className="report-btn"
                onClick={() => downloadReport(result, originalImage, overlayImage, fileName)}
              >
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/>
                  <path d="M10 13l-3-3m3 3l3-3m-3 3V7" stroke="white" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
                </svg>
                生成诊断报告 (HTML)
              </button>
            </div>
          )}
        </section>
        {showHistory && (
          <HistoryPanel
            history={history}
            onSelect={(rec) => {
              setOverlayImage(rec.overlayImage);
              setResult(rec.result);
              setFileName(rec.fileName);
              setActiveTab('overlay');
              setShowHistory(false);
            }}
            onDelete={deleteRecord}
            onClear={clearAll}
            onClose={() => setShowHistory(false)}
         />
       )}
      </main>

      {/* ── 底部 ── */}
      <footer className="site-footer">
        <span>© 2026 眼底 OCT 智能分类系统 · EfficientNet-B0 · 仅供医学研究辅助</span>
        <span className="footer-warn">⚠ 本系统不能替代专业医生的诊断意见</span>
      </footer>
    </div>
  );
}
