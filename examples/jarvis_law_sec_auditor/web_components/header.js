/**
 * JARVIS:LAW Custom Header Web Component
 * For use in HTML reports and web-based interfaces
 */

class CustomHeader extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        header {
          background-color: #18181b; /* zinc-900 */
          border-bottom: 1px solid #3f3f46; /* zinc-700 */
          padding: 1rem 0;
        }
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 1rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
        }
        .logo {
          display: flex;
          align-items: center;
          color: #fde047; /* amber-300 */
          font-weight: bold;
          font-size: 1.5rem;
        }
        .logo i {
          margin-right: 0.5rem;
          color: #fbbf24; /* amber-400 */
        }
        .logo-icon {
          margin-right: 0.5rem;
          font-size: 1.8rem;
        }
        .subtitle {
          color: #a1a1aa; /* zinc-400 */
          font-size: 0.875rem;
          margin-left: 1rem;
          font-weight: normal;
        }
        .status-indicator {
          display: flex;
          align-items: center;
          font-weight: 600;
          color: #10b981; /* emerald-500 */
          font-size: 0.875rem;
        }
        .status-dot {
          height: 10px;
          width: 10px;
          border-radius: 50%;
          background-color: #10b981; /* emerald-500 */
          margin-right: 0.5rem;
          animation: pulse 2s infinite;
        }
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
        @media (max-width: 768px) {
          .subtitle {
            display: none;
          }
          .logo {
            font-size: 1.25rem;
          }
        }
      </style>
      <header>
        <div class="container">
          <div class="logo">
            <span class="logo-icon">⚖️</span>
            <span>JARVIS:LAW</span>
            <span class="subtitle">Forensic Analysis System v3.0</span>
          </div>
          <div class="status-indicator">
            <div class="status-dot"></div>
            <span>OPERATIONAL</span>
          </div>
        </div>
      </header>
    `;
    
    // Optional: Initialize Feather icons if available
    if (typeof feather !== 'undefined') {
      try {
        feather.replace();
      } catch (e) {
        console.log('Feather icons not available, using fallback');
      }
    }
  }
  
  /**
   * Update status indicator
   * @param {string} status - Status text (e.g., 'READY', 'ANALYZING', 'COMPLETE')
   * @param {string} color - CSS color for the indicator
   */
  setStatus(status, color = '#10b981') {
    const statusDot = this.shadowRoot.querySelector('.status-dot');
    const statusText = this.shadowRoot.querySelector('.status-indicator span');
    
    if (statusDot) {
      statusDot.style.backgroundColor = color;
    }
    
    if (statusText) {
      statusText.textContent = status;
      statusText.style.color = color;
    }
  }
}

customElements.define('custom-header', CustomHeader);

