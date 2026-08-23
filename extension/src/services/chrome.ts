// This file contains Chrome extension related functions.

export async function getActiveTabUrl(): Promise<string | null> {
  const tabs = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  })

  return tabs[0]?.url ?? null
}
