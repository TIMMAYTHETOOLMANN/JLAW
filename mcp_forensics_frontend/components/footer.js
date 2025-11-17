// JARVIS:LAW Forensic Analysis System - Footer Component
// PowerShell Compatible: YES (No emojis or special characters)

class CustomFooter extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          margin-top: 3rem;
        }
        
        .footer {
          background: #1a1a2e;
          border-top: 1px solid #2d3748;
          padding: 2rem 0;
        }
        
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 2rem;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        
        .logo {
          font-size: 1.5rem;
          font-weight: 700;
          background: linear-gradient(90deg, #00ff41, #00aaff);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-bottom: 1rem;
        }
        
        .version {
          color: #a0aec0;
          font-size: 0.9rem;
          margin-bottom: 1rem;
        }
        
        .disclaimer {
          color: #718096;
          font-size: 0.8rem;
          text-align: center;
          max-width: 600px;
          line-height: 1.5;
        }
        
        .separator {
          width: 50px;
          height: 2px;
          background: linear-gradient(90deg, #00ff41, #00aaff);
          margin: 1.5rem 0;
        }
      </style>
      
      <footer class="footer">
        <div class="container">
          <div class="logo">JARVIS:LAW</div>
          <div class="version">Forensic Analysis System v2.5</div>
          <div class="separator"></div>
          <div class="disclaimer">
            This system is designed for educational and research purposes only. 
            It should not be used as the sole basis for investment decisions. 
            Historical performance does not guarantee future results.
          </div>
        </div>
      </footer>
    `;
  }
}

customElements.define('custom-footer', CustomFooter);

