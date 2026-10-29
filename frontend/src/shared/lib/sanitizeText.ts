/**
 * Strips any HTML tags from a string to ensure safe plain-text rendering.
 * This is a defense-in-depth measure — components should render text
 * via React's default escaping, never via dangerouslySetInnerHTML.
 */
export function sanitizeText(text: string): string {
  return text.replace(/<[^>]*>/g, "");
}
