/**
 * Toast Notifications & Background Job Popover Component.
 */

import { store } from "../state.js";

export class NotificationsComponent {
  constructor() {
    this.container = document.createElement("div");
    this.container.className = "toast-container";
    document.body.appendChild(this.container);

    this.bindEvents();
  }

  bindEvents() {
    store.subscribe("notifications", (state) => {
      this.renderToasts(state.notifications);
    });
  }

  renderToasts(notifications) {
    this.container.innerHTML = "";
    // Only display latest 3 active toasts
    notifications.slice(0, 3).forEach(n => {
      const toast = document.createElement("div");
      toast.className = `toast ${n.type}`;
      toast.innerHTML = `
        <div style="flex: 1;">${n.message}</div>
        <div style="font-size: 10px; color: var(--studio-text-muted);">${n.timestamp}</div>
      `;
      this.container.appendChild(toast);

      // Auto dismiss after 4 seconds
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 4000);
    });
  }
}
