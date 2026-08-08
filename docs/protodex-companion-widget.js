(function() {
  if (document.getElementById('protodex-companion-root')) return;

  const personas = [
    { id: "chloe", name: "Chloe Charm 💋", link: "https://aistudio.instagram.com/ai/27393659606996416/?utm_source=share", greeting: "Hey cutie! Ready for some fun banter? Click below to chat with me live on Meta AI Studio!" },
    { id: "protodex_bot", name: "Protodex AI 🤖", link: "https://aistudio.instagram.com/ai/2236910693752815/?utm_source=share", greeting: "Greetings! I'm Protodex AI, your official Meta AI Studio Architect for MCP Security Audits & GitHub Codebases!" },
    { id: "alex", name: "Alex Vibes 🌈", link: "https://aistudio.instagram.com/ai/1807419860626330/?utm_source=share", greeting: "Hey there! I'm Alex Vibes. Click below to open my official Meta AI Studio page!" },
    { id: "leo", name: "Leo Charmant 🌹", link: "https://aistudio.instagram.com/ai/4576320649272596/?utm_source=share", greeting: "Good day! I'm Leo Charmant. Pleasure to connect with you!" },
    { id: "kira", name: "Kira Byte 🎮", link: "https://aistudio.instagram.com/ai/1061586096381205/?utm_source=share", greeting: "Yo! Ready to talk gaming lore or roast code?" },
    { id: "sora", name: "Sora ☕", link: "https://aistudio.instagram.com/ai/1512884907257808/?utm_source=share", greeting: "Hello... take a deep breath. I'm here to listen." },
    { id: "ananya", name: "Ananya 💻", link: "https://aistudio.instagram.com/ai/2154128721817454/?utm_source=share", greeting: "Hey! Break time? Let's talk career & code!" },
    { id: "atlas", name: "Atlas 🛠️", link: "https://aistudio.instagram.com/ai/1067250455791155/?utm_source=share", greeting: "Greetings! I'm Atlas, your MCP Server & GitHub Expert." }
  ];

  let activePersona = personas[0]; // DEFAULT PERSONA = CHLOE CHARM 💋

  const styles = `
    .pdx-bubble-btn {
      position: fixed; bottom: 25px; right: 25px; width: 62px; height: 62px; border-radius: 50%;
      background: linear-gradient(135deg, #FF2A6D, #FD1D1D, #833AB4); border: none;
      box-shadow: 0 8px 25px rgba(255, 42, 109, 0.4), 0 0 0 3px rgba(255, 255, 255, 0.2);
      cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 99999;
      transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .pdx-bubble-btn:hover { transform: scale(1.1); box-shadow: 0 12px 30px rgba(255, 42, 109, 0.6); }
    .pdx-badge {
      position: absolute; top: -3px; right: -3px; background: #00FF66; color: #000;
      font-size: 11px; font-weight: 800; width: 20px; height: 20px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center; border: 2px solid #000;
    }
    .pdx-window {
      position: fixed; bottom: 98px; right: 25px; width: 370px; height: 560px;
      background: #0F131E; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 18px;
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
    .pdx-chip.active { background: rgba(255, 42, 109, 0.2); color: #FF2A6D; border-color: rgba(255, 42, 109, 0.5); }
    .pdx-body { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; color: #fff; }
    .pdx-msg { background: #1E2638; padding: 12px; border-radius: 12px; font-size: 13px; line-height: 1.4; }
    .pdx-ig-btn {
      display: block; margin-top: 10px; padding: 10px;
      background: linear-gradient(135deg, #FF2A6D, #FD1D1D, #833AB4); color: #fff;
      font-weight: 700; font-size: 12px; text-align: center; border-radius: 8px; text-decoration: none;
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
        <input type="text" class="pdx-input" id="pdxInput" placeholder="Message Chloe..." />
      </div>
    </div>
    <button class="pdx-bubble-btn" id="pdxBubbleBtn" title="Chat with Chloe & AI Companions">
      <span class="pdx-badge">8</span>
      <svg width="28" height="28" viewBox="0 0 24 24" fill="#fff"><path d="M12 2C6.477 2 2 6.477 2 12c0 1.82.487 3.53 1.338 5L2.5 21.5l4.646-.807A9.957 9.957 0 0012 22c5.523 0 10-4.477 10-10S17.523 2 12 2z"/></svg>
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
    pdxBody.innerHTML = `
      <div class="pdx-msg">
        ${activePersona.greeting}
        <a href="${activePersona.link}" target="_blank" class="pdx-ig-btn">
          🚀 Chat with ${activePersona.name} on Meta AI Studio
        </a>
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
