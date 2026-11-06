/**
 * A MAC address as AA:BB:CC:DD:EE:FF, however its twelve hex digits were written
 * ("aa-bb-cc-dd-ee-ff", "aabb.ccdd.eeff", "AABBCCDDEEFF"). Anything else stays as typed;
 * the server refuses it. Mirrors `normalize_mac_address` in the backend.
 */
export function formatMacAddress(value: string): string {
  const text = value.trim()
  const digits = text.replace(/[\s:.-]/g, '').toUpperCase()
  if (!/^[0-9A-F]{12}$/.test(digits)) return text
  return digits.match(/../g)!.join(':')
}
