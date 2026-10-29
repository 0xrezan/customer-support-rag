import { useState, useEffect } from "react";

/**
 * Returns `true` when the page/tab is visible, `false` when hidden.
 * Useful for pausing polling when the user switches tabs.
 */
export function usePageVisibility(): boolean {
  const [isVisible, setIsVisible] = useState(!document.hidden);

  useEffect(() => {
    const handleChange = () => setIsVisible(!document.hidden);
    document.addEventListener("visibilitychange", handleChange);
    return () => document.removeEventListener("visibilitychange", handleChange);
  }, []);

  return isVisible;
}
