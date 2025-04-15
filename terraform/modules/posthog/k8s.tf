resource "kubernetes_manifest" "posthog" {
  for_each   = fileset(path.module, "manifests/*.yaml")
  depends_on = [kubernetes_namespace_v1.posthog]
  manifest   = yamldecode(file("${path.module}/${each.value}"))
}
