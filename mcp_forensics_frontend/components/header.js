// JARVIS:LAW Forensic Analysis System - Header Component
// PowerShell Compatible: YES (No emojis or special characters)

class CustomHeader extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        
        .header {
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          padding: 1rem 0;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
          border-bottom: 1px solid #2d3748;
        }
        
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 2rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        
        .logo {
          display: flex;
          align-items: center;
        }
        
        .logo-text {
          font-size: 1.8rem;
          font-weight: 700;
          background: linear-gradient(90deg, #00ff41, #00aaff);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-right: 1rem;
        }
        
        .subtitle {
          font-size: 0.9rem;
          color: #a0aec0;
        }
        
        .modules-status {
          display: flex;
          align-items: center;
          background: rgba(0, 255, 65, 0.1);
          padding: 0.5rem 1rem;
          border-radius: 9999px;
          border: 1px solid rgba(0, 255, 65, 0.3);
        }
        
        .status-indicator {
          width: 10px;
          height: 10px;
          background-color: #00ff41;
          border-radius: 50%;
          margin-right: 0.5rem;
          box-shadow: 0 0 8px #00ff41;
        }
        
        @media (max-width: 768px) {
          .container {
            flex-direction: column;
            text-align: center;
          }
          
          .logo {
            margin-bottom: 0.5rem;
          }
          
          .modules-status {
            margin-top: 0.5rem;
          }
        }
      </style>
      
      <header class="header">
        <div class="container">
          <div class="logo">
            <div class="logo-text">JARVIS:LAW</div>
            <div class="subtitle">SEC Forensic Analysis System - All Modules Operational</div>
          </div>
          <div class="modules-status">
            <div class="status-indicator"></div>
            <span>All enhancement modules loaded</span>
          </div>
        </div>
      </header>
    `;
  }
}

customElements.define('custom-header', CustomHeader);

