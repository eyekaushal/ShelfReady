/** A product counts as scored once the readiness service has written issues or a score. */
export function isScored(product) {
  return product.readiness_score > 0 || (product.readiness_issues?.length ?? 0) > 0
}
