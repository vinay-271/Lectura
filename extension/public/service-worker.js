// Open the Lectura side panel when the extension icon is clicked.
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error("Failed to configure side panel:", error));
