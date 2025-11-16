/**
 * JARVIS:LAW Custom Footer Web Component
 * For use in HTML reports and web-based interfaces
 */

class CustomFooter extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          margin-top: 2rem;
        }
        footer {
          background-color: #18181b; /* zinc-900 */
          border-top: 1px solid #3f3f46; /* zinc-700 */
          padding: 1.5rem 0;
          text-align: center;
          color: #a1a1aa; /* zinc-400 */
          font-size: 0.875rem;
        }
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 1rem;
        }
        .links {
          display: flex;
          justify-content: center;
          gap: 1.5rem;
          margin-bottom: 1rem;
          flex-wrap: wrap;
        }
        .links a {
          color: #d4d4d8; /* zinc-300 */
          text-decoration: none;
          transition: color 0.2s;
        }
        .links a:hover {
          color: #fbbf24; /* amber-400 */
        }
        .version {
          margin-top: 0.5rem;
          font-size: 0.75rem;
          opacity: 0.8;
        }
      </style>
      <footer>
        <div class="container">
          <div class="links">
            <a href="#" onclick="window.open('GUI_CONSOLIDATED_README.md', '_blank')">Documentation</a>
            <a href="#" onclick="alert('API Reference - Coming Soon')">API Reference</a>
            <a href="#" onclick="alert('Support: Contact your system administrator')">Support</a>
            <a href="#" onclick="alert('Privacy Policy - All data processed locally')">Privacy Policy</a>
          </div>
          <p>© 2025 JARVIS:LAW Forensic Analysis System. All rights reserved.</p>
          <p>Leveraging SEC EDGAR database for advanced compliance monitoring.</p>
          <p class="version">Version 3.0 - Consolidated GUI | ForensicOutputGenerator Integrated</p>
        </div>
      </footer>
    `;
  }
}

customElements.define('custom-footer', CustomFooter);

