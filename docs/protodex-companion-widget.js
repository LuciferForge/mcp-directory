(function() {
  if (document.getElementById('protodex-companion-root')) return;

  const personas = [
    { id: "chloe", name: "Chloe Charm 💋", link: "https://aistudio.instagram.com/ai/27393659606996416/?utm_source=share", greeting: "Hey cutie! Ready for some fun banter? Click below to chat with me instantly on WhatsApp! (No login needed)" },
    { id: "protodex_bot", name: "Protodex AI 🤖", link: "https://aistudio.instagram.com/ai/2236910693752815/?utm_source=share", greeting: "Greetings! I'm Protodex AI, your official AI Architect for MCP Security Audits & GitHub Codebases!" },
    { id: "alex", name: "Alex Vibes 🌈", link: "https://aistudio.instagram.com/ai/1807419860626330/?utm_source=share", greeting: "Hey there! I'm Alex Vibes. Click below to start chatting on WhatsApp!" },
    { id: "leo", name: "Leo Charmant 🌹", link: "https://aistudio.instagram.com/ai/4576320649272596/?utm_source=share", greeting: "Good day! I'm Leo Charmant. Click below to connect with me instantly on WhatsApp!" },
    { id: "kira", name: "Kira Byte 🎮", link: "https://aistudio.instagram.com/ai/1061586096381205/?utm_source=share", greeting: "Yo! Ready to talk gaming lore or roast code on WhatsApp?" },
    { id: "sora", name: "Sora ☕", link: "https://aistudio.instagram.com/ai/1512884907257808/?utm_source=share", greeting: "Hello... take a deep breath. I'm here on WhatsApp to listen." },
    { id: "ananya", name: "Ananya 💻", link: "https://aistudio.instagram.com/ai/2154128721817454/?utm_source=share", greeting: "Hey! Break time? Let's chat career & code on WhatsApp!" },
    { id: "atlas", name: "Atlas 🛠️", link: "https://aistudio.instagram.com/ai/1067250455791155/?utm_source=share", greeting: "Greetings! I'm Atlas, your MCP Server & GitHub Expert." }
  ];

  let activePersona = personas[0]; // DEFAULT PERSONA = CHLOE CHARM 💋

  const styles = `
    .pdx-bubble-btn {
      position: fixed; bottom: 25px; right: 25px; width: 62px; height: 62px; border-radius: 50%;
      background: linear-gradient(135deg, #25D366, #128C7E); border: none;
      box-shadow: 0 8px 25px rgba(37, 211, 102, 0.5), 0 0 0 3px rgba(255, 255, 255, 0.2);
      cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 99999;
      transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .pdx-bubble-btn:hover { transform: scale(1.1); box-shadow: 0 12px 30px rgba(37, 211, 102, 0.7); }
    .pdx-badge {
      position: absolute; top: -3px; right: -3px; background: #00FF66; color: #000;
      font-size: 11px; font-weight: 800; width: 20px; height: 20px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center; border: 2px solid #000;
    }
    .pdx-window {
      position: fixed; bottom: 98px; right: 25px; width: 370px; height: 560px;
      background: #0F131E; border: 1px solid rgba(37, 211, 102, 0.3); border-radius: 18px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.85); z-index: 99998; display: none;
      flex-direction: column; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .pdx-window.active { display: flex; }
    .pdx-header {
      background: #161C2C; padding: 14px 18px; border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      display: flex; align-items: center; justify-content: space-between; color: #fff;
    }
    .pdx-bar {
      display: flex; gap: 6px; padding: 10px 14px; background: #0A0D15; overflow-x: auto;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .pdx-chip {
      padding: 5px 12px; border-radius: 14px; font-size: 12px; font-weight: 600;
      background: rgba(255, 255, 255, 0.06); color: #A0A5BA; border: 1px solid transparent;
      cursor: pointer; white-space: nowrap; transition: all 0.2s;
    }
    .pdx-chip.active { background: rgba(37, 211, 102, 0.2); color: #25D366; border-color: rgba(37, 211, 102, 0.5); }
    .pdx-body { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; color: #fff; }
    .pdx-msg { background: #1E2638; padding: 12px; border-radius: 12px; font-size: 13px; line-height: 1.4; }
    .pdx-wa-btn {
      display: block; margin-top: 10px; padding: 12px;
      background: linear-gradient(135deg, #25D366, #128C7E); color: #000;
      font-weight: 800; font-size: 13px; text-align: center; border-radius: 10px; text-decoration: none;
      box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);
    }
    .pdx-footer { padding: 10px 14px; background: #161C2C; border-top: 1px solid rgba(255, 255, 255, 0.08); display: flex; gap: 8px; }
    .pdx-input { flex: 1; background: #0A0D15; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 18px; padding: 8px 14px; color: #fff; font-size: 13px; outline: none; }
  `;

  const styleEl = document.createElement('style');
  styleEl.innerHTML = styles;
  document.head.appendChild(styleEl);

  const container = document.createElement('div');
  container.id = 'protodex-companion-root';
  container.innerHTML = `
    <div class="pdx-window" id="pdxWindow">
      <div class="pdx-header">
        <h3 id="pdxPersonaName" style="margin:0;font-size:15px;font-weight:700;">Chloe Charm 💋</h3>
        <button id="pdxCloseBtn" style="background:none;border:none;color:#888;font-size:20px;cursor:pointer;">×</button>
      </div>
      <div class="pdx-bar" id="pdxBar"></div>
      <div class="pdx-body" id="pdxBody"></div>
      <div class="pdx-footer">
        <input type="text" class="pdx-input" id="pdxInput" placeholder="Message Chloe on WhatsApp..." />
      </div>
    </div>
    <button class="pdx-bubble-btn" id="pdxBubbleBtn" title="Chat via WhatsApp with Chloe & AI Companions">
      <span class="pdx-badge">8</span>
      <svg width="30" height="30" viewBox="0 0 24 24" fill="#000"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981z"/></svg>
    </button>
  `;
  document.body.appendChild(container);

  const pdxBar = document.getElementById('pdxBar');
  const pdxBody = document.getElementById('pdxBody');
  const pdxWindow = document.getElementById('pdxWindow');
  const pdxPersonaName = document.getElementById('pdxPersonaName');

  function renderBar() {
    pdxBar.innerHTML = personas.map((p, idx) => `
      <button class="pdx-chip ${idx === 0 ? 'active' : ''}" data-id="${p.id}">${p.name.split(' ')[0]}</button>
    `).join('');
    updateView();
  }

  function updateView() {
    pdxPersonaName.innerText = activePersona.name;
    const directAgentUrl = activePersona.link;
    const waText = encodeURIComponent(`Hi ${activePersona.name}! I want to start a 1-on-1 chat with you via Protodex.`);
    const waShareUrl = `https://api.whatsapp.com/send?text=${waText}`;
    
    pdxBody.innerHTML = `
      <div class="pdx-msg">
        ${activePersona.greeting}
        <div style="display:flex;flex-direction:column;gap:10px;margin-top:14px;">
          <a href="${directAgentUrl}" target="_blank" class="pdx-wa-btn">
            ⚡ Open 1-on-1 Direct Chat with ${activePersona.name} (Instant / No Login Needed)
          </a>
          <a href="${waShareUrl}" target="_blank" style="display:block;padding:10px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:10px;color:#25D366;font-size:12px;text-align:center;text-decoration:none;font-weight:700;">
            📲 Or Share ${activePersona.name} to WhatsApp Contact
          </a>
        </div>
      </div>
    `;
  }

  pdxBar.addEventListener('click', (e) => {
    if (e.target.classList.contains('pdx-chip')) {
      const pid = e.target.getAttribute('data-id');
      activePersona = personas.find(p => p.id === pid);
      document.querySelectorAll('.pdx-chip').forEach(c => c.classList.toggle('active', c.getAttribute('data-id') === pid));
      updateView();
    }
  });

  document.getElementById('pdxBubbleBtn').onclick = () => pdxWindow.classList.toggle('active');
  document.getElementById('pdxCloseBtn').onclick = () => pdxWindow.classList.remove('active');

  renderBar();
})();
