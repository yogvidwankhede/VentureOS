
    // ── GLOBALS ──
    let currentIdea = '', currentContext = {}, chatHistory = [], currentProductStrategy = {};
    let protoHtml = '', finData = [], reportText = '', selectedSeed = -1, protoGenCount = 0;
    let agentStartTime = 0, analysisStartTime = 0;

    // ── DARK MODE ──
    function toggleDark() {
      document.body.classList.toggle('dark');
      const isDark = document.body.classList.contains('dark');
      document.getElementById('darkToggle').textContent = isDark ? '☀️' : '🌙';
      localStorage.setItem('ventureos_dark', isDark ? '1' : '0');
    }
    if (localStorage.getItem('ventureos_dark') === '1') {
      document.body.classList.add('dark');
      document.getElementById('darkToggle').textContent = '☀️';
    }

    // ── VOICE ──
    let recognition = null, isListening = false;
    function initVoice() {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) { document.getElementById('micBtn').classList.add('unsupported'); return; }
      recognition = new SR(); recognition.continuous = false; recognition.interimResults = true; recognition.lang = 'en-US';
      recognition.onstart = () => { isListening = true; document.getElementById('micBtn').classList.add('listening'); document.getElementById('micBtn').textContent = '⏹'; document.getElementById('voiceStatus').classList.add('visible'); document.getElementById('voiceStatusText').textContent = 'Listening...'; };
      recognition.onresult = (e) => { let final = '', interim = ''; for (let i = e.resultIndex; i < e.results.length; i++) { const t = e.results[i][0].transcript; if (e.results[i].isFinal) final += t; else interim += t; } if (final) { document.getElementById('ideaInput').value = final; document.getElementById('voiceStatusText').textContent = '✓ Captured!'; } else if (interim) document.getElementById('voiceStatusText').textContent = `Hearing: "${interim}"`; };
      recognition.onerror = (e) => { stopListening(); };
      recognition.onend = () => stopListening();
    }
    function stopListening() { isListening = false; document.getElementById('micBtn').classList.remove('listening'); document.getElementById('micBtn').textContent = '🎤'; if (!document.getElementById('voiceStatusText').textContent.includes('✓')) document.getElementById('voiceStatus').classList.remove('visible'); }
    function toggleVoice() { if (document.getElementById('micBtn').classList.contains('unsupported')) return; if (!recognition) { initVoice(); if (!recognition) return; } if (isListening) recognition.stop(); else { document.getElementById('voiceStatus').classList.add('visible'); try { recognition.start(); } catch(e) { recognition.stop(); setTimeout(() => recognition.start(), 200); } } }

    document.addEventListener('DOMContentLoaded', () => { initVoice(); loadHistory(); });

    // ── EXAMPLE IDEAS ──
    function loadExample(btn) {
      const text = btn.textContent.replace(/^[^\s]+\s/, ''); // strip emoji
      document.getElementById('ideaInput').value = text;
      document.getElementById('ideaInput').focus();
      document.getElementById('launch').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // ── UTILS ──
    function v(x) { return (x === null || x === undefined || x === '') ? '—' : x; }
    function fmt(n) { return '$' + Math.round(n).toLocaleString(); }
    function fmtK(n) { if (n >= 1000000) return '$' + (n/1000000).toFixed(1) + 'M'; if (n >= 1000) return '$' + (n/1000).toFixed(1) + 'K'; return fmt(n); }
    function elapsed() { return ((Date.now() - agentStartTime) / 1000).toFixed(1) + 's'; }

    document.addEventListener('click', e => { const h = e.target.closest('.rcard-hd'); if (!h) return; const body = h.nextElementSibling; const open = body.classList.toggle('open'); h.classList.toggle('open', open); });

    function mkCard(icon, title, bodyHtml, badgeHtml) {
      const d = document.createElement('div'); d.className = 'rcard';
      d.innerHTML = `<div class="rcard-hd open"><div class="rcard-ico">${icon}</div><div class="rcard-ttl">${title}</div>${badgeHtml||''}<div class="rcard-chev">▾</div></div><div class="rcard-body open">${bodyHtml}</div>`;
      return d;
    }

    // ── PROGRESS BAR ──
    const agentProgress = { market_research: 20, competitor_analysis: 40, product_strategy: 60, pitch: 80, scorecard: 100 };
    function setProgress(pct, msg) {
      document.getElementById('progressFill').style.width = pct + '%';
      document.getElementById('progressMsg').textContent = msg;
      document.getElementById('progressPct').textContent = pct + '%';
    }

    // ── THINKING LOG ──
    function addThinkingLine(text, type = 'active') {
      const log = document.getElementById('thinkingLog');
      const icons = { active: '⟳', done: '✓', info: '→' };
      const d = document.createElement('div');
      d.className = `thinking-line ${type}`;
      d.innerHTML = `<span class="tl-icon">${icons[type]||'→'}</span><span>${text}</span><span class="thinking-time">${elapsed()}</span>`;
      log.appendChild(d);
      log.scrollTop = log.scrollHeight;
    }

    function setAgentRunning(id) { document.getElementById(id).className = 's-agent running'; }
    function setAgentDone(id) { document.getElementById(id).className = 's-agent done'; }
    function scoreColor(s, max) { const p=s/max; if(p>=0.75) return '#16a34a'; if(p>=0.55) return '#d97706'; return '#dc2626'; }
    function verdictStyle(verdict) { const vl=(verdict||'').toLowerCase(); if(vl.includes('strong')) return 'background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0'; if(vl.includes('conditional')) return 'background:#fffbeb;color:#d97706;border:1px solid #fde68a'; if(vl.includes('needs')) return 'background:#fef2f2;color:#dc2626;border:1px solid #fecaca'; return 'background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe'; }

    // ── HISTORY ──
    const HISTORY_KEY = 'ventureos_history';
    function loadHistory() { try { const saved = JSON.parse(localStorage.getItem(HISTORY_KEY)||'[]'); if(saved.length>0){document.getElementById('historySection').style.display='block';renderHistory(saved);} } catch(e){} }
    function renderHistory(items) { const list=document.getElementById('historyList'); list.innerHTML=''; items.forEach(item => { const d=document.createElement('div'); d.className='history-item'; d.onclick=()=>loadFromHistory(item); d.innerHTML=`<div class="history-score" style="color:${scoreColor(item.score||0,100)}">${item.score||'—'}</div><div class="history-idea">${item.idea}</div><div class="history-date">${item.date}</div><div class="history-load-btn">Load →</div>`; list.appendChild(d); }); }
    function saveToHistory(idea, score) { try { const saved=JSON.parse(localStorage.getItem(HISTORY_KEY)||'[]'); const filtered=saved.filter(i=>i.idea!==idea); const updated=[{idea,score:score||0,date:new Date().toLocaleDateString('en-US',{month:'short',day:'numeric'})},...filtered].slice(0,3); localStorage.setItem(HISTORY_KEY,JSON.stringify(updated)); document.getElementById('historySection').style.display='block'; renderHistory(updated); } catch(e){} }
    function loadFromHistory(item) {
      const ta=document.getElementById('ideaInput'); ta.value=item.idea;
      document.getElementById('launch').scrollIntoView({behavior:'smooth',block:'start'});
      setTimeout(()=>{ta.focus();ta.style.borderColor='var(--accent)';ta.style.boxShadow='0 0 0 3px rgba(37,99,235,0.15)';setTimeout(()=>{ta.style.borderColor='';ta.style.boxShadow='';},2000);},400);
      showToast('✓ Idea loaded — click Run VentureOS to re-analyze');
    }

    // ── TOAST ──
    function showToast(msg, showCopy = false, copyVal = '') {
      const existing = document.querySelector('.toast');
      if (existing) existing.remove();
      const t = document.createElement('div'); t.className = 'toast';
      t.innerHTML = `<span>${msg}</span>${showCopy ? `<button class="toast-copy" onclick="copyToClipboard('${copyVal}', this)">Copy link</button>` : ''}`;
      document.body.appendChild(t);
      setTimeout(() => t.remove(), showCopy ? 8000 : 3000);
    }
    function copyToClipboard(text, btn) { navigator.clipboard.writeText(text).then(() => { btn.textContent = '✓ Copied!'; }); }

    // ── SHARE REPORT ──
    function shareReport() {
      if (!currentIdea) { alert('Run VentureOS first.'); return; }
      // Encode the idea into a URL param for a shareable link
      const encoded = encodeURIComponent(currentIdea);
      const shareUrl = `${window.location.origin}/report?idea=${encoded}`;
      copyToClipboard(shareUrl, null);
      showToast('🔗 Shareable link copied to clipboard!', false);
    }

    // ── GAMMA INTEGRATION ──
    function openGamma() {
      if (!currentContext.pitch || !currentContext.pitch.deck) { alert('Run VentureOS first to generate the pitch deck.'); return; }
      const deck = currentContext.pitch.deck || [];
      const sc = currentContext.scorecard || {};
      const m = currentContext.market_research || {};

      // Build a rich Gamma prompt from the pitch deck data
      let prompt = `Create a professional investor pitch deck presentation for: "${currentIdea}"\n\n`;
      prompt += `MARKET: ${v(m.market_size)} market, ${v(m.growth_rate)} growth rate\n`;
      prompt += `FUNDABILITY SCORE: ${sc.total || '—'}/100 — ${sc.verdict || ''}\n\n`;
      prompt += `SLIDES:\n`;
      deck.forEach(slide => {
        prompt += `\nSlide ${slide.slide_number}: ${slide.title}\n`;
        if (Array.isArray(slide.key_points)) {
          slide.key_points.forEach(pt => { prompt += `• ${pt}\n`; });
        }
      });
      prompt += `\nSTYLE: Professional, clean, investor-ready. Use data and numbers prominently.`;

      // Copy prompt and open Gamma
      navigator.clipboard.writeText(prompt).then(() => {
        showToast('✓ Pitch deck prompt copied — paste it into Gamma AI!');
        setTimeout(() => { window.open('https://gamma.app/create', '_blank'); }, 800);
      }).catch(() => {
        window.open('https://gamma.app/create', '_blank');
      });
    }

    // ── INVESTOR MATCH ──
    const INVESTORS = [
      { name: 'Y Combinator', stage: 'Pre-seed / Seed', logo: 'ycombinator.com', email: 'apply@ycombinator.com', partner: 'YC Admissions', thesis: 'Any ambitious startup solving a real problem. Especially strong in consumer apps, developer tools, and B2B SaaS.', tags: ['consumer', 'saas', 'developer', 'marketplace', 'fintech'] },
      { name: 'Andreessen Horowitz', stage: 'Seed to Growth', logo: 'a16z.com', email: 'pitch@a16z.com', partner: 'a16z Team', thesis: 'Software eating the world. AI, crypto, consumer, enterprise, bio, fintech at any stage.', tags: ['ai', 'enterprise', 'consumer', 'fintech', 'crypto', 'bio'] },
      { name: 'Sequoia Capital', stage: 'Seed to IPO', logo: 'sequoiacap.com', email: 'pitch@sequoiacap.com', partner: 'Sequoia Team', thesis: 'Legendary companies that become enduring businesses. Strong focus on enterprise, consumer, and healthcare.', tags: ['enterprise', 'consumer', 'healthcare', 'saas', 'marketplace'] },
      { name: 'Accel', stage: 'Seed to Series B', logo: 'accel.com', email: 'info@accel.com', partner: 'Accel Partners', thesis: 'Early-stage technology companies with a particular strength in SaaS, security, and developer-first products.', tags: ['saas', 'security', 'developer', 'enterprise', 'fintech'] },
      { name: 'Khosla Ventures', stage: 'Seed to Series B', logo: 'khoslaventures.com', email: 'contact@khoslaventures.com', partner: 'Vinod Khosla', thesis: 'Moonshot bets on AI, climate, health, and deep tech transforming major industries.', tags: ['ai', 'climate', 'health', 'deeptech', 'robotics'] },
      { name: 'Bessemer Venture', stage: 'Seed to IPO', logo: 'bvp.com', email: 'pitch@bvp.com', partner: 'BVP Team', thesis: 'Cloud-first businesses. Atlas framework for SaaS metrics. Strong in vertical SaaS and consumer.', tags: ['saas', 'cloud', 'consumer', 'healthcare', 'fintech', 'marketplace'] },
      { name: 'First Round Capital', stage: 'Pre-seed / Seed', logo: 'firstround.com', email: 'hello@firstround.com', partner: 'First Round Team', thesis: 'First check into exceptional founders at the earliest stages across all categories.', tags: ['consumer', 'saas', 'marketplace', 'fintech', 'edtech', 'health'] },
      { name: 'Benchmark', stage: 'Series A', logo: 'benchmark.com', email: 'info@benchmark.com', partner: 'Benchmark Partners', thesis: 'High-conviction early-stage bets on extraordinary entrepreneurs. Consumer and marketplace focused.', tags: ['consumer', 'marketplace', 'saas', 'fintech', 'social'] },
    ];

    function matchInvestors(idea, context) {
      const ideaLower = idea.toLowerCase();
      const marketText = JSON.stringify(context.market_research || '').toLowerCase();
      const combined = ideaLower + ' ' + marketText;

      return INVESTORS.map(inv => {
        let score = 0;
        inv.tags.forEach(tag => { if (combined.includes(tag)) score += 20; });
        // Base match so everyone gets at least something
        score = Math.min(95, Math.max(45, score + 40 + Math.floor(Math.random() * 15)));
        return { ...inv, matchScore: score };
      }).sort((a, b) => b.matchScore - a.matchScore).slice(0, 3);
    }

    function renderInvestors(investors) {
      const grid = document.getElementById('investorGrid'); grid.innerHTML = '';
      investors.forEach(inv => {
        const card = document.createElement('div'); card.className = 'investor-card';
        const initials = inv.name.split(' ').map(w => w[0]).join('').slice(0, 2);
        card.innerHTML = `
          <div class="investor-top">
            <div class="investor-logo-fallback" style="background:linear-gradient(135deg,#${Math.floor(Math.random()*0xffffff).toString(16).padStart(6,'0')},#${Math.floor(Math.random()*0xffffff).toString(16).padStart(6,'0')});">${initials}</div>
            <div>
              <div class="investor-name">${inv.name}</div>
              <div class="investor-stage">${inv.stage}</div>
            </div>
          </div>
          <div class="investor-thesis">${inv.thesis}</div>
          <div class="investor-match">
            <div class="match-bar-track"><div class="match-bar-fill" style="width:${inv.matchScore}%;background:${inv.matchScore>=75?'var(--green)':inv.matchScore>=60?'var(--amber)':'var(--accent)'}"></div></div>
            <div class="match-pct" style="color:${inv.matchScore>=75?'var(--green)':inv.matchScore>=60?'var(--amber)':'var(--accent)'}">${inv.matchScore}% match</div>
          </div>
          <div style="font-size:11px;color:var(--text-3);margin-bottom:10px;display:flex;align-items:center;gap:5px;">
            <span>📧</span> <span style="font-family:monospace;">${inv.email}</span>
          </div>
          <button class="investor-email-btn" onclick="draftInvestorEmail('${inv.name}', '${inv.stage}', '${inv.email}', '${inv.partner}')">✉️ Open email to ${inv.name.split(' ')[0]}</button>`;
        grid.appendChild(card);

        // Try to load Clearbit logo
        const img = new Image();
        img.onload = () => {
          const fallback = card.querySelector('.investor-logo-fallback');
          if (fallback) {
            const wrap = document.createElement('div'); wrap.className = 'investor-logo-wrap';
            const logo = document.createElement('img'); logo.className = 'investor-logo'; logo.src = img.src; logo.alt = inv.name;
            wrap.appendChild(logo);
            fallback.replaceWith(wrap);
          }
        };
        img.src = `https://logo.clearbit.com/${inv.logo}`;
      });
    }

    // ── WEBSITE BUILDER ──
    function selectStyle(seed) { selectedSeed = seed; document.querySelectorAll('.style-chip').forEach(c => c.classList.remove('active')); const chip = document.querySelector(`[data-seed="${seed}"]`); if (chip) chip.classList.add('active'); }
    const viewportSizes = { desktop:{width:'100%',height:'720px',label:'1080 × 720'}, tablet:{width:'768px',height:'680px',label:'768 × 680'}, mobile:{width:'390px',height:'680px',label:'390 × 680'} };
    function setViewport(vp) { const config=viewportSizes[vp]; document.getElementById('browserOuter').style.width=config.width; document.getElementById('browserOuter').style.margin=vp==='desktop'?'0':'0 auto'; document.getElementById('protoIframe').style.height=config.height; document.getElementById('viLabel').textContent=config.label; ['viDesktop','viTablet','viMobile'].forEach(id=>document.getElementById(id).classList.remove('active')); document.getElementById(`vi${vp.charAt(0).toUpperCase()+vp.slice(1)}`).classList.add('active'); }

    async function generatePrototype() {
      if (!currentIdea) { alert('Run VentureOS first.'); return; }
      const btn = document.getElementById('protoBtn'); btn.disabled = true; document.getElementById('protoBtnTxt').textContent = 'Building...';
      document.getElementById('protoLoading').style.display = 'block';
      document.getElementById('protoWrapper').style.display = 'none';
      document.getElementById('protoError').style.display = 'none';
      document.getElementById('protoThemeBadge').style.display = 'none';
      let seed = selectedSeed === -1 ? Math.floor(Math.random() * 5) : selectedSeed;
      try {
        const res = await fetch('/prototype', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({idea:currentIdea, product_strategy:currentProductStrategy, context:currentContext, seed}) });
        const data = await res.json();
        if (data.error) { document.getElementById('protoError').textContent = '❌ ' + data.error; document.getElementById('protoError').style.display = 'block'; return; }
        protoHtml = data.html; const themeName = data.theme || 'Custom'; protoGenCount++;
        document.getElementById('protoIframe').srcdoc = protoHtml;
        const siteSlug = currentIdea.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,28) || 'venture-site';
        document.getElementById('browserTabTitle').textContent = currentIdea.length > 30 ? currentIdea.slice(0, 30) + '…' : currentIdea;
        document.getElementById('browserUrl').textContent = `ventureos.app/${siteSlug}`;
        document.getElementById('protoFooterTheme').textContent = `Theme: ${themeName}`;
        document.getElementById('protoFooterInfo').textContent = `Generation #${protoGenCount} · Live responsive website preview`;
        const badge = document.getElementById('protoThemeBadge'); badge.textContent = `Theme · ${themeName}`; badge.style.display = 'inline-block';
        document.getElementById('protoWrapper').style.display = 'block';
        setTimeout(() => document.getElementById('protoSection').scrollIntoView({ behavior:'smooth', block:'start' }), 300);
      } catch(err) { document.getElementById('protoError').textContent = '❌ ' + err.message; document.getElementById('protoError').style.display = 'block'; }
      finally { document.getElementById('protoLoading').style.display = 'none'; btn.disabled = false; document.getElementById('protoBtnTxt').textContent = '⚡ Regenerate Website'; }
    }

    function openFullscreen() { if (!protoHtml) return; const w = window.open('', '_blank'); w.document.open(); w.document.write(protoHtml); w.document.close(); }

    // ── FINANCIALS ──
    function calcFinancials() {
      const su=parseFloat(document.getElementById('fin_users').value)||100; const gp=parseFloat(document.getElementById('fin_growth').value)/100||0.15; const arpu=parseFloat(document.getElementById('fin_arpu').value)||20; const fc=(parseFloat(document.getElementById('fin_cogs').value)||2000)+(parseFloat(document.getElementById('fin_opex').value)||5000);
      const rows=[]; let users=su,cumPL=0,bem=null;
      for(let m=1;m<=36;m++){const rev=users*arpu,costs=fc,profit=rev-costs;cumPL+=profit;if(bem===null&&profit>=0)bem=m;rows.push({month:m,users:Math.round(users),revenue:rev,costs,profit,cumPL});users=users*(1+gp);}
      finData=rows;
      const y3=rows[35];
      document.getElementById('fin_y3rev').textContent=fmtK(y3.revenue*12);
      document.getElementById('fin_y3users').textContent=y3.users.toLocaleString();
      document.getElementById('fin_breakeven').textContent=bem?`Month ${bem}`:'Not reached';
      document.getElementById('fin_cumrev').textContent=fmtK(rows.reduce((s,r)=>s+r.revenue,0));
      const tbody=document.getElementById('finTableBody'); tbody.innerHTML='';
      for(let yr=1;yr<=3;yr++){const sm=(yr-1)*12;[1,3,6,9,12].map(m=>rows[sm+m-1]).forEach(r=>{const tr=document.createElement('tr');if(r.month%12===0)tr.className='highlight';tr.innerHTML=`<td class="year-col">${r.month%12===0?`Year ${yr} End`:`Month ${r.month}`}</td><td>${r.users.toLocaleString()}</td><td>${fmt(r.revenue)}</td><td>${fmt(r.costs)}</td><td class="${r.profit>=0?'pos':'neg'}">${fmt(r.profit)}</td><td class="${r.cumPL>=0?'pos':'neg'}">${fmt(r.cumPL)}</td>`;tbody.appendChild(tr);});}
    }
    function downloadCSV() { if(!finData.length){alert('Run VentureOS first.');return;} const h=['Month','Users','Monthly Revenue','Monthly Costs','Monthly Profit','Cumulative P&L']; const rows=finData.map(r=>[r.month,r.users,r.revenue.toFixed(2),r.costs.toFixed(2),r.profit.toFixed(2),r.cumPL.toFixed(2)]); const csv=[h,...rows].map(r=>r.join(',')).join('\n'); const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([`VentureOS Financial Model\nIdea: ${currentIdea}\n\n`+csv],{type:'text/csv'}));a.download='ventureos_financial_model.csv';a.click(); }

    // ── EXPORT ──
    function exportPDF() { document.querySelectorAll('.rcard-body').forEach(b=>b.classList.add('open')); document.querySelectorAll('.rcard-hd').forEach(h=>h.classList.add('open')); const t=document.title; document.title=`VentureOS — ${currentIdea.slice(0,50)}`; window.print(); setTimeout(()=>{document.title=t;},1000); }
    function copyReport() { if(!reportText){alert('Run VentureOS first.');return;} navigator.clipboard.writeText(reportText).then(()=>{const btn=document.getElementById('copyBtn');btn.textContent='✓ Copied!';setTimeout(()=>btn.textContent='📋 Copy text',2000);}); }
    function buildReportText(ctx,idea) { const m=ctx.market_research||{},sc=ctx.scorecard||{}; return ['VentureOS Analysis Report',`Idea: ${idea}`,`Generated: ${new Date().toLocaleDateString()}`,'','MARKET',`TAM: ${v(m.market_size)} | Growth: ${v(m.growth_rate)}`,`Customer: ${v(m.target_customer)}`,'','SCORECARD',`Score: ${sc.total||'—'}/100 — ${sc.verdict||''}`,`Strength: ${v(sc.biggest_strength)}`,`Risk: ${v(sc.biggest_risk)}`,'','VentureOS · Google Build with AI Hackathon 2026'].join('\n'); }

    // ── PIVOT ──
    async function generatePivots() {
      if(!currentIdea){alert('Run VentureOS first.');return;}
      const btn=document.getElementById('pivotBtn'); btn.disabled=true; document.getElementById('pivotBtnTxt').textContent='Analyzing...';
      document.getElementById('pivotLoading').style.display='block'; document.getElementById('pivotResults').style.display='none'; document.getElementById('pivotError').style.display='none';
      try {
        const res=await fetch('/pivot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idea:currentIdea,context:currentContext})});
        const data=await res.json();
        if(data.error){document.getElementById('pivotError').textContent='❌ '+data.error;document.getElementById('pivotError').style.display='block';return;}
        renderPivots(data); document.getElementById('pivotResults').style.display='block';
      } catch(err){document.getElementById('pivotError').textContent='❌ '+err.message;document.getElementById('pivotError').style.display='block';}
      finally{document.getElementById('pivotLoading').style.display='none';btn.disabled=false;document.getElementById('pivotBtnTxt').textContent='🔄 Regenerate';}
    }
    function renderPivots(data) {
      const container=document.getElementById('pivotResults'); container.innerHTML='';
      const pivots=data.pivots||[]; const rec=data.recommendation||'';
      if(rec){container.innerHTML=`<div class="pivot-recommendation"><div class="pivot-rec-icon">💡</div><div><div class="pivot-rec-label">AI Recommendation</div><div class="pivot-rec-text">${rec}</div></div></div>`;}
      const grid=document.createElement('div'); grid.className='pivot-cards';
      pivots.forEach(pivot=>{
        const isRec=rec.toLowerCase().includes((pivot.title||'').toLowerCase().split(' ')[0]);
        const dc={Easy:'diff-easy',Medium:'diff-medium',Hard:'diff-hard'}[pivot.difficulty]||'';
        const pc={'Very High':'pot-vh',High:'pot-h'}[pivot.potential]||'';
        const card=document.createElement('div'); card.className=`pivot-card${isRec?' recommended':''}`;
        card.innerHTML=`<div class="pivot-card-title">${v(pivot.title)}</div><div class="pivot-card-desc">${v(pivot.description)}</div><div class="pivot-card-tags"><span class="pivot-tag ${dc}">⚡ ${v(pivot.difficulty)}</span><span class="pivot-tag ${pc}">📈 ${v(pivot.potential)}</span></div><div class="pivot-detail"><strong>Target:</strong> ${v(pivot.target_customer)}</div><div class="pivot-detail"><strong>Revenue:</strong> ${v(pivot.revenue_model)}</div><div class="pivot-detail"><strong>Why:</strong> ${v(pivot.why)}</div>${pivot.example?`<div class="pivot-example">📌 ${pivot.example}</div>`:''}`;
        grid.appendChild(card);
      });
      container.appendChild(grid);
    }

    // ── ANALYZE ──
    async function analyze() {
      const idea = document.getElementById('ideaInput').value.trim();
      if (!idea) { alert('Please enter your startup idea.'); return; }
      currentIdea=idea; currentContext={}; currentProductStrategy={}; chatHistory=[]; reportText=''; finData=[]; protoGenCount=0;
      analysisStartTime = Date.now(); agentStartTime = Date.now();

      const btn=document.getElementById('runBtn'); btn.disabled=true; document.getElementById('btnTxt').textContent='Agents running...';
      document.getElementById('errBox').style.display='none';
      document.getElementById('thinkingLog').innerHTML = '';

      const results=document.getElementById('results'); results.innerHTML=''; results.style.cssText='max-width:1080px;margin:0 auto;padding:56px 32px 40px;';
      ['protoSection','chatSection','exportBar','finSection','pivotSection','investorSection'].forEach(id=>document.getElementById(id).style.display='none');
      document.getElementById('protoWrapper').style.display='none';
      document.getElementById('pivotResults').style.display='none';
      document.getElementById('chatMessages').innerHTML=`<div class="chat-msg ai"><div class="chat-avatar ai">V</div><div class="chat-bubble">I've analyzed your idea. Ask me anything!</div></div>`;

      document.getElementById('progressBar').style.display = 'block';
      document.getElementById('streamStatus').style.display='block';
      ['sa1','sa2','sa3','sa4','sa5'].forEach(id=>document.getElementById(id).className='s-agent');
      setProgress(0, 'Starting agents...');

      results.innerHTML=`<div class="res-hd"><div class="res-hd-left"><div class="res-title">Your go-to-market foundation</div><div class="res-sub">Results appear as each agent completes.</div></div><button class="share-btn" onclick="shareReport()">🔗 Share this analysis</button></div>`;
      setTimeout(()=>results.scrollIntoView({behavior:'smooth',block:'start'}),100);

      try {
        const response=await fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idea})});
        const reader=response.body.getReader(); const decoder=new TextDecoder(); let buffer='';
        while(true){const{done,value}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});const lines=buffer.split('\n');buffer=lines.pop();for(const line of lines){if(!line.startsWith('data: '))continue;try{handleStreamEvent(JSON.parse(line.slice(6)),results);}catch(e){}}}
      }catch(err){document.getElementById('errBox').textContent='❌ '+err.message;document.getElementById('errBox').style.display='block';}
      finally{document.getElementById('streamStatus').style.display='none';document.getElementById('progressBar').style.display='none';btn.disabled=false;document.getElementById('btnTxt').textContent='Run VentureOS';}
    }

    function handleStreamEvent(payload, container) {
      const{event,data,message}=payload;

      if(event==='status'){
        agentStartTime = Date.now();
        if(message.includes('Market')){setAgentRunning('sa1');setProgress(5,'📊 Market Research agent running...');addThinkingLine('Market Research agent started', 'active');}
        if(message.includes('Competitor')){setAgentDone('sa1');setAgentRunning('sa2');setProgress(22,'🔍 Competitor Analysis agent running...');addThinkingLine('Market Research complete ✓','done');addThinkingLine('Competitor Analysis agent started','active');}
        if(message.includes('Product')){setAgentDone('sa2');setAgentRunning('sa3');setProgress(42,'🛠️ Product Strategy agent running...');addThinkingLine('Competitor Analysis complete ✓','done');addThinkingLine('Product Strategy agent started','active');}
        if(message.includes('Pitch')){setAgentDone('sa3');setAgentRunning('sa4');setProgress(62,'📈 Pitch agent running...');addThinkingLine('Product Strategy complete ✓','done');addThinkingLine('Pitch + Emails + Domains agent started','active');}
        if(message.includes('Scorecard')||message.includes('Fundability')){setAgentDone('sa4');setAgentRunning('sa5');setProgress(82,'🎯 Fundability Scorecard agent running...');addThinkingLine('Pitch agent complete ✓','done');addThinkingLine('Fundability Scorecard agent started','active');}
        return;
      }

      if(event==='done'){
        setAgentDone('sa5'); setProgress(100, 'All agents complete ✓');
        addThinkingLine('Fundability Scorecard complete ✓', 'done');
        const totalTime = ((Date.now() - analysisStartTime) / 1000).toFixed(1);
        addThinkingLine(`Analysis complete in ${totalTime}s 🎉`, 'done');

        reportText=buildReportText(currentContext,currentIdea);
        saveToHistory(currentIdea,(currentContext.scorecard||{}).total||0);

        // Render investor matches
        const matched = matchInvestors(currentIdea, currentContext);
        renderInvestors(matched);
        document.getElementById('investorSection').style.display = 'block';

        document.getElementById('finSection').style.display='block';
        document.getElementById('pivotSection').style.display='block';
        document.getElementById('protoSection').style.display='block';
        calcFinancials();
        setTimeout(()=>{document.getElementById('chatSection').style.display='block';setTimeout(()=>{document.getElementById('exportBar').style.display='block';},300);},600);
        return;
      }

      if(event==='error'){document.getElementById('errBox').textContent='❌ '+message;document.getElementById('errBox').style.display='block';return;}

      if(event==='market_research') currentContext.market_research=data;
      if(event==='competitor_analysis') currentContext.competitor_analysis=data;
      if(event==='product_strategy'){currentContext.product_strategy=data;currentProductStrategy=data;}
      if(event==='pitch') currentContext.pitch=data;
      if(event==='scorecard') currentContext.scorecard=data;

      if(event==='market_research'){
        const m=data||{}; const trends=Array.isArray(m.market_trends)?m.market_trends:[];
        addThinkingLine(`Market: ${v(m.market_size)} TAM, ${v(m.growth_rate)} growth`, 'info');
        container.appendChild(mkCard('📊','Market Research',`
          <div class="kv-row"><div class="kv"><div class="kv-lbl">Market Size (TAM)</div><div class="kv-val">${v(m.market_size)}</div></div><div class="kv"><div class="kv-lbl">Growth Rate</div><div class="kv-val">${v(m.growth_rate)}</div></div></div>
          <div class="fld"><div class="fld-lbl">Target Customer</div><div class="fld-val">${v(m.target_customer)}</div></div>
          <div class="fld"><div class="fld-lbl">Core Pain Point</div><div class="fld-val">${v(m.pain_point)}</div></div>
          <div class="fld"><div class="fld-lbl">Market Trends</div><ul class="trends">${trends.map(t=>`<li class="trend-li">${t}</li>`).join('')}</ul></div>
          <div class="info-box">${v(m.opportunity_summary)}</div>`));
      }

      if(event==='competitor_analysis'){
        const c=data||{}; const comps=Array.isArray(c.competitors)?c.competitors:[];
        addThinkingLine(`Found ${comps.length} competitors — whitespace identified`, 'info');
        const compCards = comps.map(co => {
          const domain = co.name.toLowerCase().replace(/\s+/g,'') + '.com';
          return `<div class="comp">
            <div class="comp-header">
              <img class="comp-logo" src="https://logo.clearbit.com/${domain}" alt="${co.name}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
              <div class="comp-logo-fallback" style="display:none">${co.name.charAt(0)}</div>
              <div>
                <div class="comp-name">${v(co.name)}</div>
                <div class="comp-fund">${v(co.funding)}</div>
              </div>
            </div>
            <div class="comp-desc">${v(co.description)}</div>
            <div class="comp-weak">⚠ ${v(co.weakness)}</div>
            <div class="comp-edge">✓ ${v(co.our_advantage)}</div>
          </div>`;
        }).join('');
        container.appendChild(mkCard('🔍','Competitor Analysis',`
          <div class="comp-grid">${compCards}</div>
          <div class="info-box">${v(c.whitespace)}</div>
          <div class="data-source-badge">🔍 Sourced from web + AI analysis</div>`));
      }

      if(event==='product_strategy'){
        const p=data||{};const feats=Array.isArray(p.mvp_features)?p.mvp_features:[];const stk=Array.isArray(p.suggested_stack)?p.suggested_stack:[];const tl=Array.isArray(p.build_timeline)?p.build_timeline:[];const mono=Array.isArray(p.monetization)?p.monetization:[];const bm={Must:'b-must',Should:'b-should',Could:'b-could',"Won't":'b-wont'};
        addThinkingLine(`Product: ${feats.length} features prioritized, ${stk.length} stack recommendations`, 'info');
        container.appendChild(mkCard('🛠️','Product Strategy',`
          <div class="sub-lbl">MVP Features</div><div class="feat-rows">${feats.map(f=>`<div class="feat-row"><span class="badge ${bm[f.priority]||'b-could'}">${v(f.priority)}</span><div><div class="feat-name">${v(f.feature)}</div><div class="feat-why">${v(f.reason)}</div></div></div>`).join('')}</div>
          <div class="sub-lbl">Stack</div><div class="stack-g">${stk.map(s=>`<div class="stack-c"><div class="stack-n">${v(s.tool)}</div><div class="stack-r">${v(s.reason)}</div></div>`).join('')}</div>
          <div class="sub-lbl">Timeline</div><div class="tl">${tl.map(t=>`<div class="trow"><div class="trow-w">${v(t.week)}</div><div class="trow-m">${v(t.milestone)}</div></div>`).join('')}</div>
          <div class="sub-lbl">Monetization</div><div class="mono-g">${mono.map(mn=>`<div class="mono-c"><div class="mono-n">${v(mn.model)}</div>${(Array.isArray(mn.pros)?mn.pros:[]).map(pr=>`<div class="mono-p">✓ ${pr}</div>`).join('')}${(Array.isArray(mn.cons)?mn.cons:[]).map(cn=>`<div class="mono-con">✗ ${cn}</div>`).join('')}</div>`).join('')}</div>`));
      }

      if(event==='pitch'){
        const pitch=data||{};const deck=pitch.deck||[],emails=pitch.emails||[],domains=pitch.domains||[];
        addThinkingLine(`Pitch: ${deck.length} slides, ${emails.length} investor emails, ${domains.length} domains`, 'info');
        if(deck.length) container.appendChild(mkCard('📈','Pitch Deck',`
          <div class="slide-list">${deck.map(s=>`<div class="slide"><div class="slide-hd"><div class="slide-n">${s.slide_number}</div><div class="slide-t">${v(s.title)}</div></div><ul class="slide-pts">${(Array.isArray(s.key_points)?s.key_points:[]).map(pt=>`<li class="slide-pt">${pt}</li>`).join('')}</ul></div>`).join('')}</div>
          <button class="slides-btn" onclick="openSlideModal()">✨ Generate Premium Deck</button>`));
        if(emails.length) container.appendChild(mkCard('💌','Cold Investor Emails',`<div class="email-list">${emails.map(e=>`<div class="email"><div class="email-meta"><span class="email-type">${v(e.investor_type)}</span><span class="email-subj">Subject: <span>${v(e.subject_line)}</span></span></div><div class="email-body">${v(e.body)}</div></div>`).join('')}</div>`));
        if(domains.length) container.appendChild(mkCard('🌐','Domain Suggestions',`<div class="domain-chips">${domains.map(d=>`<div class="domain-chip">${d}</div>`).join('')}</div>`));
      }

      if(event==='scorecard'){
        const sc=data||{};const scores=Array.isArray(sc.scores)?sc.scores:[];const total=sc.total||0;const verdict=sc.verdict||'Pass';const color=scoreColor(total,100);const verdBadge=`<span class="rcard-badge" style="${verdictStyle(verdict)}">${verdict}</span>`;
        addThinkingLine(`Fundability Score: ${total}/100 — ${verdict}`, 'info');
        const card=mkCard('🎯','Fundability Scorecard',`
          <div class="scorecard-hero"><div class="score-circle" style="border-color:${color};"><div class="score-num" style="color:${color};">${total}</div><div class="score-denom">out of 100</div></div><div class="scorecard-meta"><span class="verdict-badge" style="${verdictStyle(verdict)}">${verdict}</span><div class="scorecard-summary">${v(sc.summary)}</div></div></div>
          <div class="scorecard-hl"><div class="hl-box" style="background:var(--green-light);border:1px solid #bbf7d0;"><div class="hl-lbl" style="color:var(--green);">💪 Strength</div><div class="hl-val">${v(sc.biggest_strength)}</div></div><div class="hl-box" style="background:var(--red-light);border:1px solid #fecaca;"><div class="hl-lbl" style="color:var(--red);">⚠ Risk</div><div class="hl-val">${v(sc.biggest_risk)}</div></div></div>
          <div class="sub-lbl">Dimension Breakdown</div>
          <div class="score-bars">${scores.map(s=>{const pct=Math.round((s.score/20)*100);const col=scoreColor(s.score,20);return`<div class="score-bar-row"><div class="score-bar-top"><span class="score-bar-dim">${s.dimension}</span><span class="score-bar-val" style="color:${col}">${s.score}/20</span></div><div class="score-bar-track"><div class="score-bar-fill" style="width:0%;background:${col};" data-width="${pct}%"></div></div><div class="score-bar-reason">${v(s.reason)}</div></div>`;}).join('')}</div>`,verdBadge);
        container.appendChild(card);
        requestAnimationFrame(()=>{setTimeout(()=>{card.querySelectorAll('.score-bar-fill').forEach(bar=>{bar.style.width=bar.dataset.width;});},150);});
      }
    }

    // ── CHAT ──
    function handleChatKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendChat();}}
    function sendQuickPrompt(btn){document.getElementById('chatInput').value=btn.textContent;sendChat();}
    async function sendChat(){const input=document.getElementById('chatInput');const msg=input.value.trim();if(!msg||!currentIdea)return;const sendBtn=document.getElementById('chatSendBtn');sendBtn.disabled=true;input.value='';appendChatMsg('user',msg);chatHistory.push({role:'user',content:msg});const typingEl=appendTyping();try{const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idea:currentIdea,context:currentContext,messages:chatHistory.slice(0,-1),user_message:msg})});const data=await res.json();typingEl.remove();if(data.error){appendChatMsg('ai','❌ '+data.error);return;}chatHistory.push({role:'assistant',content:data.reply});appendChatMsg('ai',data.reply);}catch(err){typingEl.remove();appendChatMsg('ai','❌ '+err.message);}finally{sendBtn.disabled=false;input.focus();}}
    function appendChatMsg(role,text){const msgs=document.getElementById('chatMessages');const isAI=role==='ai';const d=document.createElement('div');d.className=`chat-msg ${isAI?'ai':'user'}`;d.innerHTML=`<div class="chat-avatar ${isAI?'ai':'user-av'}">${isAI?'V':'U'}</div><div class="chat-bubble">${text.replace(/\n/g,'<br>')}</div>`;msgs.appendChild(d);msgs.scrollTop=msgs.scrollHeight;return d;}
    function appendTyping(){const msgs=document.getElementById('chatMessages');const d=document.createElement('div');d.className='chat-msg ai';d.innerHTML=`<div class="chat-avatar ai">V</div><div class="chat-bubble"><div class="chat-typing"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div>`;msgs.appendChild(d);msgs.scrollTop=msgs.scrollHeight;return d;}

    // ── IN-PAGE SLIDE DECK GENERATOR ──
    let currentSlideIndex = 0;
    let totalSlides = 0;
    let slidesGenerated = false;
    let isPresenting = false;
    let currentDeckTemplateId = '';
    let currentDeckData = { title: 'Pitch Deck', subtitle: '', meta: null, slides: [] };
    let currentDeckImageStyle = 'deck-illustration';
    let currentDeckImageCoverage = 'hero-only';
    let currentDeckImageModel = 'lcm-dreamshaper-v7';
    let currentDeckImageGeneration = null;
    let currentDeckVisualRefreshKey = 0;
    const FALLBACK_IMAGE_STYLE_OPTIONS = [
      { key: 'auto', label: 'Storyboard' },
      { key: 'deck-illustration', label: 'Presentation Illustration' },
      { key: 'animated-scene', label: 'Animated Scene' },
      { key: 'illustration', label: 'Editorial Illustration' },
      { key: 'cartoon', label: 'Cartoon' },
      { key: 'product-mockup', label: 'Product Illustration' },
      { key: '3d-render', label: '3D Illustration' },
      { key: 'abstract', label: 'Abstract Scenic' }
    ];
    const FALLBACK_IMAGE_COVERAGE_OPTIONS = [
      { key: 'hero-only', label: 'Hero Only (Fast)' },
      { key: 'key-slides', label: 'Key Slides' },
      { key: 'image-heavy', label: 'Image Heavy' },
      { key: 'all', label: 'Every Slide' }
    ];
    const FALLBACK_IMAGE_MODELS = [
      { key: 'lcm-dreamshaper-v7', label: 'LCM Dreamshaper v7' },
      { key: 'dreamshaper-8-lcm', label: 'DreamShaper 8 LCM' },
      { key: 'dreamshaper-8', label: 'DreamShaper 8 (Slow HQ)' },
      { key: 'tiny-sd', label: 'Fast' },
      { key: 'sd15', label: 'Stable Diffusion 1.5' }
    ];
    const DECK_TEMPLATE_PRESETS = [
      {
        template_id: 'editorial-midnight',
        theme_name: 'Scholar Noir',
        structureVariant: 'split-panel',
        palette: { primary: '#23262F', secondary: '#2E313B', accent: '#F4728A', surface: '#333745', text: '#F7EEF4' },
        style_notes: [
          'Dark academic-editorial canvas with rose-coral accent discipline',
          'Split-layout storytelling with contextual illustration or chart panel',
          'Feels like a premium research deck or polished conference talk'
        ]
      },
      {
        template_id: 'boardroom-ivory',
        theme_name: 'Boardroom Ivory',
        structureVariant: 'consulting-grid',
        palette: { primary: '#F6F2EA', secondary: '#E9E3D8', accent: '#1D4ED8', surface: '#FFFFFF', text: '#111827' },
        style_notes: [
          'Consulting-style light canvas with precise alignment',
          'Minimal borders, disciplined spacing, executive clarity',
          'Feels like a premium strategy memo turned into slides'
        ]
      },
      {
        template_id: 'kinetic-ember',
        theme_name: 'Kinetic Ember',
        structureVariant: 'full-bleed-hero',
        palette: { primary: '#111827', secondary: '#1F2937', accent: '#F97316', surface: '#18212F', text: '#FFF7ED' },
        style_notes: [
          'Dark executive canvas with warmer highlight energy',
          'Bold accents reserved for proof points and movement cues',
          'Feels more keynote-driven and launch-oriented'
        ]
      },
      {
        template_id: 'atlas-sapphire',
        theme_name: 'Atlas Sapphire',
        structureVariant: 'data-dashboard',
        palette: { primary: '#081A3A', secondary: '#0F274F', accent: '#60A5FA', surface: '#0E2243', text: '#EFF6FF' },
        style_notes: [
          'High-contrast cobalt system for data-heavy investor stories',
          'Sharp hierarchy with crisp metric framing',
          'Feels analytical, premium, and globally scalable'
        ]
      },
      {
        template_id: 'monochrome-luxe',
        theme_name: 'Monochrome Luxe',
        structureVariant: 'centered-editorial',
        palette: { primary: '#111111', secondary: '#1E1E1E', accent: '#D4B483', surface: '#202020', text: '#F5F5F4' },
        style_notes: [
          'Luxury monochrome composition with warm metallic accent',
          'Large type, sparse copy, elevated investor-brand mood',
          'Feels premium, polished, and slightly fashion-editorial'
        ]
      }
    ];

    function escapeHtml(value) {
      return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function escapeAttr(value) {
      return escapeHtml(value).replace(/`/g, '&#96;');
    }

    function cleanText(value, fallback = '') {
      const text = String(value ?? '').trim();
      return text || fallback;
    }

    function cleanList(value, limit = 5) {
      if (!Array.isArray(value)) return [];
      return value.map(item => cleanText(item)).filter(Boolean).slice(0, limit);
    }

    function normalizeHex(value, fallback) {
      const hex = cleanText(value, fallback).replace('#', '');
      return /^[0-9a-fA-F]{6}$/.test(hex) ? `#${hex.toUpperCase()}` : fallback;
    }

    function hexToRgbString(hex, fallback = '125, 211, 252') {
      const clean = cleanText(hex).replace('#', '');
      if (!/^[0-9a-fA-F]{6}$/.test(clean)) return fallback;
      const num = Number.parseInt(clean, 16);
      return `${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}`;
    }

    function getContrastingText(hex) {
      const clean = cleanText(hex).replace('#', '');
      if (!/^[0-9a-fA-F]{6}$/.test(clean)) return '#0F172A';
      const num = Number.parseInt(clean, 16);
      const r = (num >> 16) & 255;
      const g = (num >> 8) & 255;
      const b = num & 255;
      const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
      return luminance > 0.56 ? '#0F172A' : '#F8FAFC';
    }

    function defaultLayoutForType(type, index) {
      const normalized = cleanText(type).toLowerCase();
      if (['hook', 'opening', 'title', 'cover'].includes(normalized)) return 'cover';
      if (['market', 'impact', 'proof', 'data', 'traction'].includes(normalized)) return 'metrics';
      if (['how_it_works', 'business_model', 'process', 'roadmap'].includes(normalized)) return 'roadmap';
      if (['vision', 'future', 'call_to_action', 'cta', 'ask'].includes(normalized)) return 'closing';
      if (['competition', 'competitive_landscape'].includes(normalized)) return 'comparison';
      return index === 0 ? 'cover' : 'spotlight';
    }

    function normalizeStats(slide) {
      if (Array.isArray(slide?.stats)) {
        return slide.stats
          .map(item => ({
            value: cleanText(item?.value ?? item?.num),
            label: cleanText(item?.label)
          }))
          .filter(item => item.value || item.label)
          .slice(0, 3);
      }

      return [
        { value: cleanText(slide?.stat1_num), label: cleanText(slide?.stat1_label) },
        { value: cleanText(slide?.stat2_num), label: cleanText(slide?.stat2_label) },
        { value: cleanText(slide?.stat3_num), label: cleanText(slide?.stat3_label) }
      ].filter(item => item.value || item.label);
    }

    function normalizeAnimationPlan(plan, slide = {}) {
      const sequence = cleanList(plan?.sequence ?? slide?.sequence, 4);
      return {
        entry: cleanText(plan?.entry ?? slide?.entry, 'Fade'),
        sequence: sequence.length ? sequence : ['Title', 'Core message', 'Supporting proof'],
        transition: cleanText(plan?.transition, 'Smooth fade'),
        emphasis: cleanText(plan?.emphasis)
      };
    }

    function normalizeSlide(slide, index) {
      const type = cleanText(slide?.type ?? slide?.slide_type, 'story').toLowerCase();
      return {
        slide_number: slide?.slide_number ?? index + 1,
        type,
        layout: cleanText(slide?.layout, defaultLayoutForType(type, index)).toLowerCase(),
        title: cleanText(slide?.title ?? slide?.headline ?? slide?.slide_title, `Slide ${index + 1}`),
        subtitle: cleanText(slide?.subtitle ?? slide?.subheadline),
        objective: cleanText(slide?.objective),
        content: cleanList(slide?.content ?? slide?.points ?? slide?.key_points, 5),
        stats: normalizeStats(slide),
        visual_suggestion: cleanText(slide?.visual_suggestion ?? slide?.visual ?? slide?.chart_suggestion),
        image_url: cleanText(slide?.image_url ?? slide?.visual_image_url),
        image_prompt: cleanText(slide?.image_prompt),
        image_model: cleanText(slide?.image_model),
        image_repo_id: cleanText(slide?.image_repo_id),
        image_status: cleanText(slide?.image_status),
        image_error: cleanText(slide?.image_error),
        design_notes: cleanText(slide?.design_notes),
        animation_plan: normalizeAnimationPlan(slide?.animation_plan, slide)
      };
    }

    function normalizeDeckPayload(payload) {
      const source = Array.isArray(payload) ? { slides: payload } : (payload || {});
      const design = source.design_system || {};
      const preset = getTemplatePreset(design.template_id || currentDeckTemplateId || DECK_TEMPLATE_PRESETS[0].template_id);
      const palette = { ...(preset.palette || {}), ...(design.palette || {}) };
      const slides = Array.isArray(source.slides) ? source.slides : (Array.isArray(source.deck) ? source.deck : []);

      return {
        title: cleanText(source.presentation_title, currentIdea || 'Pitch Deck'),
        subtitle: cleanText(source.presentation_subtitle, 'Investor-grade narrative presentation'),
        meta: {
          template_id: preset.template_id,
          theme_name: cleanText(design.theme_name, preset.theme_name),
          palette: {
            primary: normalizeHex(palette.primary, preset.palette.primary),
            secondary: normalizeHex(palette.secondary, preset.palette.secondary),
            accent: normalizeHex(palette.accent, preset.palette.accent),
            surface: normalizeHex(palette.surface, preset.palette.surface),
            text: normalizeHex(palette.text, preset.palette.text)
          },
          style_notes: cleanList(design.style_notes, 3).length ? cleanList(design.style_notes, 3) : cleanList(preset.style_notes, 3)
        },
        slides: slides.map((item, index) => normalizeSlide(item, index)),
        image_generation: source.image_generation || null,
        generation_mode: cleanText(source.generation_mode),
        generation_notice: cleanText(source.generation_notice),
        generation_error: cleanText(source.generation_error)
      };
    }

    function entryKey(value) {
      const key = cleanText(value).toLowerCase();
      if (key.includes('zoom')) return 'zoom';
      if (key.includes('slide')) return 'slide';
      return 'fade';
    }

    function transitionKey(value) {
      const key = cleanText(value).toLowerCase();
      if (key.includes('zoom')) return 'zoom';
      if (key.includes('push') || key.includes('slide')) return 'slide';
      return 'fade';
    }

    function slideTypeLabel(type) {
      return cleanText(type, 'story').replace(/_/g, ' ').toUpperCase();
    }

    function slideThemeStyle(meta) {
      const palette = meta?.palette || {};
      return [
        `--deck-primary:${palette.primary || '#0B1020'}`,
        `--deck-secondary:${palette.secondary || '#182033'}`,
        `--deck-surface:${palette.surface || '#121A2B'}`,
        `--deck-text:${palette.text || '#F8FAFC'}`,
        `--deck-accent:${palette.accent || '#7DD3FC'}`,
        `--deck-accent-rgb:${hexToRgbString(palette.accent || '#7DD3FC')}`
      ].join(';');
    }

    function getTemplatePreset(templateId) {
      return DECK_TEMPLATE_PRESETS.find(preset => preset.template_id === templateId) || DECK_TEMPLATE_PRESETS[0];
    }

    function pickNextTemplateId(forceDifferent = false) {
      const presets = DECK_TEMPLATE_PRESETS;
      if (!presets.length) return '';
      if (!currentDeckTemplateId) return presets[0].template_id;
      if (!forceDifferent) return currentDeckTemplateId;
      const currentIndex = presets.findIndex(preset => preset.template_id === currentDeckTemplateId);
      const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % presets.length;
      return presets[nextIndex].template_id;
    }

    function currentImageStyleOptions() {
      const options = currentDeckImageGeneration?.style_options;
      return Array.isArray(options) && options.length ? options : FALLBACK_IMAGE_STYLE_OPTIONS;
    }

    function currentImageCoverageOptions() {
      const options = currentDeckImageGeneration?.coverage_options;
      return Array.isArray(options) && options.length ? options : FALLBACK_IMAGE_COVERAGE_OPTIONS;
    }

    function currentImageModelOptions() {
      const options = currentDeckImageGeneration?.supported_models;
      return Array.isArray(options) && options.length ? options : FALLBACK_IMAGE_MODELS;
    }

    function renderVisualControls() {
      const bar = document.getElementById('visualControlsBar');
      if (!bar) return;

      document.getElementById('imageStylePills').innerHTML = currentImageStyleOptions().map(option => `
        <button class="visual-pill${option.key === currentDeckImageStyle ? ' active' : ''}"
          onclick="setImageStyle('${escapeAttr(option.key)}')"
          title="${escapeHtml(option.label || option.key)}">
          ${escapeHtml(option.label || option.key)}
        </button>`).join('');

      document.getElementById('imageCoveragePills').innerHTML = currentImageCoverageOptions().map(option => `
        <button class="visual-pill${option.key === currentDeckImageCoverage ? ' active' : ''}"
          onclick="setImageCoverage('${escapeAttr(option.key)}')"
          title="${escapeHtml(option.label || option.key)}">
          ${escapeHtml(option.label || option.key)}
        </button>`).join('');

      const modelSelect = document.getElementById('imageModelSelect');
      modelSelect.innerHTML = currentImageModelOptions().map(option => `
        <option value="${escapeAttr(option.key)}"${option.key === currentDeckImageModel ? ' selected' : ''}>
          ${escapeHtml(option.label || option.key)}
        </option>`).join('');

      const imageGenUnavailable = currentDeckImageGeneration?.available === false;
      const note = cleanText(
        currentDeckData.generation_notice || (imageGenUnavailable ? currentDeckImageGeneration?.message : ''),
        currentDeckData.generation_mode === 'local'
          ? 'Using local deck structure with local image generation.'
          : currentDeckImageCoverage === 'hero-only'
            ? 'Fast local image mode: hero visuals first. Use Key Slides or Image Heavy when you want more.'
            : 'Higher coverage can take several minutes locally. Refresh visuals after changing style or model.'
      );
      document.getElementById('visualStatusNote').textContent = note;
      bar.style.display = 'flex';
    }

    function setImageStyle(styleKey) {
      currentDeckImageStyle = cleanText(styleKey, currentDeckImageStyle || 'deck-illustration');
      renderVisualControls();
    }

    function setImageCoverage(coverageKey) {
      currentDeckImageCoverage = cleanText(coverageKey, currentDeckImageCoverage || 'hero-only');
      renderVisualControls();
    }

    function setImageModel(modelKey) {
      currentDeckImageModel = cleanText(modelKey, currentDeckImageModel || 'lcm-dreamshaper-v7');
      renderVisualControls();
    }

    function refreshSlideVisuals() {
      currentDeckVisualRefreshKey += 1;
      slidesGenerated = false;
      showToast(currentDeckImageCoverage === 'hero-only'
        ? 'Refreshing hero visuals...'
        : `Refreshing ${currentDeckImageCoverage.replace('-', ' ')} visuals. This can take a while locally...`);
      generateSlides(false);
    }

    function buildLocalDeck(templateId) {
      const preset = getTemplatePreset(templateId);
      const pitch = currentContext.pitch || {};
      const deck = Array.isArray(pitch.deck) ? pitch.deck.slice(0, 10) : [];
      const market = currentContext.market_research || {};
      const score = currentContext.scorecard || {};
      const product = currentContext.product_strategy || {};
      const monetization = Array.isArray(product.monetization) ? product.monetization : [];

      const defaultTitles = [
        'The Category Is Breaking',
        'The Problem Is Structural',
        'Why Now Matters',
        'A Better Operating Layer',
        'How It Works',
        'Value Delivered Fast',
        'Proof That It Resonates',
        'A Scalable Revenue Engine',
        'What Comes Next',
        'Join The Build'
      ];
      const typeMap = ['hook','problem','stakes','solution','how_it_works','impact','proof','business_model','vision','call_to_action'];

      const slides = Array.from({ length: 10 }, (_, index) => {
        const source = deck[index] || {};
        const title = cleanText(source.title, defaultTitles[index]);
        const points = cleanList(source.key_points, 4);
        const type = typeMap[index] || 'story';
        const stats = [];

        if (index === 2) {
          if (market.market_size) stats.push({ value: market.market_size, label: 'Market Size' });
          if (market.growth_rate) stats.push({ value: market.growth_rate, label: 'Growth Rate' });
        }
        if (index === 5 && score.total) {
          stats.push({ value: `${score.total}/100`, label: 'Fundability Score' });
          if (score.verdict) stats.push({ value: score.verdict, label: 'Current Verdict' });
        }
        if (index === 7 && monetization.length) {
          monetization.slice(0, 2).forEach(item => {
            if (item?.model) stats.push({ value: item.model, label: 'Revenue Model' });
          });
        }

        return {
          slide_number: index + 1,
          type,
          layout: defaultLayoutForType(type, index),
          title,
          subtitle: cleanText(points[0] || market.opportunity_summary || market.pain_point || currentIdea),
          objective: cleanText([
            'Hook the audience with a sharp opening.',
            'Show the real friction clearly.',
            'Frame the urgency and timing.',
            'Position the product as the answer.',
            'Explain the workflow simply.',
            'Show measurable upside quickly.',
            'Give confidence through proof and traction.',
            'Show how the business compounds.',
            'Extend the story into the future.',
            'Close with a crisp investor ask.'
          ][index]),
          content: points.length ? points : cleanList([
            market.pain_point,
            market.target_customer,
            score.biggest_strength,
            score.biggest_risk
          ], 4),
          stats,
          visual_suggestion: cleanText([
            'Minimal hero composition with one symbolic visual anchor.',
            'Tension visual showing current user friction or fragmentation.',
            'Market framing graphic with one dominant numeric proof.',
            'Editorial product narrative block with clear contrast.',
            'Step-based workflow diagram with restrained motion feel.',
            'Outcome-led metrics panel with strong whitespace.',
            'Evidence slide mixing proof points and confidence markers.',
            'Business model frame with tiered monetization rhythm.',
            'Forward roadmap visual with milestone pacing.',
            'Closing slide with high-contrast call to action.'
          ][index]),
          design_notes: cleanText([
            'Use whitespace aggressively and keep the title dominant.',
            'Keep the composition sparse so the pain reads instantly.',
            'Lead with metrics before explanation.',
            'Balance one bold statement with one supporting panel.',
            'Use structured sequencing and clear progression.',
            'Make the proof cards feel premium, not dashboard-like.',
            'Keep this analytical and confidence-building.',
            'Use a clean pricing or revenue rhythm, not clutter.',
            'Let the roadmap breathe with strong vertical rhythm.',
            'End with a confident, clean CTA frame.'
          ][index]),
          animation_plan: {
            entry: ['Fade','Slide Up','Zoom'][index % 3],
            sequence: cleanList(points, 3).length ? cleanList(points, 3) : ['Title', 'Core message', 'Proof point'],
            transition: ['Smooth fade', 'Directional push', 'Soft zoom'][index % 3],
            emphasis: index === 5 || index === 7 ? 'Subtle stat emphasis' : ''
          }
        };
      });

      return {
        title: cleanText(currentIdea, 'Pitch Deck'),
        subtitle: 'Locally generated from existing VentureOS analysis',
        meta: {
          template_id: preset.template_id,
          theme_name: preset.theme_name,
          palette: preset.palette,
          style_notes: preset.style_notes
        },
        slides,
        image_generation: {
          selected_style: currentDeckImageStyle,
          selected_coverage: currentDeckImageCoverage,
          selected_model: currentDeckImageModel,
          style_options: FALLBACK_IMAGE_STYLE_OPTIONS,
          coverage_options: FALLBACK_IMAGE_COVERAGE_OPTIONS,
          supported_models: FALLBACK_IMAGE_MODELS
        },
        generation_mode: 'local-client',
        generation_notice: 'Using browser fallback deck. Refresh visuals after the local backend is available.'
      };
    }

    function renderContentList(items) {
      if (!items.length) return '';
      return `<ul class="slide-copy">${items.map((item, idx) => `
        <li class="slide-copy-item motion-item" style="--delay:${280 + (idx * 70)}ms;">
          <span class="slide-copy-bullet">${String(idx + 1).padStart(2, '0')}</span>
          <span>${escapeHtml(item)}</span>
        </li>`).join('')}
      </ul>`;
    }

    function renderStatsGrid(stats, delayStart = 360) {
      if (!stats.length) return '';
      return `<div class="slide-stat-grid">${stats.map((stat, idx) => `
        <div class="slide-stat-card motion-item" style="--delay:${delayStart + (idx * 70)}ms;">
          <div class="slide-stat-value">${escapeHtml(stat.value || '—')}</div>
          <div class="slide-stat-label">${escapeHtml(stat.label || 'Key Metric')}</div>
        </div>`).join('')}
      </div>`;
    }

    function renderFeatureImagePanel(slide, options = {}) {
      const hasImage = Boolean(slide.image_url);
      const delay = Number.isFinite(options.delay) ? options.delay : 260;
      const kicker = cleanText(options.kicker, slide.type ? slideTypeLabel(slide.type) : 'Visual');
      const caption = cleanText(
        options.caption,
        slide.visual_suggestion || slide.design_notes || 'Premium presentation visual'
      );
      const modelLabel = cleanText(slide.image_model);
      const className = `slide-feature-media motion-item${hasImage ? '' : ' is-placeholder'}`;

      return `
        <div class="${className}" style="--delay:${delay}ms;">
          ${hasImage
            ? `<img class="slide-generated-image slide-feature-image" src="${escapeAttr(slide.image_url)}" alt="${escapeAttr(slide.title || 'Generated slide visual')}" crossorigin="anonymous" />`
            : '<div class="slide-visual-orbit"></div>'}
          <div class="slide-feature-copy">
            <div class="slide-feature-kicker">${escapeHtml(kicker)}</div>
            <div class="slide-feature-caption">${escapeHtml(caption)}</div>
            ${modelLabel ? `<div class="slide-feature-model">Generated with ${escapeHtml(modelLabel)}</div>` : ''}
          </div>
        </div>`;
    }

    function renderRoadmap(items) {
      if (!items.length) return '';
      return `<div class="slide-roadmap">${items.map((item, idx) => `
        <div class="slide-roadmap-item motion-item" style="--delay:${300 + (idx * 75)}ms;">
          <div class="slide-roadmap-step">${String(idx + 1).padStart(2, '0')}</div>
          <div class="slide-roadmap-copy">${escapeHtml(item)}</div>
        </div>`).join('')}
      </div>`;
    }

    function renderVisualPanel(slide) {
      const hasImage = Boolean(slide.image_url);
      return `
        <div class="slide-visual-panel motion-item" style="--delay:320ms;">
          <div>
            <div class="slide-visual-label">Visual Direction</div>
            <div class="slide-visual-title">${escapeHtml(slide.visual_suggestion || 'Use one strong visual anchor that clarifies the point instantly.')}</div>
          </div>
          <div class="slide-visual-media">
            ${hasImage
              ? `<img class="slide-generated-image" src="${escapeAttr(slide.image_url)}" alt="${escapeAttr(slide.title || 'Generated slide visual')}" crossorigin="anonymous" />`
              : '<div class="slide-visual-orbit"></div>'}
          </div>
          <div class="slide-visual-caption">${escapeHtml(slide.design_notes || 'Use asymmetry, whitespace, and one dominant proof element.')}
            ${slide.image_model ? `<span class="slide-visual-model">Generated with ${escapeHtml(slide.image_model)}</span>` : ''}
          </div>
        </div>`;
    }

    function renderSideBlocks(slide) {
      if (slide.layout === 'roadmap') {
        return [
          renderRoadmap(slide.content),
          slide.stats.length ? renderStatsGrid(slide.stats, 560) : renderVisualPanel(slide)
        ].filter(Boolean).join('');
      }

      if (slide.layout === 'metrics') {
        return [
          slide.stats.length ? renderStatsGrid(slide.stats, 320) : renderVisualPanel(slide),
          slide.stats.length && slide.visual_suggestion ? renderVisualPanel(slide) : ''
        ].filter(Boolean).join('');
      }

      if (slide.layout === 'closing') {
        return [
          slide.stats.length ? renderStatsGrid(slide.stats, 340) : '',
          renderVisualPanel(slide)
        ].filter(Boolean).join('');
      }

      return [
        renderVisualPanel(slide),
        slide.stats.length ? renderStatsGrid(slide.stats, 560) : ''
      ].filter(Boolean).join('');
    }

    // ── SLIDE RENDERING SYSTEM ───────────────────────────────────────────────
    // Each theme has ONE unified shell (consistent header/footer/brand).
    // Inside the shell, content zones adapt to slide type (cover, two-col,
    // metrics, steps, closing). This gives professional consistency within a
    // deck while each theme looks structurally distinct from the others.

    function assignSlideLayouts(slides, templateId) {
      // No-op: layout is now driven by slide.type + theme shell, not random pools.
      // We keep this for API compatibility with renderSlides().
      return slides.map(s => ({ ...s }));
    }

    function createSlideMarkup(slide, index, total) {
      const preset = getTemplatePreset(currentDeckTemplateId);
      const variant = preset?.structureVariant || 'split-panel';
      switch (variant) {
        case 'consulting-grid':    return _themeConsulting(slide, index, total);
        case 'full-bleed-hero':    return _themeHero(slide, index, total);
        case 'data-dashboard':     return _themeDashboard(slide, index, total);
        case 'centered-editorial': return _themeEditorial(slide, index, total);
        default:                   return _themeClassic(slide, index, total);
      }
    }

    // ── Executive content zone renderers ───────────────────────────────────
    // Designed for investor/stakeholder audiences: clear hierarchy, data-led,
    // concise messaging, confident tone.

    function _execBullets(points) {
      if (!points?.length) return '';
      return `<ul style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:11px;">
        ${points.slice(0,5).map((pt,i) => `
          <li class="slide-copy-item motion-item" style="--delay:${200+i*60}ms;display:flex;align-items:flex-start;gap:12px;">
            <span class="slide-copy-bullet" style="flex-shrink:0;margin-top:5px;width:18px;height:18px;border-radius:4px;background:rgba(var(--deck-accent-rgb),.15);border:1px solid rgba(var(--deck-accent-rgb),.3);display:flex;align-items:center;justify-content:center;">
              <svg width="8" height="6" viewBox="0 0 8 6" fill="none"><path d="M1 3l2 2 4-4" stroke="var(--deck-accent)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </span>
            <span class="slide-copy-text" style="font-size:13.5px;line-height:1.58;color:var(--deck-text);font-weight:400;">${escapeHtml(pt)}</span>
          </li>`).join('')}
      </ul>`;
    }

    function _execSteps(points) {
      if (!points?.length) return '';
      return `<div style="display:flex;flex-direction:column;gap:9px;">
        ${points.slice(0,5).map((pt,i) => `
          <div class="slide-roadmap-item motion-item" style="--delay:${200+i*60}ms;display:grid;grid-template-columns:32px 1fr;gap:12px;align-items:start;padding:12px 14px;border-radius:8px;background:rgba(var(--deck-accent-rgb),.06);border:1px solid rgba(var(--deck-accent-rgb),.14);">
            <div class="slide-roadmap-step" style="width:32px;height:32px;border-radius:8px;background:rgba(var(--deck-accent-rgb),.18);border:1px solid rgba(var(--deck-accent-rgb),.28);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:var(--deck-accent);">${i+1}</div>
            <div class="slide-roadmap-copy" style="font-size:13px;line-height:1.55;color:var(--deck-text);padding-top:7px;">${escapeHtml(pt)}</div>
          </div>`).join('')}
      </div>`;
    }

    function _execStats(stats) {
      if (!stats?.length) return '';
      const count = Math.min(stats.length, 3);
      return `<div style="display:grid;grid-template-columns:repeat(${count},1fr);gap:10px;">
        ${stats.slice(0,3).map((s,i) => `
          <div class="slide-stat-card motion-item" style="--delay:${260+i*70}ms;padding:18px 14px;border-radius:10px;background:rgba(var(--deck-accent-rgb),.08);border:1px solid rgba(var(--deck-accent-rgb),.2);text-align:center;">
            <div class="slide-stat-value" style="font-size:28px;font-weight:700;color:var(--deck-accent);font-family:Georgia,serif;line-height:1;letter-spacing:-0.02em;">${escapeHtml(s.value||'—')}</div>
            <div class="slide-stat-label" style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--deck-text);opacity:.55;margin-top:7px;line-height:1.4;">${escapeHtml(s.label||'')}</div>
          </div>`).join('')}
      </div>`;
    }

    function _execInsightCard(text, delay=200) {
      // A premium single-insight callout — for standalone key messages
      return `<div class="slide-insight-card motion-item" style="--delay:${delay}ms;padding:20px 22px;border-radius:10px;border-left:4px solid var(--deck-accent);background:rgba(var(--deck-accent-rgb),.07);border-right:1px solid rgba(var(--deck-accent-rgb),.12);border-top:1px solid rgba(var(--deck-accent-rgb),.08);border-bottom:1px solid rgba(var(--deck-accent-rgb),.08);">
        <div class="slide-insight-copy" style="font-size:14px;line-height:1.65;color:var(--deck-text);font-style:italic;opacity:.88;">${escapeHtml(text)}</div>
      </div>`;
    }

    function _pickContentZone(slide) {
      const type = slide.type || '';
      const layout = slide.layout || '';
      const pts = (slide.content || []).filter(Boolean);
      const stats = (slide.stats || []).filter(s => s?.value || s?.label);
      const isStep = layout === 'roadmap' || ['how_it_works','business_model','process'].includes(type);
      const isProof = ['proof','traction','impact'].includes(type);
      const hasStats = stats.length > 0;

      // Proof/data slides: stats are the hero
      if (isProof && hasStats && pts.length) return `<div style="display:flex;flex-direction:column;gap:16px;">${_execStats(stats)}${_execBullets(pts.slice(0,3))}</div>`;
      if (isProof && hasStats) return _execStats(stats);
      // Roadmap/how-it-works: numbered steps
      if (isStep && pts.length) return _execSteps(pts);
      // Stats + bullets
      if (hasStats && pts.length) return `<div style="display:flex;flex-direction:column;gap:14px;">${_execStats(stats)}${_execBullets(pts.slice(0,3))}</div>`;
      if (hasStats) return _execStats(stats);
      if (pts.length) return _execBullets(pts);
      // Fallback: insight card with objective
      const fallback = slide.objective || slide.visual_suggestion || slide.subtitle || '';
      return fallback ? _execInsightCard(fallback) : '';
    }

    function _slideTypeTag(type, index, total) {
      const LABELS = {
        hook:'Opening', problem:'The Problem', stakes:'Market Opportunity',
        solution:'Our Solution', how_it_works:'How It Works', impact:'Value & Impact',
        proof:'Proof Points', business_model:'Business Model', vision:'Vision',
        call_to_action:'The Ask', traction:'Traction', story:'Overview'
      };
      const label = LABELS[type] || slideTypeLabel(type);
      return `<span class="slide-top-meta"><span style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--deck-accent);">${escapeHtml(label)}</span><span style="font-size:10px;opacity:.3;color:var(--deck-text);margin-left:10px;">${index+1} / ${total}</span></span>`;
    }

    // ══════════════════════════════════════════════════════════════════════════
    // EXECUTIVE SLIDE THEMES — 5 distinct shells, each cohesive & professional
    // Every shell: Cover (slide 0) · Inner · CTA (last slide) — 3 sub-layouts
    // Content zones adapt by slide.type; shell provides uniform brand/rhythm
    // ══════════════════════════════════════════════════════════════════════════

    // ── THEME A: Classic Split (Editorial Midnight) ─────────────────────────
    // Navy canvas. Left narrative / right content panel. Ruled topbar.
    function _themeClassic(slide, index, total) {
      const isCover = index === 0;
      const isCTA   = index === total - 1;
      const content = _pickContentZone(slide);
      const titleFs = slide.title.length > 45 ? '28px' : slide.title.length > 30 ? '32px' : '38px';
      const classicSide = slide.image_url
        ? `<div style="display:flex;flex-direction:column;gap:14px;min-height:0;">${content || ''}${renderVisualPanel(slide)}</div>`
        : content;

      if (isCover) return `
        <div class="slide-shell" style="display:flex;flex-direction:column;padding:34px 40px 30px;gap:0;position:relative;">
          <div class="motion-item" style="--delay:0ms;display:flex;align-items:center;justify-content:space-between;padding-bottom:12px;border-bottom:1px solid rgba(var(--deck-accent-rgb),.18);margin-bottom:18px;">
            ${_slideTypeTag(slide.type,index,total)}
            <span style="font-size:9px;opacity:.22;color:var(--deck-text);letter-spacing:.06em;">VentureOS</span>
          </div>
          <div style="display:grid;grid-template-columns:1.02fr .98fr;gap:28px;align-items:center;flex:1;min-height:0;">
            <div style="display:flex;flex-direction:column;justify-content:center;min-height:0;">
              <div class="slide-title motion-item" style="--delay:60ms;font-size:44px;font-weight:700;font-family:Georgia,serif;line-height:1.08;letter-spacing:-.03em;color:var(--deck-text);max-width:9ch;margin-bottom:14px;">${escapeHtml(slide.title)}</div>
              ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:150ms;font-size:14px;opacity:.58;color:var(--deck-text);max-width:34ch;line-height:1.68;font-weight:300;margin-bottom:22px;">${escapeHtml(slide.subtitle)}</div>`:''}
              ${slide.content?.length?`<div style="margin-bottom:20px;">${_execBullets(slide.content.slice(0, 3))}</div>`:''}
              ${slide.stats?.length?`<div class="motion-item" style="--delay:320ms;max-width:540px;">${_execStats(slide.stats)}</div>`:''}
              <div class="motion-item" style="--delay:420ms;display:flex;align-items:center;gap:16px;margin-top:18px;">
                <div style="height:2px;width:40px;background:var(--deck-accent);border-radius:1px;"></div>
                <span style="font-size:11px;opacity:.4;color:var(--deck-text);letter-spacing:.06em;">Confidential · For Investor Use Only</span>
              </div>
            </div>
            <div style="height:100%;min-height:0;">${renderFeatureImagePanel(slide, { delay: 210, kicker: 'Hero Visual', caption: slide.visual_suggestion || 'Editorial investor-grade cover visual with strong negative space.' })}</div>
          </div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;

      if (isCTA) return `
        <div class="slide-shell" style="display:flex;flex-direction:column;padding:34px 40px 30px;gap:0;position:relative;">
          <div class="motion-item" style="--delay:0ms;display:flex;align-items:center;justify-content:space-between;padding-bottom:12px;border-bottom:1px solid rgba(var(--deck-accent-rgb),.18);margin-bottom:18px;">
            ${_slideTypeTag(slide.type,index,total)}
            <span style="font-size:9px;opacity:.22;color:var(--deck-text);letter-spacing:.06em;">VentureOS</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr .92fr;gap:24px;align-items:center;flex:1;min-height:0;">
            <div style="display:flex;flex-direction:column;justify-content:center;">
              <div class="slide-title motion-item" style="--delay:70ms;font-size:40px;font-weight:700;font-family:Georgia,serif;line-height:1.12;color:var(--deck-text);max-width:12ch;margin-bottom:14px;">${escapeHtml(slide.title)}</div>
              ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:150ms;font-size:14px;opacity:.6;color:var(--deck-text);max-width:34ch;line-height:1.65;margin-bottom:22px;font-weight:300;">${escapeHtml(slide.subtitle)}</div>`:''}
              ${slide.stats?.length
                ? `<div class="motion-item" style="--delay:240ms;max-width:540px;">${_execStats(slide.stats)}</div>`
                : slide.content?.length
                  ? `<div class="motion-item" style="--delay:240ms;max-width:520px;">${_execBullets(slide.content)}</div>`
                  : ''}
            </div>
            <div style="height:100%;min-height:0;">${renderFeatureImagePanel(slide, { delay: 220, kicker: 'Closing Visual', caption: slide.visual_suggestion || 'Decisive final visual for a strong call to action.' })}</div>
          </div>
          <div class="motion-item" style="--delay:700ms;display:flex;justify-content:flex-end;align-items:center;padding-top:10px;border-top:1px solid rgba(var(--deck-accent-rgb),.1);margin-top:14px;">
            <span style="font-size:9px;opacity:.25;color:var(--deck-text);">${index+1} / ${total}</span>
          </div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;

      return `
        <div class="slide-shell" style="display:flex;flex-direction:column;padding:24px 32px 20px;gap:0;">
          <div class="motion-item" style="--delay:0ms;display:flex;align-items:center;justify-content:space-between;padding-bottom:12px;border-bottom:1px solid rgba(var(--deck-accent-rgb),.18);margin-bottom:18px;">
            ${_slideTypeTag(slide.type,index,total)}
            <span style="font-size:9px;opacity:.22;color:var(--deck-text);letter-spacing:.06em;">VentureOS</span>
          </div>
          <div style="display:grid;grid-template-columns:1.1fr 0.9fr;gap:28px;flex:1;align-items:start;min-height:0;">
            <div style="display:flex;flex-direction:column;gap:12px;min-height:0;">
              <div class="slide-title motion-item" style="--delay:60ms;font-size:${titleFs};font-weight:700;font-family:Georgia,serif;line-height:1.2;letter-spacing:-.01em;color:var(--deck-text);">${escapeHtml(slide.title)}</div>
              ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:130ms;font-size:12.5px;opacity:.55;color:var(--deck-text);line-height:1.6;font-weight:300;max-width:38ch;">${escapeHtml(slide.subtitle)}</div>`:''}
              ${slide.objective?`<div class="motion-item" style="--delay:160ms;font-size:11.5px;opacity:.4;color:var(--deck-text);line-height:1.55;font-style:italic;max-width:36ch;padding-top:4px;">${escapeHtml(slide.objective)}</div>`:''}
            </div>
            <div style="min-height:0;">${classicSide}</div>
          </div>
          <div class="motion-item" style="--delay:700ms;display:flex;justify-content:flex-end;align-items:center;padding-top:10px;border-top:1px solid rgba(var(--deck-accent-rgb),.1);margin-top:14px;">
            <span style="font-size:9px;opacity:.25;color:var(--deck-text);">${index+1} / ${total}</span>
          </div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;
    }

    // ── THEME B: Consulting (Boardroom Ivory) ───────────────────────────────
    // Light canvas. Thick top rule. Full-width title header. Numbered card grid.
    function _themeConsulting(slide, index, total) {
      const isCover = index === 0;
      const isCTA   = index === total - 1;
      const pts = (slide.content || []).filter(Boolean);
      const stats = (slide.stats || []).filter(s => s?.value || s?.label);
      const titleFs = slide.title.length > 48 ? '26px' : slide.title.length > 32 ? '30px' : '36px';

      if (isCover || isCTA) return `
        <div class="slide-shell" style="display:flex;flex-direction:column;padding:0;position:relative;">
          <div style="height:6px;background:linear-gradient(90deg,var(--deck-accent),rgba(var(--deck-accent-rgb),.4));"></div>
          <div style="flex:1;display:grid;grid-template-columns:1.02fr .98fr;align-items:center;gap:24px;padding:34px 42px;">
            <div style="display:flex;flex-direction:column;justify-content:center;min-height:0;">
              <div class="slide-top-meta motion-item" style="--delay:0ms;font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--deck-accent);margin-bottom:18px;opacity:.85;">${isCover?'Investor Presentation':'Strategic Ask'} · ${new Date().getFullYear()}</div>
              <div class="slide-title motion-item" style="--delay:70ms;font-size:42px;font-weight:700;font-family:Georgia,serif;line-height:1.08;letter-spacing:-.02em;color:var(--deck-text);max-width:11ch;margin-bottom:16px;">${escapeHtml(slide.title)}</div>
              ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:170ms;font-size:14px;opacity:.52;color:var(--deck-text);max-width:34ch;line-height:1.68;font-weight:300;">${escapeHtml(slide.subtitle)}</div>`:''}
              ${stats.length
                ? `<div class="motion-item" style="--delay:260ms;margin-top:24px;max-width:540px;">${_execStats(stats)}</div>`
                : slide.content?.length
                  ? `<div class="motion-item" style="--delay:260ms;margin-top:22px;max-width:500px;">${_execBullets(slide.content.slice(0, 3))}</div>`
                  : ''}
            </div>
            <div style="height:100%;min-height:0;">${renderFeatureImagePanel(slide, {
              delay: 210,
              kicker: isCover ? 'Cover Visual' : 'Closing Visual',
              caption: slide.visual_suggestion || 'Premium boardroom visual with strong whitespace and clarity.'
            })}</div>
          </div>
          <div style="padding:14px 56px;border-top:1px solid rgba(var(--deck-accent-rgb),.2);display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:10px;opacity:.32;color:var(--deck-text);">VentureOS · Confidential</span>
            <span style="font-size:10px;opacity:.32;color:var(--deck-text);">${index+1} / ${total}</span>
          </div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;

      const cardData = pts.slice(0,4);
      const cards = cardData.length ? cardData.map((pt,i) => `
        <div class="slide-roadmap-item motion-item" style="--delay:${180+i*65}ms;padding:16px 18px;border-radius:8px;background:rgba(var(--deck-accent-rgb),.06);border:1px solid rgba(var(--deck-accent-rgb),.16);">
          <div class="slide-roadmap-step" style="font-size:10px;font-weight:700;letter-spacing:.1em;color:var(--deck-accent);margin-bottom:8px;text-transform:uppercase;">0${i+1}</div>
          <div class="slide-roadmap-copy" style="font-size:13px;line-height:1.58;color:var(--deck-text);">${escapeHtml(pt)}</div>
        </div>`).join('') : `<div class="slide-insight-card motion-item" style="--delay:180ms;padding:16px 18px;border-radius:8px;background:rgba(var(--deck-accent-rgb),.06);font-size:13px;opacity:.6;color:var(--deck-text);"><div class="slide-insight-copy">${escapeHtml(slide.objective||slide.visual_suggestion||'')}</div></div>`;
      const consultingBody = slide.image_url
        ? `<div style="display:flex;flex-direction:column;gap:14px;height:100%;">
            <div style="display:grid;grid-template-columns:${cardData.length>2?'1fr 1fr':'1fr'};gap:10px;align-content:start;">
              ${cards}
            </div>
            <div style="min-height:0;">${renderFeatureImagePanel(slide, { delay: 320, kicker: 'Supporting Visual', caption: slide.visual_suggestion || 'Premium supporting image with strong boardroom restraint.' })}</div>
          </div>`
        : `<div style="display:grid;grid-template-columns:${cardData.length>2?'1fr 1fr':'1fr'};gap:10px;align-content:start;">${cards}</div>`;

      return `
        <div class="slide-shell" style="display:flex;flex-direction:column;padding:0;">
          <div style="height:4px;background:var(--deck-accent);"></div>
          <div class="motion-item" style="--delay:0ms;padding:18px 32px 14px;display:flex;justify-content:space-between;align-items:flex-end;border-bottom:1px solid rgba(var(--deck-accent-rgb),.18);">
            <div style="flex:1;min-width:0;">
              <div style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--deck-accent);margin-bottom:6px;opacity:.8;">${_slideTypeTag(slide.type,index,total)}</div>
              <div class="slide-title" style="font-size:${titleFs};font-weight:700;color:var(--deck-text);font-family:Georgia,serif;line-height:1.2;max-width:580px;">${escapeHtml(slide.title)}</div>
            </div>
            <span style="font-size:9px;opacity:.22;color:var(--deck-text);flex-shrink:0;margin-left:16px;">VentureOS</span>
          </div>
          ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:60ms;padding:8px 32px 0;font-size:12.5px;opacity:.52;color:var(--deck-text);font-weight:300;line-height:1.55;">${escapeHtml(slide.subtitle)}</div>`:''}
          <div style="flex:1;padding:14px 32px;align-content:start;min-height:0;">
            ${consultingBody}
          </div>
          ${stats.length?`<div class="motion-item" style="--delay:440ms;display:flex;border-top:1px solid rgba(var(--deck-accent-rgb),.18);padding:0 32px;">
            ${stats.slice(0,3).map((s,i)=>`<div class="slide-stat-card" style="flex:1;padding:12px 14px;${i>0?'border-left:1px solid rgba(var(--deck-accent-rgb),.15);':''}">
              <div class="slide-stat-value" style="font-size:20px;font-weight:700;color:var(--deck-accent);font-family:Georgia,serif;">${escapeHtml(s.value||'—')}</div>
              <div class="slide-stat-label" style="font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;opacity:.5;margin-top:3px;color:var(--deck-text);">${escapeHtml(s.label||'')}</div>
            </div>`).join('')}
          </div>`:
          `<div style="padding:10px 32px 12px;border-top:1px solid rgba(var(--deck-accent-rgb),.1);display:flex;justify-content:flex-end;">
            <span style="font-size:9px;opacity:.25;color:var(--deck-text);">${index+1} / ${total}</span>
          </div>`}
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;
    }

    // ── THEME C: Hero (Kinetic Ember) ───────────────────────────────────────
    // Dark canvas. Bold 5px accent bar. Two-column: story left, panel right.
    function _themeHero(slide, index, total) {
      const isCover = index === 0;
      const isCTA   = index === total - 1;
      const pts = (slide.content || []).filter(Boolean);
      const stats = (slide.stats || []).filter(s => s?.value || s?.label);
      const titleFs = slide.title.length > 40 ? '28px' : slide.title.length > 26 ? '33px' : '39px';

      if (isCover || isCTA) return `
        <div class="slide-shell" style="display:flex;flex-direction:row;padding:0;overflow:hidden;">
          <div style="width:6px;background:var(--deck-accent);flex-shrink:0;"></div>
          <div style="flex:1;display:grid;grid-template-columns:1fr .92fr;align-items:center;gap:24px;padding:34px 38px;position:relative;">
            <div style="display:flex;flex-direction:column;justify-content:center;min-height:0;">
              <div class="slide-top-meta motion-item" style="--delay:0ms;font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--deck-accent);margin-bottom:18px;opacity:.85;">${isCover?'Investor Deck':'The Ask'} · ${new Date().getFullYear()}</div>
              <div class="slide-title motion-item" style="--delay:70ms;font-size:44px;font-weight:800;font-family:Georgia,serif;line-height:1.06;letter-spacing:-.02em;color:var(--deck-text);max-width:10ch;margin-bottom:14px;">${escapeHtml(slide.title)}</div>
              ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:170ms;font-size:14px;opacity:.58;color:var(--deck-text);max-width:34ch;line-height:1.68;font-weight:300;margin-bottom:${stats.length?'22px':'0px'};">${escapeHtml(slide.subtitle)}</div>`:''}
              ${stats.length
                ? `<div class="motion-item" style="--delay:260ms;max-width:540px;">${_execStats(stats)}</div>`
                : slide.content?.length
                  ? `<div class="motion-item" style="--delay:260ms;max-width:500px;">${_execBullets(slide.content.slice(0, 3))}</div>`
                  : ''}
            </div>
            <div style="height:100%;min-height:0;">${renderFeatureImagePanel(slide, {
              delay: 210,
              kicker: isCover ? 'Launch Visual' : 'Ask Visual',
              caption: slide.visual_suggestion || 'Bold keynote visual with a premium, high-contrast composition.'
            })}</div>
            <div class="motion-item" style="--delay:700ms;position:absolute;bottom:22px;right:24px;font-size:9px;opacity:.25;color:var(--deck-text);text-align:right;">VentureOS<br>${index+1} / ${total}</div>
          </div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;

      const rightPanel = slide.image_url && !stats.length
        ? renderFeatureImagePanel(slide, {
            delay: 240,
            kicker: 'Visual Direction',
            caption: slide.visual_suggestion || 'Premium supporting image'
          })
        : stats.length
        ? `<div style="display:flex;flex-direction:column;gap:10px;">
            ${stats.slice(0,3).map((s,i)=>`
              <div class="slide-stat-card motion-item" style="--delay:${260+i*75}ms;padding:16px 18px;border-radius:10px;background:rgba(var(--deck-accent-rgb),.09);border:1px solid rgba(var(--deck-accent-rgb),.2);">
                <div class="slide-stat-value" style="font-size:26px;font-weight:700;color:var(--deck-accent);font-family:Georgia,serif;line-height:1;">${escapeHtml(s.value||'—')}</div>
                <div class="slide-stat-label" style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;opacity:.5;color:var(--deck-text);margin-top:5px;">${escapeHtml(s.label||'')}</div>
              </div>`).join('')}
          </div>`
        : slide.visual_suggestion
          ? `<div class="motion-item" style="--delay:260ms;height:100%;padding:20px;border-radius:10px;background:rgba(var(--deck-accent-rgb),.06);border:1px solid rgba(var(--deck-accent-rgb),.14);display:flex;flex-direction:column;gap:12px;justify-content:center;">
              <div style="font-size:9.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--deck-accent);opacity:.7;">Visual Direction</div>
              <div style="font-size:13px;line-height:1.6;opacity:.7;color:var(--deck-text);">${escapeHtml(slide.visual_suggestion)}</div>
            </div>`
          : '';

      return `
        <div class="slide-shell" style="display:flex;flex-direction:row;padding:0;overflow:hidden;">
          <div style="width:5px;background:var(--deck-accent);flex-shrink:0;"></div>
          <div style="flex:1;display:flex;flex-direction:column;padding:22px 28px 18px;">
            <div class="motion-item" style="--delay:0ms;display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid rgba(var(--deck-accent-rgb),.15);">
              ${_slideTypeTag(slide.type,index,total)}
              <span style="font-size:9px;opacity:.22;color:var(--deck-text);">VentureOS</span>
            </div>
            <div style="flex:1;display:grid;grid-template-columns:1.05fr 0.95fr;gap:22px;align-items:start;min-height:0;">
              <div style="display:flex;flex-direction:column;gap:12px;min-height:0;">
                <div class="slide-title motion-item" style="--delay:60ms;font-size:${titleFs};font-weight:800;font-family:Georgia,serif;line-height:1.18;letter-spacing:-.01em;color:var(--deck-text);">${escapeHtml(slide.title)}</div>
                ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:130ms;font-size:12.5px;opacity:.55;color:var(--deck-text);line-height:1.58;font-weight:300;">${escapeHtml(slide.subtitle)}</div>`:''}
                <div style="margin-top:4px;">${_pickContentZone({...slide,stats:[]})}</div>
              </div>
              <div style="height:100%;">${rightPanel}</div>
            </div>
            <div class="motion-item" style="--delay:700ms;padding-top:10px;border-top:1px solid rgba(var(--deck-accent-rgb),.1);margin-top:10px;display:flex;justify-content:flex-end;">
              <span style="font-size:9px;opacity:.22;color:var(--deck-text);">${index+1} / ${total}</span>
            </div>
          </div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;
    }

    // ── THEME D: Dashboard (Atlas Sapphire) ─────────────────────────────────
    // Deep navy. Left sidebar with index + section. Right main content area.
    function _themeDashboard(slide, index, total) {
      const isCover = index === 0;
      const isCTA   = index === total - 1;
      const pts = (slide.content || []).filter(Boolean);
      const stats = (slide.stats || []).filter(s => s?.value || s?.label);
      const titleFs = slide.title.length > 42 ? '26px' : slide.title.length > 28 ? '30px' : '34px';

      if (isCover || isCTA) return `
        <div class="slide-shell" style="display:flex;flex-direction:row;padding:0;gap:0;">
          <div style="width:220px;flex-shrink:0;background:rgba(var(--deck-accent-rgb),.1);border-right:1px solid rgba(var(--deck-accent-rgb),.2);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:32px 20px;gap:14px;text-align:center;">
            <div class="motion-item" style="--delay:0ms;font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--deck-accent);opacity:.8;">${isCover?'Investor Deck':'Strategic Ask'}</div>
            <div class="motion-item" style="--delay:60ms;font-size:52px;font-weight:800;color:var(--deck-text);font-family:Georgia,serif;line-height:1;">${String(index+1).padStart(2,'0')}</div>
            <div style="width:28px;height:2px;background:var(--deck-accent);border-radius:1px;"></div>
            <div style="font-size:9.5px;opacity:.28;color:var(--deck-text);">of ${total} slides</div>
            <div style="margin-top:auto;font-size:10px;font-weight:600;letter-spacing:.08em;color:var(--deck-accent);opacity:.5;">VentureOS</div>
          </div>
          <div style="flex:1;display:grid;grid-template-columns:1fr .92fr;align-items:center;padding:30px 32px;gap:22px;">
            <div style="display:flex;flex-direction:column;justify-content:center;min-height:0;">
              <div class="slide-title motion-item" style="--delay:80ms;font-size:40px;font-weight:700;font-family:Georgia,serif;line-height:1.1;letter-spacing:-.02em;color:var(--deck-text);max-width:11ch;">${escapeHtml(slide.title)}</div>
              ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:170ms;font-size:13.5px;opacity:.56;color:var(--deck-text);max-width:34ch;line-height:1.68;font-weight:300;margin-top:12px;">${escapeHtml(slide.subtitle)}</div>`:''}
              ${stats.length
                ? `<div class="motion-item" style="--delay:260ms;margin-top:22px;max-width:520px;">${_execStats(stats)}</div>`
                : slide.content?.length
                  ? `<div class="motion-item" style="--delay:260ms;margin-top:20px;max-width:500px;">${_execBullets(slide.content.slice(0, 3))}</div>`
                  : ''}
            </div>
            <div style="height:100%;min-height:0;">${renderFeatureImagePanel(slide, {
              delay: 210,
              kicker: isCover ? 'Category Visual' : 'Future Visual',
              caption: slide.visual_suggestion || 'Structured premium image supporting the main narrative.'
            })}</div>
          </div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;

      const zone = slide.image_url && !stats.length
        ? `<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;height:100%;">${_pickContentZone({ ...slide, image_url: '', image_model: '' })}<div style="min-height:0;">${renderFeatureImagePanel(slide, { delay: 250, kicker: 'Supporting Visual', caption: slide.visual_suggestion || 'Premium contextual image' })}</div></div>`
        : _pickContentZone(slide);
      return `
        <div class="slide-shell" style="display:flex;flex-direction:row;padding:0;gap:0;">
          <div style="width:150px;flex-shrink:0;background:rgba(var(--deck-accent-rgb),.08);border-right:1px solid rgba(var(--deck-accent-rgb),.16);padding:22px 16px;display:flex;flex-direction:column;gap:0;">
            <div class="motion-item" style="--delay:0ms;flex:1;">
              <div style="font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--deck-accent);margin-bottom:8px;opacity:.8;">Section</div>
              <div style="font-size:11.5px;color:var(--deck-text);opacity:.8;line-height:1.45;">${escapeHtml(slideTypeLabel(slide.type).replace(/_/g,' '))}</div>
            </div>
            <div class="motion-item" style="--delay:40ms;">
              <div style="font-size:33px;font-weight:800;color:var(--deck-text);font-family:Georgia,serif;line-height:1;">${String(index+1).padStart(2,'0')}</div>
              <div style="font-size:9px;opacity:.28;color:var(--deck-text);margin-top:3px;">of ${total}</div>
            </div>
            <div style="font-size:8.5px;opacity:.2;color:var(--deck-text);margin-top:14px;letter-spacing:.06em;">VentureOS</div>
          </div>
          <div style="flex:1;padding:20px 24px 16px;display:flex;flex-direction:column;gap:12px;overflow:hidden;min-width:0;">
            <div class="motion-item" style="--delay:60ms;padding-bottom:10px;border-bottom:1px solid rgba(var(--deck-accent-rgb),.16);">
              <div class="slide-title" style="font-size:${titleFs};font-weight:700;color:var(--deck-text);font-family:Georgia,serif;line-height:1.22;">${escapeHtml(slide.title)}</div>
              ${slide.subtitle?`<div class="slide-subtitle" style="font-size:12px;opacity:.52;color:var(--deck-text);margin-top:5px;line-height:1.55;font-weight:300;">${escapeHtml(slide.subtitle)}</div>`:''}
            </div>
            <div style="flex:1;overflow:hidden;">${zone}</div>
            <div class="motion-item" style="--delay:700ms;display:flex;justify-content:flex-end;">
              <span style="font-size:9px;opacity:.2;color:var(--deck-text);">${index+1} / ${total}</span>
            </div>
          </div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;
    }

    // ── THEME E: Editorial (Monochrome Luxe) ────────────────────────────────
    // Black canvas. Centered luxury cover. Inner: full-width title + body grid.
    function _themeEditorial(slide, index, total) {
      const isCover = index === 0;
      const isCTA   = index === total - 1;
      const pts = (slide.content || []).filter(Boolean);
      const stats = (slide.stats || []).filter(s => s?.value || s?.label);
      const titleFs = slide.title.length > 50 ? '26px' : slide.title.length > 34 ? '32px' : '40px';

      if (isCover || isCTA) return `
        <div class="slide-shell" style="display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:44px 68px;gap:0;position:relative;">
          <div class="slide-top-meta motion-item" style="--delay:0ms;font-size:10px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:var(--deck-accent);margin-bottom:24px;opacity:.8;">${isCover?'Confidential · Investor Presentation':'The Strategic Ask'}</div>
          <div class="slide-title motion-item" style="--delay:70ms;font-size:${titleFs};font-weight:700;font-family:Georgia,serif;line-height:1.18;letter-spacing:-.02em;color:var(--deck-text);max-width:680px;margin-bottom:18px;">${escapeHtml(slide.title)}</div>
          <div class="motion-item" style="--delay:190ms;width:44px;height:1px;background:var(--deck-accent);margin-bottom:18px;"></div>
          ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:250ms;font-size:14.5px;opacity:.52;color:var(--deck-text);max-width:480px;line-height:1.68;font-weight:300;">${escapeHtml(slide.subtitle)}</div>`:''}
          <div style="margin-top:24px;width:100%;max-width:520px;">${renderFeatureImagePanel(slide, {
            delay: 320,
            kicker: isCover ? 'Editorial Visual' : 'Closing Visual',
            caption: slide.visual_suggestion || 'Refined, premium image direction with strong editorial tone.'
          })}</div>
          ${stats.length ? `<div class="motion-item" style="--delay:380ms;margin-top:20px;width:100%;max-width:560px;">${_execStats(stats)}</div>` : ''}
          <div class="motion-item" style="--delay:700ms;position:absolute;bottom:24px;font-size:9px;letter-spacing:.14em;opacity:.2;color:var(--deck-text);text-transform:uppercase;">VentureOS · ${index+1} / ${total}</div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;

      const hasGrid = pts.length >= 3;
      const baseBodyZone = hasGrid
        ? `<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
            ${pts.slice(0,4).map((pt,i)=>`
              <div class="slide-roadmap-item motion-item" style="--delay:${220+i*65}ms;padding:15px 17px;border-radius:8px;border:1px solid rgba(var(--deck-accent-rgb),.2);background:rgba(var(--deck-accent-rgb),.05);">
                <div class="slide-roadmap-step" style="font-size:10px;font-weight:700;letter-spacing:.1em;color:var(--deck-accent);margin-bottom:7px;text-transform:uppercase;">0${i+1}</div>
                <div class="slide-roadmap-copy" style="font-size:13px;line-height:1.58;color:var(--deck-text);">${escapeHtml(pt)}</div>
              </div>`).join('')}
          </div>`
        : _pickContentZone(slide);
      const bodyZone = slide.image_url && !stats.length
        ? `<div style="display:grid;grid-template-columns:1fr .96fr;gap:18px;align-items:start;min-height:0;">
            <div>${baseBodyZone}</div>
            <div style="min-height:0;">${renderFeatureImagePanel(slide, { delay: 280, kicker: 'Visual Direction', caption: slide.visual_suggestion || 'Premium supporting image' })}</div>
          </div>`
        : baseBodyZone;

      return `
        <div class="slide-shell" style="display:flex;flex-direction:column;padding:24px 40px 18px;">
          <div class="motion-item" style="--delay:0ms;display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
            ${_slideTypeTag(slide.type,index,total)}
            <span style="font-size:9px;opacity:.2;color:var(--deck-text);letter-spacing:.06em;">VentureOS</span>
          </div>
          <div class="slide-title motion-item" style="--delay:70ms;font-size:${titleFs};font-weight:700;font-family:Georgia,serif;line-height:1.2;letter-spacing:-.01em;color:var(--deck-text);margin-bottom:8px;max-width:620px;">${escapeHtml(slide.title)}</div>
          ${slide.subtitle?`<div class="slide-subtitle motion-item" style="--delay:140ms;font-size:12.5px;opacity:.5;color:var(--deck-text);margin-bottom:14px;line-height:1.58;font-weight:300;">${escapeHtml(slide.subtitle)}</div>`:'<div style="margin-bottom:12px;"></div>'}
          <div class="motion-item" style="--delay:180ms;width:100%;height:1px;background:rgba(var(--deck-accent-rgb),.28);margin-bottom:18px;"></div>
          <div style="flex:1;overflow:hidden;">
            ${stats.length?`<div style="display:flex;flex-direction:column;gap:14px;">${_execStats(stats)}${hasGrid?bodyZone:_execBullets(pts)}</div>`:bodyZone||`<div class="slide-insight-copy" style="font-size:13px;opacity:.48;color:var(--deck-text);line-height:1.65;font-weight:300;">${escapeHtml(slide.objective||slide.visual_suggestion||'')}</div>`}
          </div>
          <div class="motion-item" style="--delay:700ms;padding-top:10px;border-top:1px solid rgba(var(--deck-accent-rgb),.12);margin-top:12px;display:flex;justify-content:flex-end;">
            <span style="font-size:9px;opacity:.2;color:var(--deck-text);">${index+1} / ${total}</span>
          </div>
          <div class="present-hint">Arrow keys or click · Esc to exit</div>
        </div>`;
    }

        function renderInspector() {
      const inspector = document.getElementById('slideInspector');
      const slide = currentDeckData.slides[currentSlideIndex];
      const meta = currentDeckData.meta;
      if (!slide || !meta) { inspector.innerHTML = ''; return; }

      const paletteEntries = Object.entries(meta.palette || {}).slice(0, 4);
      inspector.innerHTML = `
        <div class="inspector-card">
          <div class="inspector-meta">
            <strong>${escapeHtml(slide.title)}</strong>
            <span>${currentSlideIndex + 1} / ${totalSlides}</span>
          </div>
          <div class="inspector-card-title">Objective</div>
          <div class="inspector-card-copy">${escapeHtml(slide.objective || 'Clarify the narrative move of this slide.')}</div>
        </div>
        <div class="inspector-card">
          <div class="inspector-card-title">Visual + Layout</div>
          <ul class="inspector-note-list">
            <li>${escapeHtml(slide.visual_suggestion || 'Lead with a single proof-driven visual.')}</li>
            <li>${escapeHtml(slide.design_notes || 'Keep alignment disciplined and spacing generous.')}</li>
            ${slide.image_model ? `<li>Generated image: ${escapeHtml(slide.image_model)}</li>` : ''}
            ${slide.image_status === 'failed' ? `<li>Image generation issue: ${escapeHtml(slide.image_error || 'Unknown error')}</li>` : ''}
            ${!slide.image_url && slide.image_status !== 'failed' ? '<li>No image attached to this slide with the current coverage setting.</li>' : ''}
          </ul>
        </div>
        <div class="inspector-card">
          <div class="inspector-card-title">Deck System</div>
          <div class="inspector-card-copy" style="margin-bottom:12px;">${escapeHtml(meta.theme_name || 'Editorial Midnight')}</div>
          <div class="inspector-palette">
            ${paletteEntries.map(([label, value]) => `
              <div class="inspector-swatch" style="background:${escapeHtml(value)};color:${getContrastingText(value)};">
                <div class="inspector-swatch-label" style="color:${getContrastingText(value)};">${escapeHtml(label)}</div>
                <div class="inspector-swatch-value" style="color:${getContrastingText(value)};">${escapeHtml(value)}</div>
              </div>`).join('')}
          </div>
          ${meta.style_notes?.length ? `
            <div class="inspector-card-title" style="margin-top:14px;">Style Notes</div>
            <ul class="inspector-note-list">${meta.style_notes.map(note => `<li>${escapeHtml(note)}</li>`).join('')}</ul>` : ''}
        </div>
        <div class="inspector-card">
          <div class="inspector-card-title">Animation Plan</div>
          <div class="inspector-motion-grid">
            <div class="inspector-motion-row"><span>Entry</span><strong>${escapeHtml(slide.animation_plan.entry || 'Fade')}</strong></div>
            <div class="inspector-motion-row"><span>Transition</span><strong>${escapeHtml(slide.animation_plan.transition || 'Smooth fade')}</strong></div>
            ${slide.animation_plan.emphasis ? `<div class="inspector-motion-row"><span>Emphasis</span><strong>${escapeHtml(slide.animation_plan.emphasis)}</strong></div>` : ''}
          </div>
          <div class="inspector-card-title" style="margin-top:14px;">Sequence</div>
          <div class="inspector-step-list">
            ${slide.animation_plan.sequence.map((step, idx) => `
              <div class="inspector-step">
                <div class="inspector-step-num">${idx + 1}</div>
                <div class="inspector-step-copy">${escapeHtml(step)}</div>
              </div>`).join('')}
          </div>
        </div>`;
    }

    function playSlideMotion(slideEl) {
      if (!slideEl) return;
      slideEl.classList.remove('motion-playing');
      void slideEl.offsetWidth;
      slideEl.classList.add('motion-playing');
    }

    function openSlideModal() {
      if (!currentIdea) { alert('Run VentureOS first.'); return; }
      document.getElementById('slideDeckModal').classList.add('open');
      document.body.style.overflow = 'hidden';
      if (!slidesGenerated) generateSlides();
    }

    function closeSlideModal(e) {
      if (e.target === document.getElementById('slideDeckModal')) closeSlideModalDirect();
    }

    function closeSlideModalDirect() {
      if (isPresenting) exitPresent();
      document.getElementById('slideDeckModal').classList.remove('open');
      document.body.style.overflow = '';
    }

    // Keyboard navigation
    document.addEventListener('keydown', e => {
      const modalOpen = document.getElementById('slideDeckModal').classList.contains('open');
      if (e.key === 'Escape') { closeSlideModalDirect(); return; }
      if (!modalOpen) return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); nextSlide(); }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); prevSlide(); }
      if (e.key === 'f' || e.key === 'F') togglePresent();
    });

    function togglePresent() {
      const wrap = document.getElementById('slideDeckWrap');
      isPresenting = !isPresenting;
      wrap.classList.toggle('presenting', isPresenting);
      document.getElementById('presentBtn').textContent = isPresenting ? '⊡ Exit' : '⛶ Present';
      document.getElementById('slideDeckModal').style.padding = isPresenting ? '0' : '24px';
    }

    function exitPresent() {
      const wrap = document.getElementById('slideDeckWrap');
      isPresenting = false;
      wrap.classList.remove('presenting');
      document.getElementById('presentBtn').textContent = '⛶ Present';
      document.getElementById('slideDeckModal').style.padding = '24px';
    }

    async function generateSlides(forceNewTemplate = false) {
      // If a specific theme was already set (via selectTheme), honour it.
      // forceNewTemplate with no specific ID → cycle to next theme.
      const nextTemplateId = (forceNewTemplate && currentDeckTemplateId)
        ? currentDeckTemplateId   // selectTheme already set it
        : forceNewTemplate
          ? pickNextTemplateId(true)
          : (currentDeckTemplateId || pickNextTemplateId(false));
      document.getElementById('slideDeckLoading').style.display = 'block';
      document.getElementById('slideDeckBody').style.display = 'none';
      document.getElementById('slideNav').style.display = 'none';
      document.getElementById('slideStrip').style.display = 'none';
      document.getElementById('themePickerBar').style.display = 'none';
      document.getElementById('visualControlsBar').style.display = 'none';
      document.getElementById('presentBtn').style.display = 'none';
      document.getElementById('slidesContainer').innerHTML = '';
      document.getElementById('slideStrip').innerHTML = '';
      document.getElementById('slideDots').innerHTML = '';
      document.getElementById('slideInspector').innerHTML = '';
      slidesGenerated = false;
      currentDeckData = { title: 'Pitch Deck', subtitle: '', meta: null, slides: [], image_generation: null, generation_mode: '', generation_notice: '' };

      try {
        const res = await fetch('/slides', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            idea: currentIdea,
            context: currentContext,
            template_id: nextTemplateId,
            previous_template_id: currentDeckTemplateId || '',
            generate_images: true,
            image_model: currentDeckImageModel,
            image_options: {
              enabled: true,
              style: currentDeckImageStyle,
              coverage: currentDeckImageCoverage,
              variation_key: String(currentDeckVisualRefreshKey)
            }
          })
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || `Server error ${res.status}`);
        }

        const data = await res.json();
        if (data.error) throw new Error(data.error);
        currentDeckTemplateId = nextTemplateId;
        const deck = normalizeDeckPayload(data);
        if (!deck.slides.length) throw new Error('No slides returned');

        renderSlides(deck);
        if (forceNewTemplate) showToast(`Switched to ${deck.meta?.theme_name || 'a new style'}.`);
        slidesGenerated = true;
      } catch(err) {
        console.error('Slide generation error:', err);
        const localDeck = buildLocalDeck(nextTemplateId);
        currentDeckTemplateId = nextTemplateId;
        renderSlides(localDeck);
        slidesGenerated = true;
        showToast(forceNewTemplate
          ? `Using local deck generation · ${localDeck.meta?.theme_name || 'New style'}`
          : 'Using local deck generation from existing analysis.');
      }
    }

    function renderThemePills() {
      const pills = document.getElementById('themePills');
      if (!pills) return;
      pills.innerHTML = DECK_TEMPLATE_PRESETS.map(preset => {
        const active = preset.template_id === currentDeckTemplateId;
        return `<button class="theme-pill${active ? ' active' : ''}"
          onclick="selectTheme('${preset.template_id}')"
          title="${escapeHtml(preset.theme_name)}">
          <span class="theme-pill-dot" style="background:${escapeHtml(preset.palette.accent)};"></span>
          ${escapeHtml(preset.theme_name)}
        </button>`;
      }).join('');
    }

    async function selectTheme(templateId) {
      if (templateId === currentDeckTemplateId) return;
      currentDeckTemplateId = templateId;
      renderThemePills();
      await generateSlides(false);
    }

    function renderSlides(deck) {
      currentDeckData = deck;
      // currentDeckTemplateId is set BEFORE calling renderSlides (in generateSlides/selectTheme)
      // Don't override it from deck.meta — that locks it to whatever the server returned.
      // Just ensure we have a fallback if it's still empty.
      if (!currentDeckTemplateId) {
        currentDeckTemplateId = deck.meta?.template_id || DECK_TEMPLATE_PRESETS[0].template_id;
      }
      // Sync deck.meta so theme name badge reflects reality
      if (deck.meta) deck.meta.template_id = currentDeckTemplateId;
      currentDeckImageGeneration = deck.image_generation || null;
      currentDeckImageStyle = cleanText(deck.image_generation?.selected_style, currentDeckImageStyle || 'deck-illustration');
      currentDeckImageCoverage = cleanText(deck.image_generation?.selected_coverage, currentDeckImageCoverage || 'hero-only');
      currentDeckImageModel = cleanText(
        deck.image_generation?.selected_model || deck.image_generation?.default_model,
        currentDeckImageModel || 'lcm-dreamshaper-v7'
      );
      totalSlides = deck.slides.length;
      currentSlideIndex = 0;

      const wrap = document.getElementById('slideDeckWrap');
      const container = document.getElementById('slidesContainer');
      const strip = document.getElementById('slideStrip');
      const dots = document.getElementById('slideDots');
      container.innerHTML = '';
      strip.innerHTML = '';
      dots.innerHTML = '';
      wrap.style.setProperty('--deck-accent-ui', deck.meta?.palette?.accent || '#7DD3FC');

      // Assign per-slide layouts
      deck.slides = assignSlideLayouts(deck.slides, currentDeckTemplateId);

      deck.slides.forEach((slide, i) => {
        const slideEl = document.createElement('article');
        slideEl.className = `deck-slide template-${currentDeckTemplateId} layout-${slide.layout} variant-${slide._layoutVariant || 'split-panel'} ${i === 0 ? 'active motion-playing' : ''}`;
        slideEl.dataset.index = i;
        slideEl.dataset.entry = entryKey(slide.animation_plan.entry);
        slideEl.dataset.transition = transitionKey(slide.animation_plan.transition);
        slideEl.style.cssText = slideThemeStyle(deck.meta);
        slideEl.onclick = () => { if (isPresenting) nextSlide(); };
        slideEl.innerHTML = createSlideMarkup(slide, i, deck.slides.length);
        container.appendChild(slideEl);

        // Thumbnail strip
        const thumb = document.createElement('button');
        thumb.type = 'button';
        thumb.className = `slide-thumb template-${currentDeckTemplateId} ${i === 0 ? 'active' : ''}`;
        thumb.dataset.index = i;
        thumb.style.cssText = slideThemeStyle(deck.meta);
        thumb.onclick = () => goToSlide(i);
        thumb.innerHTML = `
          <div class="slide-thumb-inner">
            <div class="slide-thumb-kicker">${escapeHtml(slideTypeLabel(slide.type))}</div>
            <div class="slide-thumb-title">${escapeHtml(slide.title)}</div>
          </div>
          <div class="slide-thumb-num">${i + 1}</div>`;
        strip.appendChild(thumb);

        const dot = document.createElement('button');
        dot.className = `slide-dot ${i === 0 ? 'active' : ''}`;
        dot.dataset.index = i;
        dot.onclick = () => goToSlide(i);
        dots.appendChild(dot);
      });

      document.getElementById('slideDeckTitle').textContent = deck.title;
      const subtitleParts = [deck.subtitle, deck.meta.theme_name, `${deck.slides.length} slides`];
      if (deck.generation_mode === 'local') subtitleParts.push('Local fallback');
      document.getElementById('slideDeckSubtitle').textContent = subtitleParts.filter(Boolean).join(' · ');
      document.getElementById('slideDeckLoading').style.display = 'none';
      document.getElementById('slideDeckBody').style.display = 'grid';
      document.getElementById('slideNav').style.display = 'flex';
      document.getElementById('slideStrip').style.display = 'flex';
      document.getElementById('themePickerBar').style.display = 'flex'; /* theme bar always flex */
      document.getElementById('visualControlsBar').style.display = 'flex';
      document.getElementById('presentBtn').style.display = 'flex';
      renderThemePills();
      renderVisualControls();
      updateSlideNav();
    }

        function goToSlide(index) {
      currentSlideIndex = Math.max(0, Math.min(totalSlides - 1, index));
      updateSlideNav();
    }

    function updateSlideNav() {
      document.querySelectorAll('.deck-slide').forEach((slideEl, i) => {
        const isActive = i === currentSlideIndex;
        slideEl.classList.toggle('active', isActive);
        if (isActive) playSlideMotion(slideEl);
        else slideEl.classList.remove('motion-playing');
      });

      document.querySelectorAll('.slide-thumb').forEach((thumb, i) => {
        thumb.classList.toggle('active', i === currentSlideIndex);
        if (i === currentSlideIndex) thumb.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' });
      });

      document.querySelectorAll('.slide-dot').forEach((dot, i) => dot.classList.toggle('active', i === currentSlideIndex));
      document.getElementById('slideCounter').textContent = `${currentSlideIndex + 1} / ${totalSlides}`;
      document.getElementById('prevSlideBtn').disabled = currentSlideIndex === 0;
      document.getElementById('nextSlideBtn').textContent = currentSlideIndex === totalSlides - 1 ? '✓ Done' : 'Next →';
      document.getElementById('nextSlideBtn').disabled = false;
      renderInspector();
    }

    function nextSlide() {
      if (currentSlideIndex < totalSlides - 1) {
        currentSlideIndex++;
        updateSlideNav();
      } else if (!isPresenting) {
        closeSlideModalDirect();
      }
    }

    function prevSlide() {
      if (currentSlideIndex > 0) {
        currentSlideIndex--;
        updateSlideNav();
      }
    }

    function regenerateSlides() {
      // Cycle to the next theme
      currentDeckTemplateId = pickNextTemplateId(true);
      slidesGenerated = false;
      generateSlides(false);
    }

    // ── REAL SHARE REPORT (saves to backend) ──
    async function shareReport() {
      if (!currentIdea) { alert('Run VentureOS first.'); return; }
      const btn = document.getElementById('shareBtn');
      if (btn) { btn.textContent = '⏳ Saving...'; btn.disabled = true; }
      try {
        const res = await fetch('/report/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ idea: currentIdea, context: currentContext })
        });
        if (!res.ok) throw new Error('Save failed');
        const data = await res.json();
        const shareUrl = `${window.location.origin}${data.url}`;
        navigator.clipboard.writeText(shareUrl).then(() => {
          showToast(`🔗 Share link copied! ventureos.app${data.url}`);
        });
      } catch(err) {
        // Fallback: encode idea in URL param
        const shareUrl = `${window.location.origin}?idea=${encodeURIComponent(currentIdea)}`;
        navigator.clipboard.writeText(shareUrl).then(() => {
          showToast('🔗 Share link copied to clipboard!');
        });
      } finally {
        if (btn) { btn.textContent = '🔗 Share link'; btn.disabled = false; }
      }
    }

    // ── INVESTOR EMAIL — opens system mail app with real TO address ──
    function draftInvestorEmail(firmName, stage, firmEmail, partnerName) {
      const sc = currentContext.scorecard || {};
      const m = currentContext.market_research || {};
      const pitch = currentContext.pitch || {};
      const emails = pitch.emails || [];
      const baseEmail = emails[0] || {};

      const subject = encodeURIComponent(`${currentIdea.slice(0, 45)} — ${stage} Opportunity`);
      const bodyLines = [
        `Dear ${partnerName || firmName + ' team'},`,
        ``,
        `I'm reaching out because ${firmName}'s investment focus on ${stage} companies aligns closely with what we're building.`,
        ``,
        baseEmail.body
          ? baseEmail.body.replace(/\[.*?\]/g, '').trim()
          : `We're building: ${currentIdea}`,
        ``,
        `A few key metrics:`,
        `• Market opportunity: ${v(m.market_size)} TAM growing at ${v(m.growth_rate)}`,
        `• VentureOS fundability score: ${sc.total || '—'}/100 — ${sc.verdict || ''}`,
        `• Biggest strength: ${v(sc.biggest_strength)}`,
        ``,
        `I'd love to share our full deck and learn more about ${firmName}'s current focus areas.`,
        `Would you be open to a 20-minute call this week?`,
        ``,
        `Best regards,`,
        `[Your name]`,
        `[Your title]`,
        `[Your phone]`
      ];
      const body = encodeURIComponent(bodyLines.join('\n'));

      // Open email app with real TO address pre-filled
      const mailtoUrl = `mailto:${firmEmail}?subject=${subject}&body=${body}`;
      window.location.href = mailtoUrl;

      showToast(`📧 Opening email app → ${firmEmail}`);
    }

    // ── DOWNLOAD WEBSITE AS HTML FILE ──
    function downloadProtoHTML() {
      if (!protoHtml) { alert('Generate a website first.'); return; }
      const filename = currentIdea
        ? currentIdea.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40) + '-website.html'
        : 'ventureos-website.html';
      const blob = new Blob([protoHtml], { type: 'text/html;charset=utf-8' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
      showToast('⬇ Website downloaded as HTML file!');
    }

    // ── DOWNLOAD PITCH DECK AS PPTX ──
    function pptColor(value, fallback) {
      return normalizeHex(value, fallback).replace('#', '');
    }

    function pptShapeType(pptx, key, fallback) {
      return pptx?.ShapeType?.[key] || fallback;
    }

    function downloadBlobFile(blob, fileName) {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = fileName;
      a.click();
      URL.revokeObjectURL(a.href);
    }

    async function writePptxBlob(pptx, fileName, timeoutLabel = 'PPTX packaging timed out') {
      const withTimeout = (promise, ms, label) => Promise.race([
        promise,
        new Promise((_, reject) => setTimeout(() => reject(new Error(label)), ms))
      ]);
      const blob = await withTimeout(
        pptx.write({ outputType: 'blob' }),
        30000,
        timeoutLabel
      );
      downloadBlobFile(blob, fileName);
    }

    async function buildEditablePPTX(fileName) {
      const Pptx = window.PptxGenJS || window.pptxgen;
      if (!Pptx) throw new Error('PPTX library not loaded in browser');
      if (document.fonts?.ready) await document.fonts.ready;

      const pptx = new Pptx();
      pptx.layout = 'LAYOUT_WIDE';
      pptx.author = 'VentureOS';
      pptx.company = 'VentureOS';
      pptx.subject = currentDeckData.subtitle || 'Premium investor deck';
      pptx.title = currentDeckData.title || currentIdea || 'Pitch Deck';

      const rectShape = pptShapeType(pptx, 'rect', 'rect');
      const roundRectShape = pptShapeType(pptx, 'roundRect', 'roundRect');
      const ellipseShape = pptShapeType(pptx, 'ellipse', 'ellipse');
      const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
      const slideEls = Array.from(document.querySelectorAll('.deck-slide'));
      if (!slideEls.length) throw new Error('No rendered slides to export');

      const cssColorInfo = (value, fallback = '#FFFFFF') => {
        const raw = cleanText(value);
        if (!raw) return { color: pptColor(fallback, '#FFFFFF'), transparency: 0 };
        if (raw.startsWith('#')) {
          return { color: pptColor(raw, fallback), transparency: 0 };
        }
        const match = raw.match(/rgba?\(([^)]+)\)/i);
        if (!match) return { color: pptColor(fallback, '#FFFFFF'), transparency: 0 };
        const parts = match[1].split(',').map(part => part.trim());
        const r = Number.parseFloat(parts[0] || '255');
        const g = Number.parseFloat(parts[1] || '255');
        const b = Number.parseFloat(parts[2] || '255');
        const a = parts.length > 3 ? Number.parseFloat(parts[3] || '1') : 1;
        const hex = `#${[r, g, b].map(num => Math.max(0, Math.min(255, Math.round(num))).toString(16).padStart(2, '0')).join('')}`;
        return {
          color: pptColor(hex, fallback),
          transparency: Math.max(0, Math.min(100, Math.round((1 - Math.max(0, Math.min(1, a))) * 100)))
        };
      };

      const cssFontFace = (fontFamily, fallback = 'Aptos') => {
        const family = cleanText(fontFamily);
        if (!family) return fallback;
        if (family.toLowerCase().includes('instrument serif')) return 'Georgia';
        if (family.toLowerCase().includes('geist')) return 'Aptos';
        return family.split(',')[0].replace(/['"]/g, '').trim() || fallback;
      };

      const pxToPt = px => Math.max(7, Number(((Number.parseFloat(px) || 12) * 0.75).toFixed(1)));

      const boxForNode = (node, slideRect) => {
        if (!node) return null;
        const rect = node.getBoundingClientRect();
        if (!rect.width || !rect.height) return null;
        return {
          x: Number((((rect.left - slideRect.left) / slideRect.width) * 13.33).toFixed(3)),
          y: Number((((rect.top - slideRect.top) / slideRect.height) * 7.5).toFixed(3)),
          w: Number(((rect.width / slideRect.width) * 13.33).toFixed(3)),
          h: Number(((rect.height / slideRect.height) * 7.5).toFixed(3))
        };
      };

      const addTextFromNode = (slide, node, slideRect, textOverride = '', options = {}) => {
        const box = boxForNode(node, slideRect);
        if (!box) return;
        const textValue = cleanText(textOverride || node.textContent);
        if (!textValue) return;
        const style = getComputedStyle(node);
        const color = cssColorInfo(style.color, '#F8FAFC');
        slide.addText(textValue, {
          x: box.x,
          y: box.y,
          w: box.w,
          h: box.h,
          margin: 0,
          fit: 'shrink',
          breakLine: true,
          fontFace: cssFontFace(style.fontFamily, 'Aptos'),
          fontSize: pxToPt(style.fontSize),
          bold: style.fontWeight === 'bold' || Number.parseInt(style.fontWeight, 10) >= 600,
          color: color.color,
          transparency: color.transparency,
          align: ['center', 'right', 'justify'].includes(style.textAlign) ? style.textAlign : 'left',
          valign: 'top',
          ...options
        });
      };

      const addShapeFromNode = (slide, node, slideRect, options = {}) => {
        const box = boxForNode(node, slideRect);
        if (!box) return;
        const style = getComputedStyle(node);
        const fill = options.fill || cssColorInfo(style.backgroundColor, '#FFFFFF');
        const line = options.line || cssColorInfo(style.borderTopColor, fill.color);
        slide.addShape(options.shape || roundRectShape, {
          x: box.x,
          y: box.y,
          w: box.w,
          h: box.h,
          radius: options.radius,
          fill: {
            color: fill.color,
            transparency: fill.transparency ?? 0
          },
          line: {
            color: line.color,
            transparency: line.transparency ?? 0,
            width: options.lineWidth ?? Math.max(0.6, Number.parseFloat(style.borderTopWidth || '1'))
          }
        });
      };

      const imageDataCache = new Map();
      const urlToDataUrl = async url => {
        if (imageDataCache.has(url)) return imageDataCache.get(url);
        const pending = (async () => {
          const response = await fetch(url);
          if (!response.ok) throw new Error(`Failed to load image: ${url}`);
          const blob = await response.blob();
          return await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.onerror = () => reject(new Error(`Failed to read image: ${url}`));
            reader.readAsDataURL(blob);
          });
        })();
        imageDataCache.set(url, pending);
        return pending;
      };

      const waitForImageNode = async node => {
        if (!node || node.tagName !== 'IMG') return;
        if (node.complete && node.naturalWidth > 0) return;
        await Promise.race([
          new Promise((resolve, reject) => {
            const handleLoad = () => {
              node.removeEventListener('load', handleLoad);
              node.removeEventListener('error', handleError);
              resolve();
            };
            const handleError = () => {
              node.removeEventListener('load', handleLoad);
              node.removeEventListener('error', handleError);
              reject(new Error(`Failed to load image node: ${node.currentSrc || node.src || 'unknown source'}`));
            };
            node.addEventListener('load', handleLoad, { once: true });
            node.addEventListener('error', handleError, { once: true });
          }),
          delay(6000)
        ]);
      };

      const addImageFromNode = async (slide, node, slideRect, options = {}) => {
        const box = options.box || boxForNode(node, slideRect);
        if (!box) return;
        const src = cleanText(options.src || node?.getAttribute?.('src'));
        if (!src) return;
        const absoluteSrc = src.startsWith('data:') ? src : new URL(src, window.location.origin).href;
        const data = absoluteSrc.startsWith('data:') ? absoluteSrc : await urlToDataUrl(absoluteSrc);
        slide.addImage({
          data,
          x: box.x,
          y: box.y,
          w: box.w,
          h: box.h
        });
      };

      const showAllMotion = slideEl => {
        const items = Array.from(slideEl.querySelectorAll('.motion-item'));
        items.forEach(item => {
          item.dataset.exportOpacity = item.style.opacity;
          item.dataset.exportTransform = item.style.transform;
          item.dataset.exportAnimation = item.style.animation;
          item.style.opacity = '1';
          item.style.transform = 'none';
          item.style.animation = 'none';
        });
      };

      const clearAllMotion = slideEl => {
        const items = Array.from(slideEl.querySelectorAll('.motion-item'));
        items.forEach(item => {
          item.style.opacity = item.dataset.exportOpacity || '';
          item.style.transform = item.dataset.exportTransform || '';
          item.style.animation = item.dataset.exportAnimation || '';
          delete item.dataset.exportOpacity;
          delete item.dataset.exportTransform;
          delete item.dataset.exportAnimation;
        });
      };

      const originalIndex = currentSlideIndex;

      try {
        for (let index = 0; index < currentDeckData.slides.length; index++) {
          showToast(`⏳ Building editable slide ${index + 1} of ${currentDeckData.slides.length}...`);
          goToSlide(index);
          await delay(100);

          const slideEl = slideEls[index];
          const slideRect = slideEl.getBoundingClientRect();
          if (!slideRect.width || !slideRect.height) throw new Error(`Slide ${index + 1} is not renderable yet`);
          showAllMotion(slideEl);

          const slide = pptx.addSlide();
          const meta = currentDeckData.meta || {};
          const palette = meta.palette || {};
          const templateId = meta.template_id || '';
          const primary = pptColor(palette.primary, '#0B1020');
          const secondary = pptColor(palette.secondary, '#182033');
          const surface = pptColor(palette.surface, '#121A2B');
          const accent = pptColor(palette.accent, '#7DD3FC');
          const text = pptColor(palette.text, '#F8FAFC');
          const isLightTheme = templateId === 'boardroom-ivory';
          const panelFill = isLightTheme ? { color: 'FFFFFF', transparency: 10 } : { color: surface, transparency: 18 };
          const panelLine = isLightTheme ? { color: 'D9E2EC', transparency: 28 } : { color: text, transparency: 58 };

          slide.background = { color: primary };
          slide.addShape(ellipseShape, {
            x: 9.05, y: -0.65, w: 4.55, h: 4.55,
            fill: { color: accent, transparency: isLightTheme ? 86 : 84 },
            line: { color: accent, transparency: 100, width: 0 }
          });
          slide.addShape(ellipseShape, {
            x: 8.6, y: 4.05, w: 5.05, h: 5.05,
            fill: { color: accent, transparency: isLightTheme ? 92 : 91 },
            line: { color: accent, transparency: 100, width: 0 }
          });
          slide.addShape(rectShape, {
            x: 8.08, y: 0.78, w: 3.38, h: 0.018,
            fill: { color: text, transparency: isLightTheme ? 78 : 64 },
            line: { color: text, transparency: 100, width: 0 }
          });

          const kicker = slideEl.querySelector('.slide-kicker');
          if (kicker) addShapeFromNode(slide, kicker, slideRect);
          const noteChip = slideEl.querySelector('.slide-note-chip');
          if (noteChip) addShapeFromNode(slide, noteChip, slideRect);
          const visualPanel = slideEl.querySelector('.slide-visual-panel');
          if (visualPanel) addShapeFromNode(slide, visualPanel, slideRect, { fill: panelFill, line: panelLine, lineWidth: 1.1 });
          slideEl.querySelectorAll('.slide-feature-media').forEach(node => addShapeFromNode(slide, node, slideRect, { fill: panelFill, line: panelLine, lineWidth: 1.1 }));
          slideEl.querySelectorAll('.slide-stat-card').forEach(node => addShapeFromNode(slide, node, slideRect, { fill: panelFill, line: panelLine, lineWidth: 1.05 }));
          slideEl.querySelectorAll('.slide-insight-card').forEach(node => addShapeFromNode(slide, node, slideRect, { fill: panelFill, line: panelLine, lineWidth: 1.05 }));
          slideEl.querySelectorAll('.slide-roadmap-item').forEach(node => addShapeFromNode(slide, node, slideRect, { fill: panelFill, line: panelLine, lineWidth: 1.05 }));
          slideEl.querySelectorAll('.slide-roadmap-step').forEach(node => addShapeFromNode(slide, node, slideRect, {
            fill: cssColorInfo(getComputedStyle(node).backgroundColor, `#${accent}`),
            line: cssColorInfo(getComputedStyle(node).borderTopColor, `#${accent}`),
            lineWidth: 1
          }));

          const kickerDot = slideEl.querySelector('.slide-kicker-dot');
          if (kickerDot) {
            const dotBox = boxForNode(kickerDot, slideRect);
            if (dotBox) {
              slide.addShape(ellipseShape, {
                x: dotBox.x, y: dotBox.y, w: dotBox.w, h: dotBox.h,
                fill: { color: accent, transparency: 0 },
                line: { color: accent, transparency: 100, width: 0 }
              });
            }
          }

          const orbit = slideEl.querySelector('.slide-visual-orbit');
          if (orbit) {
            const orbitBox = boxForNode(orbit, slideRect);
            if (orbitBox) {
              slide.addShape(ellipseShape, {
                x: orbitBox.x, y: orbitBox.y, w: orbitBox.w, h: orbitBox.h,
                fill: { color: accent, transparency: isLightTheme ? 72 : 64 },
                line: { color: accent, transparency: 100, width: 0 }
              });
              slide.addShape(ellipseShape, {
                x: orbitBox.x + orbitBox.w * 0.19, y: orbitBox.y + orbitBox.h * 0.19,
                w: orbitBox.w * 0.62, h: orbitBox.h * 0.62,
                fill: { color: accent, transparency: 100 },
                line: { color: panelLine.color, transparency: 68, width: 1 }
              });
              slide.addShape(ellipseShape, {
                x: orbitBox.x + orbitBox.w * 0.07, y: orbitBox.y + orbitBox.h * 0.07,
                w: orbitBox.w * 0.86, h: orbitBox.h * 0.86,
                fill: { color: accent, transparency: 100 },
                line: { color: panelLine.color, transparency: 82, width: 1 }
              });
            }
          }

          const slideData = currentDeckData.slides[index] || {};
          const imagePlacements = [];
          const seenImageSrc = new Set();

          slideEl.querySelectorAll('.slide-feature-media, .slide-visual-media').forEach(host => {
            const imageNode = host.querySelector('.slide-generated-image');
            const hostSrc = cleanText(imageNode?.getAttribute('src'));
            if (!hostSrc) return;
            const normalizedSrc = hostSrc.startsWith('data:') ? hostSrc : new URL(hostSrc, window.location.origin).href;
            if (seenImageSrc.has(normalizedSrc)) return;
            seenImageSrc.add(normalizedSrc);
            imagePlacements.push({ host, imageNode, src: hostSrc });
          });

          if (!imagePlacements.length && slideData.image_url) {
            const fallbackHost = slideEl.querySelector('.slide-feature-media, .slide-visual-media');
            if (fallbackHost) {
              imagePlacements.push({ host: fallbackHost, imageNode: null, src: slideData.image_url });
            }
          }

          for (const placement of imagePlacements) {
            try {
              await waitForImageNode(placement.imageNode);
              await addImageFromNode(slide, placement.host, slideRect, { src: placement.src });
            } catch (imageError) {
              console.warn('Skipping PPT image export for slide', index + 1, imageError);
            }
          }

          addTextFromNode(slide, kicker, slideRect, kicker?.textContent);
          addTextFromNode(slide, slideEl.querySelector('.slide-top-meta'), slideRect);
          addTextFromNode(slide, noteChip, slideRect, noteChip?.textContent);
          addTextFromNode(slide, slideEl.querySelector('.slide-title'), slideRect);
          addTextFromNode(slide, slideEl.querySelector('.slide-subtitle'), slideRect);
          addTextFromNode(slide, slideEl.querySelector('.slide-footer-copy'), slideRect);
          addTextFromNode(slide, slideEl.querySelector('.slide-brand'), slideRect);
          addTextFromNode(slide, slideEl.querySelector('.slide-slide-number'), slideRect);

          slideEl.querySelectorAll('.slide-copy-item').forEach(item => {
            const bullet = item.querySelector('.slide-copy-bullet');
            const copy = item.lastElementChild;
            if (bullet) {
              const bulletBox = boxForNode(bullet, slideRect);
              const bulletStyle = getComputedStyle(bullet);
              const fill = cssColorInfo(bulletStyle.backgroundColor, `#${accent}`);
              const line = cssColorInfo(bulletStyle.borderTopColor, `#${accent}`);
              if (bulletBox) {
                slide.addShape(ellipseShape, {
                  x: bulletBox.x, y: bulletBox.y, w: bulletBox.w, h: bulletBox.h,
                  fill: { color: fill.color, transparency: fill.transparency },
                  line: { color: line.color, transparency: line.transparency, width: 1 }
                });
                addTextFromNode(slide, bullet, slideRect, bullet.textContent, { align: 'center', valign: 'mid' });
              }
            }
            if (copy) addTextFromNode(slide, copy, slideRect);
          });

          slideEl.querySelectorAll('.slide-stat-value, .slide-stat-label, .slide-roadmap-copy, .slide-insight-copy').forEach(node => {
            addTextFromNode(slide, node, slideRect);
          });
          slideEl.querySelectorAll('.slide-roadmap-step').forEach(node => {
            addTextFromNode(slide, node, slideRect, node.textContent, { align: 'center', valign: 'mid' });
          });
        }
      } finally {
        slideEls.forEach(clearAllMotion);
        goToSlide(originalIndex);
      }

      showToast('⏳ Finalizing editable PPTX...');
      await writePptxBlob(pptx, fileName, 'Editable PPTX packaging timed out');
    }

    async function buildClientPPTX(fileName) {
      const Pptx = window.PptxGenJS || window.pptxgen;
      if (!Pptx) throw new Error('PPTX library not loaded in browser');
      const captureLib = window.html2canvas;
      if (!captureLib) throw new Error('Slide capture library not loaded');
      if (document.fonts?.ready) await document.fonts.ready;

      const pptx = new Pptx();
      pptx.layout = 'LAYOUT_WIDE';
      pptx.author = 'VentureOS';
      pptx.company = 'VentureOS';
      pptx.subject = currentDeckData.subtitle || 'Premium investor deck';
      pptx.title = currentDeckData.title || currentIdea || 'Pitch Deck';
      const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
      const slideEls = Array.from(document.querySelectorAll('.deck-slide'));
      if (!slideEls.length) throw new Error('No rendered slides to capture');
      const captureScale = 2;
      const withTimeout = (promise, ms, label) => Promise.race([
        promise,
        new Promise((_, reject) => setTimeout(() => reject(new Error(label)), ms))
      ]);

      function applyCaptureState(slideEl, revealCount) {
        slideEl.classList.add('active');
        slideEl.classList.remove('motion-playing');
        const items = Array.from(slideEl.querySelectorAll('.motion-item'));
        items.forEach((item, index) => {
          item.style.animation = 'none';
          item.style.opacity = index < revealCount ? '1' : '0';
          item.style.transform = 'translateY(0) scale(1)';
        });
      }

      function clearCaptureState(slideEl) {
        const items = Array.from(slideEl.querySelectorAll('.motion-item'));
        items.forEach(item => {
          item.style.animation = '';
          item.style.opacity = '';
          item.style.transform = '';
        });
      }

      const originalIndex = currentSlideIndex;
      document.body.classList.add('capture-export');

      try {
        for (let logicalIndex = 0; logicalIndex < currentDeckData.slides.length; logicalIndex++) {
          showToast(`⏳ Capturing slide ${logicalIndex + 1} of ${currentDeckData.slides.length}...`);
          goToSlide(logicalIndex);
          await delay(80);
          const slideEl = slideEls[logicalIndex];
          const rect = slideEl.getBoundingClientRect();
          if (!rect.width || !rect.height) {
            throw new Error(`Slide ${logicalIndex + 1} is not renderable yet`);
          }
          applyCaptureState(slideEl, 99);
          await delay(40);
          const canvas = await withTimeout(captureLib(slideEl, {
            backgroundColor: null,
            scale: captureScale,
            useCORS: true,
            logging: false,
            removeContainer: true,
            width: Math.round(rect.width),
            height: Math.round(rect.height),
            windowWidth: Math.ceil(rect.width),
            windowHeight: Math.ceil(rect.height),
            scrollX: 0,
            scrollY: -window.scrollY,
            ignoreElements: element => {
              if (!element || typeof element.tagName !== 'string') return false;
              const tag = element.tagName.toUpperCase();
              if (tag === 'IFRAME' || tag === 'VIDEO') return true;
              if (tag === 'CANVAS' && (!element.width || !element.height)) return true;
              return element.classList?.contains('toast') || element.id === 'protoIframe';
            },
            onclone: clonedDoc => {
              clonedDoc.body.classList.add('capture-export');
              clonedDoc.querySelectorAll('iframe, video').forEach(node => node.remove());
              clonedDoc.querySelectorAll('canvas').forEach(node => {
                if (!node.width || !node.height) node.remove();
              });
            }
          }), 20000, `Capture timed out on slide ${logicalIndex + 1}`);
          const imageData = canvas.toDataURL('image/png');
          const slide = pptx.addSlide();
          slide.addImage({ data: imageData, x: 0, y: 0, w: 13.33, h: 7.5 });
          clearCaptureState(slideEl);
        }
      } finally {
        slideEls.forEach(clearCaptureState);
        document.body.classList.remove('capture-export');
        goToSlide(originalIndex);
      }

      showToast('⏳ Finalizing PPTX...');
      const blob = await withTimeout(
        pptx.write({ outputType: 'blob' }),
        30000,
        'PPTX packaging timed out'
      );
      downloadBlobFile(blob, fileName);
    }

    async function downloadPPTX() {
      if (!slidesGenerated || !currentDeckData.slides.length) { showToast('Generate slides first, then download PPTX.'); return; }
      showToast('⏳ Building editable PPTX...');

      try {
        const fname = (currentIdea || 'ventureos').toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40) + '-pitch-deck.pptx';
        await buildEditablePPTX(fname);
        showToast('⬇ Editable PPTX downloaded!');

      } catch(err) {
        console.error('Editable PPTX export error:', err);
        const message = cleanText(err?.message, 'Editable PPTX export failed.');
        showToast(`❌ Editable PPTX export failed: ${message}`);
        alert(`Editable PPTX export failed.\n\n${message}`);
      }
    }

    // Override openGamma to use in-page slides
    function openGamma() { openSlideModal(); }
  